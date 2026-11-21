"""Télécharge 1000 livres anglophones depuis Hugging Face en respectant la limite de requêtes."""

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "gutenberg_books"
METADATA_FILE = PROJECT_ROOT / "data" / "books_metadata.json"
TARGET_COUNT = 1000

HF_ROWS_API = "https://datasets-server.huggingface.co/rows?dataset=manu%2Fproject_gutenberg&config=default&split=en"


def parse_header_metadata(raw_text: str) -> dict:
    """Extrait le titre, l'auteur et la date depuis l'en-tête Gutenberg."""
    header = raw_text[:4000]

    title_match = re.search(
        r"^Title:\s*(.+?)(?=\n[A-Z][a-zA-Z ]+:|\r?\n\r?\n)",
        header,
        re.MULTILINE | re.DOTALL,
    )
    author_match = re.search(
        r"^Author:\s*(.+?)(?=\n[A-Z][a-zA-Z ]+:|\r?\n\r?\n)",
        header,
        re.MULTILINE | re.DOTALL,
    )
    date_match = re.search(r"^Release [Dd]ate:\s*([^\[\r\n]+)", header, re.MULTILINE)

    title = " ".join(title_match.group(1).split()) if title_match else "Sans titre"
    author = " ".join(author_match.group(1).split()) if author_match else "Inconnu"
    release_date = date_match.group(1).strip() if date_match else "Inconnue"

    return {
        "title": title,
        "author": author,
        "release_date": release_date,
    }


def clean_gutenberg_text(raw_text: str) -> str:
    """Retire les en-têtes et pieds de page légaux de Gutenberg."""
    start_match = re.search(
        r"\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*? \*\*\*",
        raw_text,
        re.IGNORECASE,
    )
    text = raw_text[start_match.end() :] if start_match else raw_text

    end_match = re.search(
        r"\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*? \*\*\*",
        text,
        re.IGNORECASE,
    )
    text = text[: end_match.start()] if end_match else text
    return text.strip()


def fetch_batch(offset: int, length: int) -> list:
    """Récupère un paquet de livres et attend automatiquement en cas d'erreur 429."""
    url = f"{HF_ROWS_API}&offset={offset}&length={length}"
    while True:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("rows", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("Limite de requêtes atteinte (429) — pause de 30s avant reprise...", flush=True)
                time.sleep(30)
            else:
                print(f"Erreur HTTP {e.code} à l'offset {offset} — pause de 10s...", flush=True)
                time.sleep(10)
        except Exception as e:
            print(f"Micro-coupure réseau ({e}) — pause de 10s...", flush=True)
            time.sleep(10)


def build_library(target_count: int = TARGET_COUNT):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    metadata_db = {}
    if METADATA_FILE.exists():
        metadata_db = json.loads(METADATA_FILE.read_text(encoding="utf-8"))

    # Remove stale metadata entries whose text files are no longer present locally.
    valid_metadata = {}
    for book_id, info in metadata_db.items():
        file_path = Path(info.get("file_path", ""))
        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path
        if file_path.exists():
            info["file_path"] = file_path.relative_to(PROJECT_ROOT).as_posix()
            valid_metadata[book_id] = info

    metadata_db = valid_metadata
    METADATA_FILE.write_text(
        json.dumps(metadata_db, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    count = len(metadata_db)
    offset = 0
    batch_size = 10  # Paquets de 10 livres pour aller 2x plus vite

    print(f"Reprise du téléchargement ({count}/{target_count} déjà présents)...", flush=True)

    while count < target_count:
        rows = fetch_batch(offset, batch_size)
        if not rows:
            offset += batch_size
            continue

        for item in rows:
            if count >= target_count:
                break

            row = item.get("row", {})
            raw_text = row.get("text", "")
            if not raw_text or len(raw_text) < 5000:
                continue

            raw_id = str(row.get("id", item.get("row_idx", offset)))
            digits = re.sub(r"\D", "", raw_id)
            book_id = digits if digits else str(offset + count)

            if book_id in metadata_db:
                continue

            info = parse_header_metadata(raw_text)
            clean_text = clean_gutenberg_text(raw_text)

            if len(clean_text) < 5000:
                continue

            file_path = OUTPUT_DIR / f"book_{book_id}.txt"
            file_path.write_text(clean_text, encoding="utf-8")

            metadata_db[book_id] = {
                "id": int(book_id),
                "file_path": file_path.relative_to(PROJECT_ROOT).as_posix(),
                "title": info["title"],
                "author": info["author"],
                "release_date": info["release_date"],
                "word_count": len(clean_text.split()),
            }
            count += 1

        offset += batch_size
        print(f"Progression : {count}/{target_count} livres prêts...", flush=True)

        METADATA_FILE.write_text(
            json.dumps(metadata_db, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # Petite pause de politesse pour éviter de déclencher l'erreur 429
        time.sleep(1.5)

    print(f"\nTerminé ! {len(metadata_db)} livres indexés dans {METADATA_FILE}.", flush=True)


if __name__ == "__main__":
    build_library(target_count=1000)