"""CustomTkinter graphical interface for the Vocabulary Acquisition Path Planner.

The interface is available in Spanish, English and French; the ES / EN / FR
segmented buttons switch the language at any time.

Run with:
    python -m vocabulary_acquisition_path_planner.gui
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

import customtkinter as ctk

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.models.word_group import (
    WordGroupRegistry,
)
from vocabulary_acquisition_path_planner.search.graph import Graph
from vocabulary_acquisition_path_planner.search.path_finder import PathFinder


# Set CustomTkinter global appearance and theme
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"


# ---------------------------------------------------------------- languages
TRANSLATIONS = {
    "es": {
        "window_title": "Planificador de adquisición de vocabulario",
        "language": "Idioma:",
        "status_start": "Añade textos para empezar.",
        "media_panel": "Medios",
        "col_name": "Nombre",
        "col_cost": "Coste",
        "col_groups": "Grupos",
        "col_initial": "Comprensión inicial",
        "col_read": "Ya leído",
        "add_texts": "Añadir textos…",
        "remove": "Quitar",
        "toggle_read": "Marcar/desmarcar como leído",
        "vocab_panel": "Vocabulario inicial",
        "load_words": "Cargar lista de palabras…",
        "clear": "Limpiar",
        "params_panel": "Parámetros",
        "exposure": "Umbral de exposición:",
        "min_comprehension": "Comprensión mínima:",
        "time_limit": "Límite de tiempo (s, 0 = sin límite):",
        "target": "Medio objetivo:",
        "find_path": "Buscar camino",
        "results_panel": "Camino recomendado",
        "col_media": "Medio",
        "col_comprehension": "Comprensión",
        "col_known_after": "Conocidas después",
        "yes": "Sí",
        "vocab_status": (
            "{groups} grupos de palabras conocidos de antemano · "
            "{read} medio(s) marcados como ya leídos."
        ),
        "err_threshold_int": "El umbral de exposición debe ser un entero.",
        "err_threshold_min": "El umbral de exposición debe ser al menos 1.",
        "err_time_limit": "El límite de tiempo debe ser un entero.",
        "dialog_select_texts": "Selecciona textos",
        "filetype_text": "Texto",
        "filetype_all": "Todos los archivos",
        "media_loaded": "{count} medio(s) cargados.",
        "load_errors_title": "No se pudieron cargar algunos archivos",
        "error_title": "Error",
        "dialog_word_list": "Lista de palabras conocidas",
        "word_list_loaded": (
            "Lista cargada · {unknown} palabra(s) no están en el registro."
        ),
        "no_media_title": "Sin medios",
        "no_media_msg": "Añade al menos un texto.",
        "no_target_title": "Sin objetivo",
        "no_target_msg": "Elige un medio objetivo.",
        "invalid_params": "Parámetros no válidos",
        "searching": "Buscando camino hacia «{name}»…",
        "total_cost": "Coste total: {cost} · {count} medio(s)",
        "path_found": "Camino encontrado.",
        "search_failed_title": "Búsqueda fallida",
        "search_failed_status": "La búsqueda no encontró un camino.",
        "timeout_msg": (
            "Se agotó el tiempo de búsqueda. Prueba con un límite mayor o con"
            " menos medios."
        ),
        "no_path_msg": (
            "No existe un camino hasta el objetivo con esta comprensión"
            " mínima. Prueba a bajarla o a añadir textos intermedios."
        ),
    },
    "en": {
        "window_title": "Vocabulary Acquisition Path Planner",
        "language": "Language:",
        "status_start": "Add texts to get started.",
        "media_panel": "Media",
        "col_name": "Name",
        "col_cost": "Cost",
        "col_groups": "Groups",
        "col_initial": "Initial comprehension",
        "col_read": "Already read",
        "add_texts": "Add texts…",
        "remove": "Remove",
        "toggle_read": "Mark/unmark as read",
        "vocab_panel": "Starting vocabulary",
        "load_words": "Load word list…",
        "clear": "Clear",
        "params_panel": "Parameters",
        "exposure": "Exposure threshold:",
        "min_comprehension": "Minimum comprehension:",
        "time_limit": "Time limit (s, 0 = none):",
        "target": "Target media:",
        "find_path": "Find path",
        "results_panel": "Recommended path",
        "col_media": "Media",
        "col_comprehension": "Comprehension",
        "col_known_after": "Known after",
        "yes": "Yes",
        "vocab_status": (
            "{groups} known word groups · {read} media marked as already read."
        ),
        "err_threshold_int": "The exposure threshold must be an integer.",
        "err_threshold_min": "The exposure threshold must be at least 1.",
        "err_time_limit": "The time limit must be an integer.",
        "dialog_select_texts": "Select texts",
        "filetype_text": "Text",
        "filetype_all": "All files",
        "media_loaded": "{count} media loaded.",
        "load_errors_title": "Some files could not be loaded",
        "error_title": "Error",
        "dialog_word_list": "Known word list",
        "word_list_loaded": (
            "Word list loaded · {unknown} word(s) not in the registry."
        ),
        "no_media_title": "No media",
        "no_media_msg": "Add at least one text.",
        "no_target_title": "No target",
        "no_target_msg": "Choose a target media.",
        "invalid_params": "Invalid parameters",
        "searching": "Searching for a path to “{name}”…",
        "total_cost": "Total cost: {cost} · {count} media",
        "path_found": "Path found.",
        "search_failed_title": "Search failed",
        "search_failed_status": "The search did not find a path.",
        "timeout_msg": (
            "The search ran out of time. Try a higher limit or fewer media."
        ),
        "no_path_msg": (
            "No path to the target exists with this minimum comprehension. Try"
            " lowering it or adding intermediate texts."
        ),
    },
    "fr": {
        "window_title": "Planificateur d'acquisition de vocabulaire",
        "language": "Langue :",
        "status_start": "Ajoutez des textes pour commencer.",
        "media_panel": "Médias",
        "col_name": "Nom",
        "col_cost": "Coût",
        "col_groups": "Groupes",
        "col_initial": "Compréhension initiale",
        "col_read": "Déjà lu",
        "add_texts": "Ajouter des textes…",
        "remove": "Retirer",
        "toggle_read": "Marquer/démarquer comme lu",
        "vocab_panel": "Vocabulaire initial",
        "load_words": "Charger une liste de mots…",
        "clear": "Effacer",
        "params_panel": "Paramètres",
        "exposure": "Seuil d'exposition :",
        "min_comprehension": "Compréhension minimale :",
        "time_limit": "Limite de temps (s, 0 = aucune) :",
        "target": "Média cible :",
        "find_path": "Chercher le chemin",
        "results_panel": "Chemin recommandé",
        "col_media": "Média",
        "col_comprehension": "Compréhension",
        "col_known_after": "Connus après",
        "yes": "Oui",
        "vocab_status": (
            "{groups} groupes de mots déjà connus · {read} média(s) marqué(s)"
            " comme lu(s)."
        ),
        "err_threshold_int": "Le seuil d'exposition doit être un entier.",
        "err_threshold_min": "Le seuil d'exposition doit être au moins 1.",
        "err_time_limit": "La limite de temps doit être un entier.",
        "dialog_select_texts": "Sélectionnez des textes",
        "filetype_text": "Texte",
        "filetype_all": "Tous les fichiers",
        "media_loaded": "{count} média(s) chargé(s).",
        "load_errors_title": "Certains fichiers n'ont pas pu être chargés",
        "error_title": "Erreur",
        "dialog_word_list": "Liste de mots connus",
        "word_list_loaded": (
            "Liste chargée · {unknown} mot(s) absent(s) du registre."
        ),
        "no_media_title": "Aucun média",
        "no_media_msg": "Ajoutez au moins un texte.",
        "no_target_title": "Aucune cible",
        "no_target_msg": "Choisissez un média cible.",
        "invalid_params": "Paramètres invalides",
        "searching": "Recherche d'un chemin vers « {name} »…",
        "total_cost": "Coût total : {cost} · {count} média(s)",
        "path_found": "Chemin trouvé.",
        "search_failed_title": "Échec de la recherche",
        "search_failed_status": "La recherche n'a pas trouvé de chemin.",
        "timeout_msg": (
            "La recherche a dépassé le temps imparti. Essayez une limite plus"
            " élevée ou moins de médias."
        ),
        "no_path_msg": (
            "Aucun chemin n'atteint la cible avec cette compréhension"
            " minimale. Essayez de la baisser ou d'ajouter des textes"
            " intermédiaires."
        ),
    },
}

LANGUAGE_ORDER = ("es", "en", "fr")
DEFAULT_LANGUAGE = "es"


@dataclass
class MediaEntry:
    """A media item loaded in the interface, plus its UI metadata."""

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


def safe_percentage(
    vocabulary: LearnerVocabulary, media: Media
) -> float:
    if not media.word_group_occurrences:
        return 0.0
    return vocabulary.know_percentage(media)


class PlannerApp(ctk.CTkFrame):
    """Main window of the path planner built with CustomTkinter."""

    POLL_MS = 100

    def __init__(self, master: ctk.CTk, language: str = DEFAULT_LANGUAGE):
        super().__init__(master)
        self.master = master
        self.language = language

        # Application state
        self.entries: list[MediaEntry] = []
        self.known_groups: set[str] = set()
        self.results_queue: queue.Queue = queue.Queue()
        self.search_thread: threading.Thread | None = None
        self.searching = False
        self.path_rows: list[tuple] = []
        self.path_total: tuple[int, int] | None = None
        self.status_message = ("status_start", {})

        # Tkinter variables
        self.exposure_var = tk.IntVar(value=10)
        self.comprehension_var = tk.DoubleVar(value=80.0)
        self.time_limit_var = tk.IntVar(value=30)
        self.target_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.vocab_status_var = tk.StringVar()
        self.total_var = tk.StringVar()

        self.pack(fill="both", expand=True, padx=10, pady=10)
        self._configure_treeview_styles()
        self._build_layout()

    # ------------------------------------------------------------ Language
    def t(self, key: str, **kwargs) -> str:
        text = TRANSLATIONS[self.language][key]
        return text.format(**kwargs) if kwargs else text

    def set_language(self, language_code: str):
        code = language_code.lower()
        if code == self.language or self.searching:
            return
        self.language = code
        for child in self.winfo_children():
            child.destroy()
        self._build_layout()

    def set_status(self, key: str, **kwargs):
        self.status_message = (key, kwargs)
        self.status_var.set(self.t(key, **kwargs))

    # ------------------------------------------------------------------ Styles
    def _configure_treeview_styles(self):
        """Style ttk.Treeview to seamlessly fit with dark/light CustomTkinter themes."""
        style = ttk.Style()
        style.theme_use("clam")

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        bg_color = "#2b2b2b" if is_dark else "#f0f0f0"
        fg_color = "#ffffff" if is_dark else "#000000"
        field_bg = "#212121" if is_dark else "#ffffff"
        header_bg = "#383838" if is_dark else "#e0e0e0"

        style.configure(
            "Treeview",
            background=field_bg,
            foreground=fg_color,
            fieldbackground=field_bg,
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=header_bg,
            foreground=fg_color,
            relief="flat",
            font=("Arial", 10, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#1f538d")],
            foreground=[("selected", "#ffffff")],
        )

    # ------------------------------------------------------------------ UI
    def _build_layout(self):
        self.master.title(self.t("window_title"))
        self.master.geometry("960x640")
        self.master.minsize(900, 580)

        self._build_top_bar()

        # Main 2-column container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, pady=(0, 6))
        main_container.columnconfigure(0, weight=3)
        main_container.columnconfigure(1, weight=2)
        main_container.rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        right_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self._build_media_panel(left_frame)
        self._build_vocabulary_panel(left_frame)
        self._build_parameters_panel(right_frame)
        self._build_results_panel(right_frame)

        # Bottom Status Bar
        status_bar = ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            anchor="w",
            height=28,
            corner_radius=6,
            fg_color=("gray85", "gray20"),
            padx=10,
        )
        status_bar.pack(fill="x", side="bottom")

        # Refresh interface state
        self.refresh_media_tree()
        self._refresh_vocab_status()
        self._render_results()
        key, kwargs = self.status_message
        self.set_status(key, **kwargs)

    def _build_top_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 10))

        title = ctk.CTkLabel(
            bar,
            text=self.t("window_title"),
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(side="left")

        # Segmented button for language switching
        self.lang_segmented = ctk.CTkSegmentedButton(
            bar,
            values=[code.upper() for code in LANGUAGE_ORDER],
            command=self.set_language,
            width=120,
        )
        self.lang_segmented.set(self.language.upper())
        self.lang_segmented.pack(side="right")

        lang_label = ctk.CTkLabel(
            bar, text=self.t("language"), font=ctk.CTkFont(size=13)
        )
        lang_label.pack(side="right", padx=(0, 8))

    def _build_media_panel(self, parent: ctk.CTkFrame):
        box = ctk.CTkFrame(parent)
        box.pack(fill="both", expand=True, pady=(0, 8))

        label = ctk.CTkLabel(
            box,
            text=self.t("media_panel"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        label.pack(anchor="w", padx=10, pady=(8, 4))

        tree_frame = ctk.CTkFrame(box, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)

        columns = ("cost", "groups", "comprehension", "read")
        self.media_tree = ttk.Treeview(
            tree_frame, columns=columns, height=8, selectmode="extended"
        )
        self.media_tree.heading("#0", text=self.t("col_name"))
        self.media_tree.heading("cost", text=self.t("col_cost"))
        self.media_tree.heading("groups", text=self.t("col_groups"))
        self.media_tree.heading("comprehension", text=self.t("col_initial"))
        self.media_tree.heading("read", text=self.t("col_read"))
        self.media_tree.column("#0", width=180)

        for col, width in (
            ("cost", 60),
            ("groups", 60),
            ("comprehension", 130),
            ("read", 80),
        ):
            self.media_tree.column(col, width=width, anchor="center")

        scroll = ctk.CTkScrollbar(
            tree_frame, orientation="vertical", command=self.media_tree.yview
        )
        self.media_tree.configure(yscrollcommand=scroll.set)
        self.media_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        btn_frame = ctk.CTkFrame(box, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(4, 10))

        ctk.CTkButton(
            btn_frame,
            text=self.t("add_texts"),
            command=self.add_media_files,
            width=110,
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            btn_frame,
            text=self.t("remove"),
            command=self.remove_selected,
            fg_color="transparent",
            border_width=1,
            width=80,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_frame,
            text=self.t("toggle_read"),
            command=self.toggle_read,
            fg_color="transparent",
            border_width=1,
        ).pack(side="left", padx=4)

    def _build_vocabulary_panel(self, parent: ctk.CTkFrame):
        box = ctk.CTkFrame(parent)
        box.pack(fill="x")

        label = ctk.CTkLabel(
            box,
            text=self.t("vocab_panel"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        label.pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            box,
            textvariable=self.vocab_status_var,
            wraplength=400,
            justify="left",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=10, pady=2)

        btn_frame = ctk.CTkFrame(box, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=10, pady=(4, 10))

        ctk.CTkButton(
            btn_frame,
            text=self.t("load_words"),
            command=self.load_known_words,
            width=130,
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            btn_frame,
            text=self.t("clear"),
            command=self.clear_known_words,
            fg_color="transparent",
            border_width=1,
            width=70,
        ).pack(side="left", padx=4)

    def _build_parameters_panel(self, parent: ctk.CTkFrame):
        box = ctk.CTkFrame(parent)
        box.pack(fill="x", pady=(0, 8))

        label = ctk.CTkLabel(
            box,
            text=self.t("params_panel"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        label.pack(anchor="w", padx=10, pady=(8, 6))

        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=2)
        grid.columnconfigure(1, weight=1)

        # Exposure
        ctk.CTkLabel(
            grid, text=self.t("exposure"), font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="w", pady=4)
        ctk.CTkEntry(
            grid,
            width=70,
            textvariable=self.exposure_var,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)

        # Min Comprehension
        ctk.CTkLabel(
            grid, text=self.t("min_comprehension"), font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="w", pady=4)

        scale_frame = ctk.CTkFrame(grid, fg_color="transparent")
        scale_frame.grid(
            row=1, column=1, sticky="ew", padx=(10, 0), pady=4
        )

        ctk.CTkSlider(
            scale_frame,
            from_=0,
            to=100,
            variable=self.comprehension_var,
            command=lambda _v: self._update_comprehension_label(),
        ).pack(side="left", fill="x", expand=True)

        self.comprehension_label = ctk.CTkLabel(
            scale_frame, width=45, font=ctk.CTkFont(size=12)
        )
        self.comprehension_label.pack(side="left", padx=(6, 0))
        self._update_comprehension_label()

        # Time Limit
        ctk.CTkLabel(
            grid, text=self.t("time_limit"), font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, sticky="w", pady=4)
        ctk.CTkEntry(
            grid,
            width=70,
            textvariable=self.time_limit_var,
        ).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)

        # Target Media OptionMenu
        ctk.CTkLabel(
            grid, text=self.t("target"), font=ctk.CTkFont(size=12)
        ).grid(row=3, column=0, sticky="w", pady=4)
        self.target_optionmenu = ctk.CTkOptionMenu(
            grid, variable=self.target_var, values=[""]
        )
        self.target_optionmenu.grid(
            row=3, column=1, sticky="ew", padx=(10, 0), pady=4
        )

        # Actions
        actions = ctk.CTkFrame(box, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=(8, 10))

        self.search_button = ctk.CTkButton(
            actions, text=self.t("find_path"), command=self.start_search
        )
        self.search_button.pack(side="left")

        self.progress = ctk.CTkProgressBar(actions, mode="indeterminate")
        self.progress.pack(
            side="left", fill="x", expand=True, padx=(10, 0)
        )
        self.progress.set(0)

    def _build_results_panel(self, parent: ctk.CTkFrame):
        box = ctk.CTkFrame(parent)
        box.pack(fill="both", expand=True)

        label = ctk.CTkLabel(
            box,
            text=self.t("results_panel"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        label.pack(anchor="w", padx=10, pady=(8, 4))

        tree_frame = ctk.CTkFrame(box, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)

        columns = ("media", "cost", "comprehension", "known")
        self.result_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=6
        )
        for col, key, width in (
            ("media", "col_media", 140),
            ("cost", "col_cost", 50),
            ("comprehension", "col_comprehension", 100),
            ("known", "col_known_after", 100),
        ):
            self.result_tree.heading(col, text=self.t(key))
            self.result_tree.column(
                col, width=width, anchor="w" if col == "media" else "center"
            )

        scroll = ctk.CTkScrollbar(
            tree_frame, orientation="vertical", command=self.result_tree.yview
        )
        self.result_tree.configure(yscrollcommand=scroll.set)
        self.result_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        ctk.CTkLabel(
            box,
            textvariable=self.total_var,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(4, 8))

    # ------------------------------------------------------------ Helpers
    def _update_comprehension_label(self):
        self.comprehension_label.configure(
            text=f"{self.comprehension_var.get():.0f} %"
        )

    def _exposure_threshold(self) -> int:
        try:
            value = int(self.exposure_var.get())
        except (tk.TclError, ValueError):
            raise ValueError(self.t("err_threshold_int"))
        if value < 1:
            raise ValueError(self.t("err_threshold_min"))
        return value

    def _time_limit(self) -> int | None:
        try:
            value = int(self.time_limit_var.get())
        except (tk.TclError, ValueError):
            raise ValueError(self.t("err_time_limit"))
        return value if value > 0 else None

    def _unique_name(self, base: str) -> str:
        names = {entry.name for entry in self.entries}
        name, index = base, 2
        while name in names:
            name = f"{base} ({index})"
            index += 1
        return name

    def _entry_by_iid(self, iid: str) -> MediaEntry:
        return self.entries[int(iid)]

    def _file_types(self):
        return [
            (self.t("filetype_text"), "*.txt"),
            (self.t("filetype_all"), "*.*"),
        ]

    def build_initial_vocabulary(self) -> LearnerVocabulary:
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

    def refresh_media_tree(self):
        self.media_tree.delete(*self.media_tree.get_children())
        try:
            vocabulary = self.build_initial_vocabulary()
        except ValueError:
            vocabulary = None

        for index, entry in enumerate(self.entries):
            comprehension = (
                f"{safe_percentage(vocabulary, entry.media):.0%}"
                if vocabulary is not None
                else "—"
            )
            self.media_tree.insert(
                "",
                "end",
                iid=str(index),
                text=entry.name,
                values=(
                    entry.cost,
                    entry.group_count,
                    comprehension,
                    self.t("yes") if entry.already_read else "",
                ),
            )

        names = [entry.name for entry in self.entries]
        self.target_optionmenu.configure(values=names if names else [""])
        if self.target_var.get() not in names:
            self.target_var.set(names[-1] if names else "")

    def _refresh_vocab_status(self):
        read = sum(entry.already_read for entry in self.entries)
        self.vocab_status_var.set(
            self.t("vocab_status", groups=len(self.known_groups), read=read)
        )

    def _render_results(self):
        self.result_tree.delete(*self.result_tree.get_children())
        for step, name, cost, comprehension, known in self.path_rows:
            self.result_tree.insert(
                "",
                "end",
                values=(
                    f"{step}. {name}",
                    cost,
                    f"{comprehension:.0%}",
                    known,
                ),
            )
        if self.path_total is None:
            self.total_var.set("")
        else:
            cost, count = self.path_total
            self.total_var.set(self.t("total_cost", cost=cost, count=count))

    # ------------------------------------------------------------ Actions
    def add_media_files(self):
        paths = filedialog.askopenfilenames(
            title=self.t("dialog_select_texts"), filetypes=self._file_types()
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
        self.set_status("media_loaded", count=len(self.entries))
        if errors:
            messagebox.showwarning(
                self.t("load_errors_title"), "\n".join(errors)
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
            title=self.t("dialog_word_list"), filetypes=self._file_types()
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror(self.t("error_title"), str(exc))
            return

        registry = WordGroupRegistry()
        unknown = 0
        for word in re.findall(r"[^\W\d_]+(?:['-][^\W\d_]+)*", text):
            group = registry.lookup(word)
            if group is None:
                unknown += 1
            else:
                self.known_groups.add(group)

        self.refresh_media_tree()
        self._refresh_vocab_status()
        self.set_status("word_list_loaded", unknown=unknown)

    def clear_known_words(self):
        self.known_groups.clear()
        self.refresh_media_tree()
        self._refresh_vocab_status()

    # ------------------------------------------------------------- Search
    def start_search(self):
        if self.searching:
            return
        if not self.entries:
            messagebox.showinfo(
                self.t("no_media_title"), self.t("no_media_msg")
            )
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
            messagebox.showinfo(
                self.t("no_target_title"), self.t("no_target_msg")
            )
            return

        try:
            initial_vocabulary = self.build_initial_vocabulary()
            time_limit = self._time_limit()
        except ValueError as exc:
            messagebox.showerror(self.t("invalid_params"), str(exc))
            return

        graph = Graph(
            [entry.media for entry in self.entries],
            initial_vocabulary=initial_vocabulary,
            comprehension_threshold=self.comprehension_var.get() / 100,
        )
        names = {id(entry.media): entry.name for entry in self.entries}

        self.path_rows, self.path_total = [], None
        self._render_results()
        self.searching = True
        self.lang_segmented.configure(state="disabled")
        self.search_button.configure(state="disabled")
        self.progress.start()
        self.set_status("searching", name=target.name)

        self.search_thread = threading.Thread(
            target=self._search_worker,
            args=(graph, target.media, time_limit, initial_vocabulary, names),
            daemon=True,
        )
        self.search_thread.start()
        self.after(self.POLL_MS, self._poll_search)

    def _search_worker(
        self,
        graph: Graph,
        target: Media,
        time_limit: int | None,
        vocabulary: LearnerVocabulary,
        names: dict,
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

        self.searching = False
        self.progress.stop()
        self.progress.set(0)
        self.search_button.configure(state="normal")
        self.lang_segmented.configure(state="normal")

        if kind == "ok":
            self._show_result(*payload)
        else:
            self._show_error(payload)

    def _show_result(
        self, result, initial_vocabulary: LearnerVocabulary, names: dict
    ):
        vocabulary = deepcopy(initial_vocabulary)
        rows = []
        for step, media in enumerate(result.media, start=1):
            comprehension = safe_percentage(vocabulary, media)
            vocabulary.account_for_media(media)
            rows.append(
                (
                    step,
                    names.get(id(media), "?"),
                    sum(media.word_group_occurrences.values()),
                    comprehension,
                    len(vocabulary.known_words),
                )
            )
        self.path_rows = rows
        self.path_total = (result.cost, len(result.media))
        self._render_results()
        self.set_status("path_found")

    def _show_error(self, exc: Exception):
        if isinstance(exc, TimeoutError):
            message = self.t("timeout_msg")
        elif isinstance(exc, LookupError):
            message = self.t("no_path_msg")
        else:
            message = f"{type(exc).__name__}: {exc}"
        self.set_status("search_failed_status")
        messagebox.showerror(self.t("search_failed_title"), message)


def main():
    root = ctk.CTk()
    PlannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()