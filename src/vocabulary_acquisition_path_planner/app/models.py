from typing import Literal
from pydantic import BaseModel


class PointVocabulaire(BaseModel):
    mois: str                 # "Juin", "Juil."...
    mots_connus: int


class Profil(BaseModel):
    nom: str
    membre_depuis: str
    niveau: str               # "B2"
    mots_connus: int
    historique: list[PointVocabulaire]


class LivreLu(BaseModel):
    id: str
    titre: str
    auteur: str
    niveau: str
    termine_le: str
    mots_appris: int
    couverture_url: str


class EtapeChemin(BaseModel):
    livre_id: str
    titre: str
    auteur: str
    niveau: str
    mots_nouveaux: int
    statut: Literal["lu", "en_cours", "a_venir", "cible"]


class CheminActuel(BaseModel):
    cible_id: str
    cible_titre: str
    type_chemin: str          # "progressif"
    etapes: list[EtapeChemin]


class Preferences(BaseModel):
    genres: list[str]
    livres_aimes: list[str]   # liste d'identifiants de livres

class Noeud(BaseModel):
    id: str
    titre: str
    auteur: str
    niveau: str
    pages: int
    pourcentage_connu: float   # 85.0
    mots_nouveaux: int
    est_cible: bool = False


class Lien(BaseModel):
    source: str                # id du livre de départ
    target: str                # id du livre d'arrivée
    chemin_id: str             # "court", "progressif", "doux"


class ResumeChemin(BaseModel):
    id: str
    nom: str
    livres: list[str]
    duree_heures: int
    difficulte: str
    mots_appris: int


class Graphe(BaseModel):
    noeuds: list[Noeud]
    liens: list[Lien]
    chemins: list[ResumeChemin]