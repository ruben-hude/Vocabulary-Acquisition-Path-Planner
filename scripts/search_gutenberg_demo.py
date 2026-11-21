"""Recherche un livre cible (local + Internet Archive / Gutenberg) et calcule un chemin de lecture."""

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.search.graph import Graph
from vocabulary_acquisition_path_planner.search.path_finder import PathFinder


def clean_gutenberg_text(raw_text: str) -> str:
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


def download_from_ia_identifier(identifier: str) -> str:
    """Télécharge le fichier texte d'un livre depuis son identifiant Internet Archive."""
    meta_url = f"https://archive.org/metadata/{urllib.parse.quote(identifier)}"
    req = urllib.request.Request(meta_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        meta = json.loads(resp.read().decode("utf-8"))

    files = meta.get("files", [])
    # Priorité aux fichiers texte Gutenberg (.txt hors _djvu.txt et _meta.txt)
    txt_files = [
        f["name"]
        for f in files
        if f.get("name", "").endswith(".txt")
        and not f["name"].endswith("_djvu.txt")
        and not f["name"].endswith("_meta.txt")
    ]
    if not txt_files:
        # Sinon n'importe quel .txt disponible
        txt_files = [f["name"] for f in files if f.get("name", "").endswith(".txt")]

    if not txt_files:
        raise RuntimeError(f"Aucun fichier texte trouvé dans l'archive {identifier}")

    file_url = f"https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(txt_files[0])}"
    req_txt = urllib.request.Request(file_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req_txt, timeout=25) as resp_txt:
        raw = resp_txt.read().decode("utf-8", errors="ignore")

    return clean_gutenberg_text(raw)


def search_target_book(query: str, local_metadata: dict) -> list[dict]:
    """Cherche d'abord dans les 1000 livres locaux, puis dans la collection Gutenberg sur Internet Archive."""
    results = []
    q_lower = query.lower()

    # 1. Recherche instantanée dans les 1000 livres locaux
    for bid_str, info in local_metadata.items():
        if q_lower in info["title"].lower() or q_lower in info["author"].lower():
            results.append({
                "id": bid_str,
                "title": info["title"],
                "author": info["author"],
                "source": "Local (déjà dans vos 1000 livres)",
                "file_path": info["file_path"],
            })
            if len(results) >= 5:
                return results

    # 2. Recherche directe dans le miroir Gutenberg d'Internet Archive (toujours accessible)
    ia_query = urllib.parse.quote(f'collection:(gutenberg) AND title:("{query}") AND language:(eng)')
    url = (
        f"https://archive.org/advancedsearch.php?q={ia_query}"
        "&fl[]=identifier&fl[]=title&fl[]=creator&sort[]=downloads+desc&rows=5&output=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for doc in data.get("response", {}).get("docs", []):
            identifier = doc.get("identifier", "")
            if not identifier:
                continue
            creator = doc.get("creator", "Inconnu")
            if isinstance(creator, list):
                creator = creator[0]

            results.append({
                "id": identifier,
                "title": doc.get("title", "Sans titre"),
                "author": creator,
                "source": "Gutenberg (Internet Archive)",
                "ia_identifier": identifier,
            })
            if len(results) >= 5:
                break
    except Exception as e:
        print(f"Note : recherche en ligne indisponible ({e}).")

    return results[:5]


def main():
    parser = argparse.ArgumentParser(description="Recherche un livre cible et trouve un chemin de lecture.")
    parser.add_argument("target_query", type=str, help="Titre ou auteur recherché (ex: 'Frankenstein')")
    parser.add_argument("--max-local-books", type=int, default=120, help="Nombre de livres locaux chargés dans le graphe")
    parser.add_argument("--comprehension-threshold", type=float, default=0.8)
    parser.add_argument("--time-limit-seconds", type=float, default=20)
    args = parser.parse_args()

    metadata_path = Path("data/books_metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}

    print(f"Recherche de '{args.target_query}' dans la base Gutenberg ({len(metadata)} livres en local)...")
    matches = search_target_book(args.target_query, metadata)
    if not matches:
        print("Aucun livre trouvé pour cette recherche.")
        return

    print("\nRésultats trouvés :")
    for idx, book in enumerate(matches):
        print(f"  [{idx}] {book['title']} — {book['author']} [{book['source']}]")

    choice = int(input("\nEntrez le numéro du livre cible choisi [0] : ") or 0)
    chosen = matches[choice]
    target_id = str(chosen["id"])

    # Chargement du livre cible (local ou téléchargement direct depuis Internet Archive)
    if "file_path" in chosen and Path(chosen["file_path"]).exists():
        target_path = Path(chosen["file_path"])
    else:
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", target_id)
        target_path = Path(f"data/raw/gutenberg_books/book_{safe_id}.txt")
        if not target_path.exists():
            print(f"Téléchargement du livre cible ({target_id})...")
            clean_txt = download_from_ia_identifier(chosen["ia_identifier"])
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(clean_txt, encoding="utf-8")

    target_media = Media.from_text_file(target_path)

    # Livre de départ déjà lu (premier livre de l'index)
    first_id = next(iter(metadata))
    source_info = metadata[first_id]
    source_media = Media.from_text_file(Path(source_info["file_path"]))

    vocabulary = LearnerVocabulary()
    vocabulary.account_for_media(source_media)

    local_books = []
    media_to_title = {
        id(target_media): f"{chosen['title']} - {chosen['author']} ({target_id})"
    }

    for bid_str, info in list(metadata.items())[: args.max_local_books]:
        if bid_str in {first_id, target_id}:
            continue
        p = Path(info["file_path"])
        if p.exists():
            m = Media.from_text_file(p)
            local_books.append(m)
            media_to_title[id(m)] = f"{info['title']} - {info['author']} (ID: {bid_str})"

    all_media = local_books + [target_media]
    print(f"\nLivre de départ déjà lu : {source_info['title']}")
    print(f"Construction du graphe avec {len(all_media)} livres...")

    graph = Graph(
        all_media,
        initial_vocabulary=vocabulary,
        comprehension_threshold=args.comprehension_threshold,
    )

    print(f"Compréhension initiale du livre cible : {vocabulary.know_percentage(target_media):.2%}")
    print("Calcul du chemin optimal en cours...")

    try:
        result = PathFinder(graph).find_path(target_media, time_limit_seconds=args.time_limit_seconds)
    except (LookupError, TimeoutError) as exc:
        print(f"Résultat : {exc}")
        return

    print(f"\nChemin recommandé (Coût total : {result.cost} mots) :")
    for step, m in enumerate(result.media, start=1):
        print(f"  {step}. {media_to_title.get(id(m), 'Livre inconnu')}")


if __name__ == "__main__":
    main()