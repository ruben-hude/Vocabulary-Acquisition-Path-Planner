from fastapi import APIRouter, Depends

from app.models import CurrentPath, Preferences, Profile, ReadBook
from app.services import fake_data

router = APIRouter(prefix="/api", tags=["profile"])


def get_profile_data():
    return fake_data


@router.get("/profile", response_model=Profile)
def get_profile(profile_data=Depends(get_profile_data)):
    return profile_data.get_profile()


@router.get("/read-books", response_model=list[ReadBook])
def get_read_books(profile_data=Depends(get_profile_data)):
    return profile_data.get_read_books()


@router.get("/current-path", response_model=CurrentPath)
def get_current_path(profile_data=Depends(get_profile_data)):
    return profile_data.get_current_path()


@router.get("/preferences", response_model=Preferences)
def get_preferences(profile_data=Depends(get_profile_data)):
    return profile_data.get_preferences()


@router.put("/preferences", response_model=Preferences)
def save_preferences(
    new_preferences: Preferences,
    profile_data=Depends(get_profile_data),
):
    return profile_data.save_preferences(new_preferences)