"""Récupération des listes d'élèves depuis Pronote.

Rien ici ne connaît l'interface : le module renvoie un `Roster` ou lève une
`PronoteError` portant un message déjà rédigé pour l'utilisateur.
"""

from auto_classes.pronote.client import (
    ENT_NONE,
    Roster,
    StudentClass,
    available_ents,
    fetch_roster,
    normalize_url,
)
from auto_classes.pronote.errors import PronoteError

__all__ = [
    "ENT_NONE",
    "PronoteError",
    "Roster",
    "StudentClass",
    "available_ents",
    "fetch_roster",
    "normalize_url",
]
