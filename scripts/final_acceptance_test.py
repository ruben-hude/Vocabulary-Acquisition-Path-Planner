import json
import re
from pathlib import Path

METADATA_FILE = Path("data/books_metadata.json")
REQUIRED_KEYS = {
    "id", "file_path", "title", "author",
    "download_count", "gutenberg_release_date", "first_publish_year"
}

db = json.load(open(METADATA_FILE, encoding="utf-8"))

schema_errors = []
file_errors = []
chrono_errors = []
round_years = []
seen_paths = set()
duplicate_paths = []

for bid, info in db.items():
    # 1. Schéma et types
    missing_keys = REQUIRED_KEYS - set(info.keys())
    if missing_keys or not isinstance(info.get("first_publish_year"), int) or not str(info.get("title", "")).strip():
        schema_errors.append((bid, missing_keys, info.get("first_publish_year")))

    # 2. Fichiers physiques
    fp = info.get("file_path", "")
    p = Path(fp)
    if not p.exists() or p.stat().st_size < 1000:
        file_errors.append((bid, fp, p.exists(), p.stat().st_size if p.exists() else 0))
    if fp in seen_paths:
        duplicate_paths.append((bid, fp))
    seen_paths.add(fp)

    # 3. Cohérence chronologique
    pub = info.get("first_publish_year")
    if isinstance(pub, int):
        if pub < 1450 or pub > 2026:
            chrono_errors.append((bid, info["title"][:40], pub, "Hors bornes"))
        g_match = re.search(r"\b(199\d|20[0-2]\d)\b", str(info.get("gutenberg_release_date", "")))
        if g_match and pub > int(g_match.group(1)):
            chrono_errors.append((bid, info["title"][:40], pub, f"> Gutenberg {g_match.group(1)}"))
        if pub in {1500, 1600, 1700, 1800, 1900, 2000}:
            round_years.append((bid, info["title"][:42], info["author"][:20], pub))

print("==================================================")
print(f"RAPPORT DE RECETTE MÉTHODIQUE ({len(db)} ENTRÉES)")
print("==================================================")
print(f"1. Erreurs de schéma / types     : {len(schema_errors)}")
print(f"2. Fichiers manquants / < 1 Ko   : {len(file_errors)}")
print(f"3. Doublons de fichiers          : {len(duplicate_paths)}")
print(f"4. Anomalies chronologiques      : {len(chrono_errors)}")
print(f"5. Années rondes (1700/1800/1900): {len(round_years)}")

if schema_errors:
    print("\n[!] Détail erreurs schéma :", schema_errors[:10])
if file_errors:
    print("\n[!] Détail erreurs fichiers :", file_errors[:10])
if chrono_errors:
    print("\n[!] Détail anomalies chrono :", chrono_errors[:10])

if round_years:
    print("\n--- Liste complète des années rondes (pour vérification rapide) ---")
    for bid, t, a, y in round_years:
        print(f"  {bid:<7} | {y} | {a:<20} | {t}")

sorted_books = sorted(db.items(), key=lambda x: x[1]["first_publish_year"])

print("\n--- TOP 10 LES PLUS ANCIENS ---")
for bid, v in sorted_books[:10]:
    print(f"  {bid:<7} | {v['first_publish_year']} | {v['author'][:22]:<22} | {v['title'][:45]}")

print("\n--- TOP 10 LES PLUS RÉCENTS ---")
for bid, v in sorted_books[-10:]:
    print(f"  {bid:<7} | {v['first_publish_year']} | {v['author'][:22]:<22} | {v['title'][:45]}")
