from app.models import (
    CheminActuel, EtapeChemin, Graphe, Lien, LivreLu, Noeud,
    Preferences, PointVocabulaire, Profil, ResumeChemin,
)

_preferences = Preferences(genres=["Fantasy", "Classique"], livres_aimes=["narnia"])


def profil() -> Profil:
    mots = [2100, 2380, 2650, 2900, 3050, 3200]
    mois = ["Juin", "Juil.", "Août", "Sept.", "Oct.", "Nov."]
    return Profil(
        nom="User Name",
        membre_depuis="juin 2026",
        niveau="B2",
        mots_connus=3200,
        historique=[PointVocabulaire(mois=m, mots_connus=v) for m, v in zip(mois, mots)],
    )


def livres_lus() -> list[LivreLu]:
    return [
        LivreLu(id="psychology-of-money", titre="The Psychology of Money",
                auteur="Morgan Housel", niveau="B2", termine_le="2026-10-28",
                mots_appris=210, couverture_url="/static/couvertures/psychology.jpg"),
        LivreLu(id="dorian-gray", titre="The Picture of Dorian Gray",
                auteur="Oscar Wilde", niveau="B2", termine_le="2026-10-03",
                mots_appris=320, couverture_url="/static/couvertures/dorian.jpg"),
    ]


def chemin_actuel() -> CheminActuel:
    return CheminActuel(
        cible_id="pride-and-prejudice",
        cible_titre="Pride and Prejudice",
        type_chemin="progressif",
        etapes=[
            EtapeChemin(livre_id="charlottes-web", titre="Charlotte's Web", auteur="E. B. White",
                        niveau="A2", mots_nouveaux=150, statut="lu"),
            EtapeChemin(livre_id="little-prince", titre="The Little Prince", auteur="A. de Saint-Exupéry",
                        niveau="B1", mots_nouveaux=210, statut="en_cours"),
            EtapeChemin(livre_id="animal-farm", titre="Animal Farm", auteur="George Orwell",
                        niveau="B1", mots_nouveaux=340, statut="a_venir"),
            EtapeChemin(livre_id="pride-and-prejudice", titre="Pride and Prejudice", auteur="Jane Austen",
                        niveau="C1", mots_nouveaux=1250, statut="cible"),
        ],
    )


def graphe(cible_id: str) -> Graphe | None:
    if cible_id != "pride-and-prejudice":
        return None                      # cible inconnue
    return Graphe(
        noeuds=[
            Noeud(id="charlottes-web", titre="Charlotte's Web", auteur="E. B. White", niveau="A2",
                  pages=184, pourcentage_connu=92, mots_nouveaux=150),
            Noeud(id="animal-farm", titre="Animal Farm", auteur="George Orwell", niveau="B1",
                  pages=112, pourcentage_connu=85, mots_nouveaux=340),
            Noeud(id="pride-and-prejudice", titre="Pride and Prejudice", auteur="Jane Austen", niveau="C1",
                  pages=432, pourcentage_connu=72, mots_nouveaux=1250, est_cible=True),
        ],
        liens=[
            Lien(source="charlottes-web", target="animal-farm", chemin_id="progressif"),
            Lien(source="animal-farm", target="pride-and-prejudice", chemin_id="progressif"),
        ],
        chemins=[
            ResumeChemin(id="progressif", nom="Chemin progressif",
                         livres=["charlottes-web", "animal-farm"], duree_heures=12,
                         difficulte="Facile", mots_appris=700),
        ],
    )


def preferences() -> Preferences:
    return _preferences


def enregistrer_preferences(nouvelles: Preferences) -> Preferences:
    global _preferences
    _preferences = nouvelles
    return _preferences