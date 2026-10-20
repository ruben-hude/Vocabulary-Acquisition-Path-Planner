"""Graphical User Interface (Tkinter) for the Vocabulary Acquisition Path Planner.

Run with:
    PYTHONPATH=src python -m vocabulary_acquisition_path_planner.gui.gui
"""

from __future__ import annotations

import queue
import re
import threading
import tkinter as tk
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Vrais modules du backend
from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.models.word_group import (
    WordGroupRegistry,
)
from vocabulary_acquisition_path_planner.search.graph import Graph
from vocabulary_acquisition_path_planner.search.path_finder import PathFinder


@dataclass
class MediaEntry:
    """Represents a loaded media item along with its UI metadata."""

    name: str
    path: Path
    media: Media
    already_read: bool = False

    @property
    def cost(self) -> int:
        return sum(self.media.word_group_occurrences.values())

    @property
    def group_count(self) -> int:
        return len(self.media.word_group_occurrences)


def safe_percentage(vocabulary: LearnerVocabulary, media: Media) -> float:
    """Safe wrapper for know_percentage when media has no recognized words."""
    if not media.word_group_occurrences:
        return 0.0
    return vocabulary.know_percentage(media)


class PlannerApp(ttk.Frame):
    """Main window for the path planner application."""

    POLL_MS = 100

    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=8)
        self.master = master
        self.entries: list[MediaEntry] = []
        self.known_groups: set[str] = set()
        self.results_queue: queue.Queue = queue.Queue()
        self.search_thread: threading.Thread | None = None

        self.exposure_var = tk.IntVar(value=10)
        self.comprehension_var = tk.DoubleVar(value=80.0)
        self.time_limit_var = tk.IntVar(value=30)
        self.target_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Add text files to get started.")
        self.vocab_status_var = tk.StringVar()
        self.total_var = tk.StringVar()

        self._build_layout()
        self._refresh_vocab_status()
        self.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ UI
    def _build_layout(self):
        self.master.title("Vocabulary Acquisition Path Planner")
        self.master.minsize(900, 560)

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned, padding=4)
        right = ttk.Frame(paned, padding=4)
        paned.add(left, weight=3)
        paned.add(right, weight=2)

        self._build_media_panel(left)
        self._build_vocabulary_panel(left)
        self._build_parameters_panel(right)
        self._build_results_panel(right)

        ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            relief="sunken",
            padding=(6, 2),
        ).pack(fill="x", pady=(6, 0))

    def _build_media_panel(self, parent: ttk.Frame):
        box = ttk.LabelFrame(parent, text="Media Library", padding=6)
        box.pack(fill="both", expand=True)

        columns = ("cost", "groups", "comprehension", "read")
        self.media_tree = ttk.Treeview(
            box, columns=columns, height=12, selectmode="extended"
        )
        self.media_tree.heading("#0", text="Name")
        self.media_tree.heading("cost", text="Cost")
        self.media_tree.heading("groups", text="Groups")
        self.media_tree.heading("comprehension", text="Initial Coverage")
        self.media_tree.heading("read", text="Already Read")
        self.media_tree.column("#0", width=200)
        for col, width in (
            ("cost", 70),
            ("groups", 70),
            ("comprehension", 130),
            ("read", 90),
        ):
            self.media_tree.column(col, width=width, anchor="center")

        scroll = ttk.Scrollbar(
            box, orient="vertical", command=self.media_tree.yview
        )
        self.media_tree.configure(yscrollcommand=scroll.set)
        self.media_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        box.rowconfigure(0, weight=1)
        box.columnconfigure(0, weight=1)

        buttons = ttk.Frame(box)
        buttons.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(
            buttons, text="Add Texts...", command=self.add_media_files
        ).pack(side="left")
        ttk.Button(
            buttons, text="Remove", command=self.remove_selected
        ).pack(side="left", padx=4)
        ttk.Button(
            buttons, text="Toggle Read Status", command=self.toggle_read
        ).pack(side="left")

    def _build_vocabulary_panel(self, parent: ttk.Frame):
        box = ttk.LabelFrame(parent, text="Initial Vocabulary", padding=6)
        box.pack(fill="x", pady=(8, 0))
        ttk.Label(
            box,
            textvariable=self.vocab_status_var,
            wraplength=420,
            justify="left",
        ).pack(anchor="w")
        buttons = ttk.Frame(box)
        buttons.pack(anchor="w", pady=(6, 0))
        ttk.Button(
            buttons, text="Load Word List...", command=self.load_known_words
        ).pack(side="left")
        ttk.Button(
            buttons, text="Clear", command=self.clear_known_words
        ).pack(side="left", padx=4)

    def _build_parameters_panel(self, parent: ttk.Frame):
        box = ttk.LabelFrame(parent, text="Parameters", padding=6)
        box.pack(fill="x")
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="Exposure Threshold:").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Spinbox(
            box,
            from_=1,
            to=1000,
            width=8,
            textvariable=self.exposure_var,
            command=self._on_parameters_changed,
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(box, text="Min Comprehension:").grid(
            row=1, column=0, sticky="w", pady=4
        )
        scale_frame = ttk.Frame(box)
        scale_frame.grid(row=1, column=1, sticky="ew")
        self.comprehension_label = ttk.Label(scale_frame, width=6)
        ttk.Scale(
            scale_frame,
            from_=0,
            to=100,
            variable=self.comprehension_var,
            command=lambda _v: self._update_comprehension_label(),
        ).pack(side="left", fill="x", expand=True)
        self.comprehension_label.pack(side="left", padx=(4, 0))
        self._update_comprehension_label()

        ttk.Label(box, text="Time Limit (s, 0 = none):").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Spinbox(
            box, from_=0, to=3600, width=8, textvariable=self.time_limit_var
        ).grid(row=2, column=1, sticky="w")

        ttk.Label(box, text="Target Media:").grid(
            row=3, column=0, sticky="w", pady=4
        )
        self.target_combo = ttk.Combobox(
            box, textvariable=self.target_var, state="readonly"
        )
        self.target_combo.grid(row=3, column=1, sticky="ew")

        actions = ttk.Frame(box)
        actions.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.search_button = ttk.Button(
            actions, text="Find Path", command=self.start_search
        )
        self.search_button.pack(side="left")
        self.progress = ttk.Progressbar(actions, mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _build_results_panel(self, parent: ttk.Frame):
        box = ttk.LabelFrame(parent, text="Recommended Reading Path", padding=6)
        box.pack(fill="both", expand=True, pady=(8, 0))

        columns = ("media", "cost", "comprehension", "known")
        self.result_tree = ttk.Treeview(
            box, columns=columns, show="headings", height=10
        )
        for col, text, width in (
            ("media", "Media", 160),
            ("cost", "Cost", 60),
            ("comprehension", "Comprehension", 100),
            ("known", "Known Words After", 120),
        ):
            self.result_tree.heading(col, text=text)
            self.result_tree.column(
                col, width=width, anchor="w" if col == "media" else "center"
            )
        self.result_tree.pack(fill="both", expand=True)
        ttk.Label(
            box,
            textvariable=self.total_var,
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor="w", pady=(6, 0))

    # ------------------------------------------------------------ Helpers
    def _update_comprehension_label(self):
        self.comprehension_label.configure(
            text=f"{self.comprehension_var.get():.0f} %"
        )

    def _exposure_threshold(self) -> int:
        try:
            value = int(self.exposure_var.get())
        except (tk.TclError, ValueError):
            raise ValueError("Exposure threshold must be an integer.")
        if value < 1:
            raise ValueError("Exposure threshold must be at least 1.")
        return value

    def _unique_name(self, base: str) -> str:
        names = {entry.name for entry in self.entries}
        name, index = base, 2
        while name in names:
            name = f"{base} ({index})"
            index += 1
        return name

    def _entry_by_iid(self, iid: str) -> MediaEntry:
        return self.entries[int(iid)]

    def build_initial_vocabulary(self) -> LearnerVocabulary:
        """Constructs the initial learner vocabulary based on UI state."""
        threshold = self._exposure_threshold()
        vocabulary = LearnerVocabulary(exposure_threshold=threshold)
        if self.known_groups:
            vocabulary.account_for_media(
                Media({group: threshold for group in self.known_groups})
            )
        for entry in self.entries:
            if entry.already_read:
                vocabulary.account_for_media(entry.media)
        return vocabulary

    def _on_parameters_changed(self):
        self.refresh_media_tree()
        self._refresh_vocab_status()

    def refresh_media_tree(self):
        self.media_tree.delete(*self.media_tree.get_children())
        try:
            vocabulary = self.build_initial_vocabulary()
        except ValueError:
            vocabulary = None

        for index, entry in enumerate(self.entries):
            if vocabulary is not None:
                comprehension = (
                    f"{safe_percentage(vocabulary, entry.media):.0%}"
                )
            else:
                comprehension = "—"
            self.media_tree.insert(
                "",
                "end",
                iid=str(index),
                text=entry.name,
                values=(
                    entry.cost,
                    entry.group_count,
                    comprehension,
                    "Yes" if entry.already_read else "",
                ),
            )

        names = [entry.name for entry in self.entries]
        self.target_combo.configure(values=names)
        if self.target_var.get() not in names:
            self.target_var.set(names[-1] if names else "")

    def _refresh_vocab_status(self):
        read_count = sum(entry.already_read for entry in self.entries)
        self.vocab_status_var.set(
            f"{len(self.known_groups)} word group(s) known beforehand · "
            f"{read_count} media item(s) marked as read."
        )

    # ------------------------------------------------------------ Actions
    def add_media_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Text Files",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        errors = []
        for raw_path in paths:
            path = Path(raw_path)
            try:
                media = Media.from_text_file(path)
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            self.entries.append(
                MediaEntry(self._unique_name(path.stem), path, media)
            )

        self.refresh_media_tree()
        self.status_var.set(f"{len(self.entries)} media item(s) loaded.")
        if errors:
            messagebox.showwarning(
                "Could not load some files", "\n".join(errors)
            )

    def remove_selected(self):
        selected = {int(iid) for iid in self.media_tree.selection()}
        if not selected:
            return
        self.entries = [
            entry
            for index, entry in enumerate(self.entries)
            if index not in selected
        ]
        self.refresh_media_tree()
        self._refresh_vocab_status()

    def toggle_read(self):
        for iid in self.media_tree.selection():
            entry = self._entry_by_iid(iid)
            entry.already_read = not entry.already_read
        self.refresh_media_tree()
        self._refresh_vocab_status()

    def load_known_words(self):
        path = filedialog.askopenfilename(
            title="Select Known Word List",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror("Error", str(exc))
            return

        registry = WordGroupRegistry()
        unknown_count = 0
        for word in re.findall(r"[^\W\d_]+(?:['-][^\W\d_]+)*", text):
            group = registry.lookup(word)
            if group is None:
                unknown_count += 1
            else:
                self.known_groups.add(group)

        self.refresh_media_tree()
        self._refresh_vocab_status()
        self.status_var.set(
            f"List loaded · {unknown_count} word(s) not in registry."
        )

    def clear_known_words(self):
        self.known_groups.clear()
        self.refresh_media_tree()
        self._refresh_vocab_status()

    # ------------------------------------------------------------- Search
    def start_search(self):
        if self.search_thread is not None and self.search_thread.is_alive():
            return
        if not self.entries:
            messagebox.showinfo("No Media", "Please add at least one text file.")
            return

        target = next(
            (
                entry
                for entry in self.entries
                if entry.name == self.target_var.get()
            ),
            None,
        )
        if target is None:
            messagebox.showinfo("No Target", "Please select a target media.")
            return

        try:
            initial_vocabulary = self.build_initial_vocabulary()
            time_limit = int(self.time_limit_var.get())
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("Invalid Parameters", str(exc))
            return

        graph = Graph(
            [entry.media for entry in self.entries],
            initial_vocabulary=initial_vocabulary,
            comprehension_threshold=self.comprehension_var.get() / 100,
        )
        names = {id(entry.media): entry.name for entry in self.entries}

        self.result_tree.delete(*self.result_tree.get_children())
        self.total_var.set("")
        self.search_button.configure(state="disabled")
        self.progress.start(12)
        self.status_var.set(f"Searching path to «{target.name}»…")

        self.search_thread = threading.Thread(
            target=self._search_worker,
            args=(
                graph,
                target.media,
                time_limit or None,
                initial_vocabulary,
                names,
            ),
            daemon=True,
        )
        self.search_thread.start()
        self.after(self.POLL_MS, self._poll_search)

    def _search_worker(
        self, graph: Graph, target: Media, time_limit: int | None, vocabulary: LearnerVocabulary, names: dict
    ):
        try:
            result = PathFinder(graph).find_path(
                target, time_limit_seconds=time_limit
            )
            self.results_queue.put(("ok", (result, vocabulary, names)))
        except Exception as exc:
            self.results_queue.put(("error", exc))

    def _poll_search(self):
        try:
            kind, payload = self.results_queue.get_nowait()
        except queue.Empty:
            self.after(self.POLL_MS, self._poll_search)
            return

        self.progress.stop()
        self.search_button.configure(state="normal")
        if kind == "ok":
            self._show_result(*payload)
        else:
            self._show_error(payload)

    def _show_result(self, result, initial_vocabulary: LearnerVocabulary, names: dict):
        vocabulary = deepcopy(initial_vocabulary)
        for step, media in enumerate(result.media, start=1):
            comprehension = safe_percentage(vocabulary, media)
            vocabulary.account_for_media(media)
            self.result_tree.insert(
                "",
                "end",
                values=(
                    f"{step}. {names.get(id(media), '?')}",
                    sum(media.word_group_occurrences.values()),
                    f"{comprehension:.0%}",
                    len(vocabulary.known_words),
                ),
            )
        self.total_var.set(
            f"Total Cost: {result.cost} · {len(result.media)} media item(s)"
        )
        self.status_var.set("Path successfully found.")

    def _show_error(self, exc: Exception):
        if isinstance(exc, TimeoutError):
            message = (
                "Search timed out. Try increasing the time limit or "
                "reducing the number of media items."
            )
        elif isinstance(exc, LookupError):
            message = (
                "No path exists to the target with the given minimum "
                "comprehension threshold. Try lowering it or adding "
                "intermediate texts."
            )
        else:
            message = f"{type(exc).__name__}: {exc}"
        self.status_var.set("Search failed to find a path.")
        messagebox.showerror("Search Failed", message)


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    PlannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()