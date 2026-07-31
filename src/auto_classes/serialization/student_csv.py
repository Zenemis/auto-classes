"""Lecture d'une liste d'élèves exportée en CSV (typiquement depuis Pronote).

Seules les colonnes **Nom** et **Prénom** sont lues : tout le reste de l'export
(date de naissance, classe, projet d'accompagnement, allergies…) ne sert pas à la
répartition, et une partie relève de données sensibles qu'il n'y a aucune raison de
faire entrer dans l'application.

Le format d'un export réel n'est pas garanti : Pronote sort du point-virgule en ANSI sur
certaines versions, de la virgule en UTF-8 sur d'autres, avec ou sans BOM. Le lecteur
s'adapte plutôt que d'imposer un format, sauf sur un point : sans les deux colonnes de
nom, il refuse le fichier au lieu de deviner.
"""

from __future__ import annotations

import csv
import unicodedata
from dataclasses import dataclass
from pathlib import Path

# Libellés attendus, sous leur forme normalisée (minuscules, sans accent). La
# comparaison est exacte : « Prénom d'usage », colonne voisine dans les exports Pronote,
# ne doit surtout pas être prise pour « Prénom ».
NAME_COLUMN = "nom"
FIRST_NAME_COLUMN = "prenom"

# Ordre d'essai : `utf-8-sig` avale le BOM qu'Excel ajoute, `cp1252` couvre les exports
# ANSI, `latin-1` ne peut pas échouer et sert de dernier recours plutôt que de refuser
# un fichier pour un seul octet exotique.
ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")

DELIMITERS = ";,\t"

MAX_LISTED_COLUMNS = 10


class CsvImportError(Exception):
    """Fichier inexploitable, avec un message affichable tel quel."""


@dataclass(frozen=True)
class CsvImport:
    """Résultat d'une lecture : les noms retenus, et ce qui a été laissé de côté."""

    names: tuple[str, ...]
    skipped_rows: int = 0


def load_students_csv(path: Path) -> CsvImport:
    """Noms des élèves d'un CSV, sous la forme « NOM Prénom ».

    Même forme que l'import Pronote en ligne : un élève importé par les deux chemins
    n'apparaît ainsi qu'une fois dans la liste.
    """
    text = _read_text(path)
    if not text.strip():
        raise CsvImportError("Ce fichier est vide.")

    reader = csv.reader(text.splitlines(), delimiter=_sniff_delimiter(text))
    try:
        header = next(reader)
    except StopIteration:  # pragma: no cover - déjà écarté par le test de vacuité
        raise CsvImportError("Ce fichier est vide.") from None

    columns = {_normalize(cell): index for index, cell in enumerate(header)}
    _require_name_columns(columns, header)

    name_index = columns[NAME_COLUMN]
    first_name_index = columns[FIRST_NAME_COLUMN]

    names: list[str] = []
    skipped = 0
    for row in reader:
        last = _cell(row, name_index)
        first = _cell(row, first_name_index)
        full_name = f"{last} {first}".strip()
        if full_name:
            names.append(full_name)
        elif any(cell.strip() for cell in row):
            # Ligne porteuse d'autre chose (un total, une note de bas de tableau) mais
            # sans identité : signalée à l'utilisateur, pas importée.
            skipped += 1

    if not names:
        raise CsvImportError("Aucun élève trouvé dans ce fichier.")
    return CsvImport(names=tuple(names), skipped_rows=skipped)


def _read_text(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as error:
        raise CsvImportError(f"Fichier introuvable : {path.name}") from error
    except OSError as error:
        # `strerror` vient du système et n'est pas traduit : il complète le message
        # français, il ne le remplace pas.
        raise CsvImportError(f"Fichier illisible : {path.name} ({error.strerror}).") from error

    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CsvImportError("Encodage du fichier non reconnu.")  # pragma: no cover - latin-1 accepte tout


def _sniff_delimiter(text: str) -> str:
    """Séparateur du fichier, deviné sur son en-tête.

    `csv.Sniffer` se trompe régulièrement sur une seule ligne (il voit un séparateur dans
    l'espace d'un prénom composé) : on prend simplement le candidat le plus fréquent, et
    le point-virgule par défaut, qui est celui des exports Pronote français.
    """
    header = text.splitlines()[0] if text.splitlines() else ""
    counts = {delimiter: header.count(delimiter) for delimiter in DELIMITERS}
    best = max(counts, key=lambda delimiter: counts[delimiter])
    return best if counts[best] else ";"


def _normalize(cell: str) -> str:
    """Libellé de colonne comparable : sans accent, sans casse, sans espaces superflus.

    « PRÉNOM », « Prenom » et « prénom  » désignent la même colonne ; un export ne dit
    pas lequel des trois il utilisera.
    """
    stripped = cell.strip().strip('"').strip()
    decomposed = unicodedata.normalize("NFKD", stripped)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.casefold().split())


def _cell(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


def _require_name_columns(columns: dict[str, int], header: list[str]) -> None:
    missing = [
        label
        for label, key in (("Nom", NAME_COLUMN), ("Prénom", FIRST_NAME_COLUMN))
        if key not in columns
    ]
    if not missing:
        return

    found = [cell.strip() for cell in header if cell.strip()]
    listed = ", ".join(found[:MAX_LISTED_COLUMNS]) or "aucune"
    if len(found) > MAX_LISTED_COLUMNS:
        listed += ", …"
    raise CsvImportError(
        f"Colonne{'s' if len(missing) > 1 else ''} manquante{'s' if len(missing) > 1 else ''} : "
        f"{' et '.join(missing)}.\n\n"
        f"Colonnes trouvées : {listed}.\n\n"
        "L'import a besoin d'une colonne « Nom » et d'une colonne « Prénom »."
    )
