"""Lecture d'un CSV de liste d'élèves.

Le fichier de référence reproduit un export Pronote : point-virgule, colonnes dans
l'ordre de l'écran Ressources › Élèves, dont plusieurs que l'import doit ignorer —
« Prénom d'usage » est volontairement présente, c'est le piège du libellé qui commence
comme « Prénom ».
"""

from pathlib import Path

import pytest

from auto_classes.serialization import CsvImportError, load_students_csv

PRONOTE_HEADER = "Nom;Prénom;Né(e) le;Prénom d'usage;Sexe;Classe;Projet d'accompagnement;Allergies"
PRONOTE_ROWS = (
    "BELLOT;Lise;13/04/2012;;F;CM2C;;",
    "DOGER DE SPEVILLE;Jules;07/11/2012;;G;CM2C;;",
    "HAESEBAERT;Ethan;06/03/2012;;G;CM2C;PPRE;",
    "PALETAN;Amy Latifah Keyon;12/12/2011;;F;CM2C;;",
)


def write_csv(tmp_path: Path, content: str, *, encoding: str = "utf-8") -> Path:
    path = tmp_path / "eleves.csv"
    path.write_bytes(content.encode(encoding))
    return path


@pytest.fixture
def pronote_export(tmp_path: Path) -> Path:
    return write_csv(tmp_path, "\n".join((PRONOTE_HEADER, *PRONOTE_ROWS)))


def test_reads_names_as_surname_then_first_name(pronote_export: Path) -> None:
    """Même forme que l'import Pronote en ligne, pour que les deux chemins se recoupent."""
    imported = load_students_csv(pronote_export)

    assert imported.names == (
        "BELLOT Lise",
        "DOGER DE SPEVILLE Jules",
        "HAESEBAERT Ethan",
        "PALETAN Amy Latifah Keyon",
    )


def test_ignores_every_column_but_name_and_first_name(pronote_export: Path) -> None:
    imported = load_students_csv(pronote_export)

    joined = " ".join(imported.names)
    for unwanted in ("2012", "CM2C", "PPRE", ";"):
        assert unwanted not in joined


def test_usage_first_name_column_is_not_taken_for_the_first_name(tmp_path: Path) -> None:
    """« Prénom d'usage » ne doit jamais se substituer à « Prénom »."""
    path = write_csv(tmp_path, "Nom;Prénom d'usage;Prénom\nBELLOT;Lisou;Lise")

    assert load_students_csv(path).names == ("BELLOT Lise",)


@pytest.mark.parametrize(
    "header",
    [
        pytest.param("NOM;PRENOM", id="majuscules sans accent"),
        pytest.param("nom;prenom", id="minuscules"),
        pytest.param(" Nom ; Prénom ", id="espaces autour"),
        pytest.param('"Nom";"Prénom"', id="libellés entre guillemets"),
    ],
)
def test_column_labels_are_matched_regardless_of_case_accents_and_spacing(
    tmp_path: Path, header: str
) -> None:
    path = write_csv(tmp_path, f"{header}\nBELLOT;Lise")

    assert load_students_csv(path).names == ("BELLOT Lise",)


def test_columns_may_come_in_any_order(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "Classe;Prénom;Nom\nCM2C;Lise;BELLOT")

    assert load_students_csv(path).names == ("BELLOT Lise",)


@pytest.mark.parametrize(
    ("delimiter", "identifier"),
    [pytest.param(",", "virgule", id="virgule"), pytest.param("\t", "tabulation", id="tabulation")],
)
def test_other_delimiters_are_detected(tmp_path: Path, delimiter: str, identifier: str) -> None:
    header = delimiter.join(("Nom", "Prénom", "Classe"))
    row = delimiter.join(("BELLOT", "Lise", "CM2C"))
    path = write_csv(tmp_path, f"{header}\n{row}")

    assert load_students_csv(path).names == ("BELLOT Lise",)


@pytest.mark.parametrize(
    "encoding",
    [
        pytest.param("utf-8", id="utf-8"),
        pytest.param("utf-8-sig", id="utf-8 avec BOM"),
        pytest.param("cp1252", id="ansi windows"),
    ],
)
def test_accented_names_survive_the_usual_encodings(tmp_path: Path, encoding: str) -> None:
    path = write_csv(tmp_path, "Nom;Prénom\nMANDRON-MATOMBÉ;Mahé", encoding=encoding)

    assert load_students_csv(path).names == ("MANDRON-MATOMBÉ Mahé",)


def test_blank_lines_are_not_counted_as_skipped(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "Nom;Prénom\nBELLOT;Lise\n\n;\nGOIX;Charlie\n")

    imported = load_students_csv(path)

    assert imported.names == ("BELLOT Lise", "GOIX Charlie")
    assert imported.skipped_rows == 0


def test_rows_carrying_data_but_no_name_are_counted(tmp_path: Path) -> None:
    """Une ligne de total en pied de tableau : signalée, pas importée."""
    path = write_csv(tmp_path, "Nom;Prénom;Classe\nBELLOT;Lise;CM2C\n;;24 élèves")

    imported = load_students_csv(path)

    assert imported.names == ("BELLOT Lise",)
    assert imported.skipped_rows == 1


def test_row_with_only_a_surname_is_still_imported(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "Nom;Prénom\nBELLOT;\n;Lise")

    assert load_students_csv(path).names == ("BELLOT", "Lise")


def test_short_rows_do_not_break_the_reading(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "Nom;Prénom;Classe\nBELLOT;Lise\nGOIX")

    assert load_students_csv(path).names == ("BELLOT Lise", "GOIX")


# ---------------------------------------------------------------------- refus


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        pytest.param("Nom;Classe;Sexe", "Prénom", id="prénom manquant"),
        pytest.param("Prénom;Classe;Sexe", "Nom", id="nom manquant"),
        pytest.param("Identité;Classe", "Nom et Prénom", id="les deux manquantes"),
    ],
)
def test_missing_name_columns_are_refused(tmp_path: Path, header: str, expected: str) -> None:
    path = write_csv(tmp_path, f"{header}\nvaleur;valeur;valeur")

    with pytest.raises(CsvImportError, match=expected):
        load_students_csv(path)


def test_the_refusal_lists_the_columns_actually_found(tmp_path: Path) -> None:
    """Sans cette liste, l'utilisateur ne sait pas si son fichier a été mal découpé."""
    path = write_csv(tmp_path, "Identité;Classe;Sexe\nBELLOT Lise;CM2C;F")

    with pytest.raises(CsvImportError, match="Identité, Classe, Sexe"):
        load_students_csv(path)


@pytest.mark.parametrize(
    "content",
    [pytest.param("", id="fichier vide"), pytest.param("\n\n  \n", id="lignes blanches")],
)
def test_empty_file_is_refused(tmp_path: Path, content: str) -> None:
    with pytest.raises(CsvImportError, match="vide"):
        load_students_csv(write_csv(tmp_path, content))


def test_header_without_any_row_is_refused(tmp_path: Path) -> None:
    with pytest.raises(CsvImportError, match="Aucun élève"):
        load_students_csv(write_csv(tmp_path, "Nom;Prénom\n"))


def test_missing_file_is_refused(tmp_path: Path) -> None:
    with pytest.raises(CsvImportError, match="introuvable"):
        load_students_csv(tmp_path / "absent.csv")


def test_a_directory_is_refused_without_crashing(tmp_path: Path) -> None:
    """Une sélection malheureuse dans l'explorateur ne doit pas remonter en trace Python."""
    with pytest.raises(CsvImportError):
        load_students_csv(tmp_path)
