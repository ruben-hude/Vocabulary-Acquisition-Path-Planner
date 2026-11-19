from fastapi import APIRouter

from app.models import CheminActuel, LivreLu, Preferences, Profil
from app.services import donnees_factices as donnees

router = APIRouter(prefix="/api", tags=["profil"])


@router.get("/profil", response_model=Profil)
def lire_profil():
    return donnees.profil()


@router.get("/livres-lus", response_model=list[LivreLu])
def lire_livres_lus():
    return donnees.livres_lus()


@router.get("/chemin-actuel", response_model=CheminActuel)
def lire_chemin_actuel():
    return donnees.chemin_actuel()


@router.get("/preferences", response_model=Preferences)
def lire_preferences():
    return donnees.preferences()


@router.put("/preferences", response_model=Preferences)
def modifier_preferences(nouvelles: Preferences):
    # FastAPI lit le JSON du corps de la requête et le valide avec le modèle Preferences
    return donnees.enregistrer_preferences(nouvelles)