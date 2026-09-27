# Using Scripts in `scripts/`

This guide explains how to execute the Python scripts located in the `scripts/` directory.

## Resolving Import Errors (`src/`)

Because the project modules are located in `src/vocabulary_acquisition_path_planner`, Python will raise a `ModuleNotFoundError` if you run a script directly from the `scripts/` directory without specifying where to find the source files.

To let Python know where to find the dependencies in `src`, use the `PYTHONPATH` environment variable:

```bash
PYTHONPATH=src python3 scripts/find_book_path.py data/raw/gutenberg_books/book_1342.txt data/raw/gutenberg_books/book_11.txt
```

On Windows (PowerShell):
```powershell
$env:PYTHONPATH="src"
python scripts/find_book_path.py data/raw/gutenberg_books/book_1342.txt data/raw/gutenberg_books/book_11.txt
```

On Windows (Command Prompt / CMD):
```cmd
set PYTHONPATH=src
python scripts\find_book_path.py data\raw\gutenberg_books\book_1342.txt data\raw\gutenberg_books\book_11.txt
```

---

## Available Scripts

### 1. `find_book_path.py`
Finds an optimal reading path between a source book and a target book using available books in the corpus.

* **Positional Arguments:**
  * `source`: Path to the source text file (e.g., `data/raw/gutenberg_books/book_1342.txt`).
  * `target`: Path to the target text file (e.g., `data/raw/gutenberg_books/book_11.txt`).

* **Optional Arguments:**
  * `--comprehension-threshold`: Comprehension threshold required (default: `0.8`).
  * `--time-limit-seconds`: Time limit for the path search in seconds (default: `10`).

* **Usage Example:**
  ```bash
  PYTHONPATH=src python3 scripts/find_book_path.py data/raw/gutenberg_books/book_1342.txt data/raw/gutenberg_books/book_11.txt
  ```

---

### 2. `find_non_obvious_book_path.py`
Scans available books in `data/raw/gutenberg_books/` to find a source and target pair where direct reading is insufficient, but a valid multi-step learning path exists.

* **This script takes no command-line arguments.** Configuration variables (directory, threshold, time limit) are defined at the top of the file.

* **Usage Example:**
  ```bash
  PYTHONPATH=src python3 scripts/find_non_obvious_book_path.py
  ```
