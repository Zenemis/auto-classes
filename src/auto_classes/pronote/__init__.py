"""Récupération des listes d'élèves depuis Pronote.

Rien ici ne connaît l'interface : le module renvoie un `Roster` ou lève une
`PronoteError` portant un message déjà rédigé pour l'utilisateur.
"""

from auto_classes.pronote.client import (
    ENT_NONE,
    Connection,
    Roster,
    StudentClass,
    available_ents,
    connect_with_qr_code,
    connect_with_token,
    fetch_roster,
    normalize_url,
    parse_qr_payload,
)
from auto_classes.pronote.credentials import (
    SavedCredentials,
    forget_credentials,
    load_credentials,
    save_credentials,
)
from auto_classes.pronote.errors import PronoteError

__all__ = [
    "ENT_NONE",
    "Connection",
    "PronoteError",
    "Roster",
    "SavedCredentials",
    "StudentClass",
    "available_ents",
    "connect_with_qr_code",
    "connect_with_token",
    "fetch_roster",
    "forget_credentials",
    "load_credentials",
    "normalize_url",
    "parse_qr_payload",
    "save_credentials",
]
