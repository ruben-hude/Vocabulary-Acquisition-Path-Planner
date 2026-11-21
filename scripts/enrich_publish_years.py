"""Passe finale sur les derniers null : inspecte le début du fichier .txt local puis Wikidata."""

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

METADATA_FILE = Path("data/books_metadata.json")


def extract_year_from_local_text(file_path_str: str) -> int | None:
    """Cherche une année de copyright ou de première édition dans les 4 000 premiers caractères du livre."""
    path = Path(file_path_str)
    if not path.exists():
        return None

    head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
    patterns = [
        r"(?:copyright|published|printed|edition|written|composed|london|new york|boston|paris)\D{0,25}\b(1[5-9]\d{2}|20[0-2]\d)\b",
        r"\b(1[6-9]\d{2})\b",
    ]
    for pat in patterns:
        matches = [int(y) for y in re.findall(pat, head, flags=re.IGNORECASE)]
        valid = [y for y in matches if 1500 <= y <= 2025]
        if valid:
            return min(valid)
    return None


def fetch_wikidata_year(title: str) -> int | None:
    """Interroge l'API de recherche Wikidata sur le titre nettoyé."""
    clean_title = re.split(r"[:;(]|,\s*(?:Vol|Volume|Part|Book)", title, flags=re.I)[0].strip()
    if len(clean_title) < 4:
        return None

    url = (
        "https://www.wikidata.org/w/api.php?"
        f"action=wbsearchentities&search={urllib.parse.quote(clean_title[:80])}"
        "&language=en&format=json&limit=3"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for item in data.get("search", []):
            desc = item.get("description", "")
            m = re.search(r"\b(1[0-9]\d{2}|20[0-2]\d)\b", desc)
            if m:
                return int(m.group(1))
    except Exception:
        return None
    return None


def main():
    db = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    missing = [k for k, v in db.items() if v.get("first_publish_year") is None]
    print(f"Analyse finale sur {len(missing)} livres restants...")

    recovered = 0
    for idx, book_id in enumerate(missing, start=1):
        info = db[book_id]
        year = extract_year_from_local_text(info.get("file_path", ""))
        if year is None:
            year = fetch_wikidata_year(info["title"])
            time.sleep(0.15)

        if year is not None:
            info["first_publish_year"] = year
            recovered += 1

        if idx % 30 == 0 or idx == len(missing):
            print(f"Progression : {idx}/{len(missing)} ({recovered} années récupérées)", flush=True)

    METADATA_FILE.write_text(
        json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    remaining = sum(1 for v in db.values() if v.get("first_publish_year") is None)
    print(f"Terminé ! {recovered} années récupérées. Total renseigné : {len(db) - remaining}/{len(db)}.")


if __name__ == "__main__":
    main()