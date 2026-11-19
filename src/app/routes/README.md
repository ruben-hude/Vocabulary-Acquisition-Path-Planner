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
fastapi dev src/app/main.py
```

Then open the address displayed by FastAPI, typically:

```text
http://127.0.0.1:8000
```

The server exposes the interactive page and API routes through
`src/app/main.py`. The static page is located in `src/app/routes/static`.

## Structure

- `main.py`: main FastAPI application.
- `routes/pathhandler.py`: book and similarity API routes.
- `routes/profilehandler.py`: profile and preferences API routes.
- `static/render.html`: HTML interface for the map.
- `static/render.js`: Data retrieval, D3.js graph construction, and similarity
  threshold handling.
