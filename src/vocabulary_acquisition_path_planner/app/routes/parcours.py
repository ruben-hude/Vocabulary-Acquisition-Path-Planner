from fastapi import APIRouter, HTTPException

from app.models import Graphe
from app.services import donnees_factices as donnees

router = APIRouter(prefix="/api", tags=["parcours"])


@router.get("/parcours", response_model=Graphe)
def lire_parcours(cible: str):
    """Appel : /api/parcours?cible=pride-and-prejudice"""
    graphe = donnees.graphe(cible)
    if graphe is None:
        raise HTTPException(status_code=404, detail=f"Livre cible inconnu : {cible}")
    return graphe