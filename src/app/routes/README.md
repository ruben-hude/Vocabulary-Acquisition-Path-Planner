# Interactive Book Map

## Description

This interactive map visualizes vocabulary relationships between the books
available in `data/raw/gutenberg_books`.

Each book is represented by a node. A connection is created between two books
when they share word groups. The displayed similarity is calculated using the
Jaccard index:

```text
similarity = common word groups / word groups present in both books
```

The **Similarity threshold** slider shows only connections whose similarity is
greater than or equal to the selected value. The value ranges from 0% to 100%.
Clicking a book shows only its connections. Click the empty map background to
show all connections again.
The books are positioned using a D3.js force simulation and can be moved with
the mouse.

## Requirements

- Python 3
- Project dependencies
- FastAPI and Uvicorn
- An internet connection to load D3.js from its CDN

From the project root, optionally create and activate a virtual environment,
then install the required dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install fastapi uvicorn
pip install pandas openpyxl
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn
pip install pandas openpyxl
```

## Launch

From the project root, start the FastAPI API with:

```powershell
$env:PYTHONPATH = "$PWD\src"
fastapi dev src/app/main.py
```

Open the page you want to test:

```text
http://127.0.0.1:8000/render.html
```

The server exposes the interactive page and API routes through
`src/app/main.py`. The static page is located in `src/app/routes/static`.

## Test the profile workflow

The `ui-v2.html` page uses the real profile and path APIs. On Windows, start
the server with `PYTHONPATH` set as above, then open:

```text
http://127.0.0.1:8000/ui-v2.html
```

On the profile page, select the known-words count to open **Mes livres lus**.
The page lists completed books from newest to oldest and provides a search by
title or author. Select a result to mark it as read or undo its read status.
Those changes are stored in `data/processed/reading_history.json`.

To calculate a path, open **Parcours**, search for a target by title or author,
select a result, adjust the comprehension threshold if needed, and select
**Calculer le chemin**. Leave `USE_FAKE_DATA` unset or set it to `0` to use
the real data service.

On macOS or Linux, set the import path before starting the API:

```bash
export PYTHONPATH=src
fastapi dev src/app/main.py
```

## Structure

- `main.py`: main FastAPI application.
- `routes/pathhandler.py`: book and similarity API routes.
- `routes/profilehandler.py`: profile and preferences API routes.
- `static/render.html`: HTML interface for the map.
- `static/render.js`: Data retrieval, D3.js graph construction, and similarity
  threshold handling.
