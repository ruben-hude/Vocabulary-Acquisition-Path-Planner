from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.pathhandler import router as path_router
from app.routes.profilehandler import router as profile_router

app = FastAPI(title="Reading and Vocabulary API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(path_router)
app.include_router(profile_router)


@app.get("/api/ping")
def ping():
    return {"message": "pong"}


# Mount last so that it does not hide the API routes.
app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent / "routes" / "static", html=True),
    name="static",
)