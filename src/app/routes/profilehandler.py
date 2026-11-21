import os
from fastapi import APIRouter

from app.models import CurrentPath, Preferences, Profile, ReadBook
from app.services import fake_data, real_data

# Si USE_FAKE_DATA=1 dans le terminal, on utilise fake_data, sinon real_data
USE_FAKE = os.getenv("USE_FAKE_DATA", "0") == "1"
data_service = fake_data if USE_FAKE else real_data

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/profile", response_model=Profile)
def get_profile():
    return data_service.get_profile()


@router.get("/read-books", response_model=list[ReadBook])
def get_read_books():
    return data_service.get_read_books()


@router.get("/current-path", response_model=CurrentPath)
def get_current_path():
    return data_service.get_current_path()


@router.get("/preferences", response_model=Preferences)
def get_preferences():
    return data_service.get_preferences()


@router.put("/preferences", response_model=Preferences)
def save_preferences(new_preferences: Preferences):
    return data_service.save_preferences(new_preferences)