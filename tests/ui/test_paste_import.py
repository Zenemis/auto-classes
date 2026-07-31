"""Collage d'un tableau Pronote : ce qui est importé, et ce qui est ignoré sans bruit.

Le presse-papiers d'un tableau copié depuis la page Pronote arrive en colonnes séparées
par des tabulations. Tout le reste — du texte quelconque, une liste sans en-tête — doit
sortir par « rien à importer », jamais par une erreur.
"""

import tkinter as tk

import customtkinter as ctk
import pytest

from auto_classes.ui.paste_import import is_text_input, students_from_clipboard

PASTED_TABLE = (
    "Nom\tPrénom\tNé(e) le\tPrénom d'usage\tSexe\tClasse\n"
    "MARTIN\tSophie\t13/04/2012\t\tF\tCM2C\n"
    "DE LA FONTAINE\tGabriel\t12/12/2011\t\tG\tCM2C\n"
)


def test_a_pasted_pronote_table_is_imported() -> None:
    imported = students_from_clipboard(PASTED_TABLE)

    assert imported is not None
    assert imported.names == ("MARTIN Sophie", "DE LA FONTAINE Gabriel")


def test_a_pasted_semicolon_csv_is_imported_too() -> None:
    """Un passage par Excel avant le collage rend du point-virgule plutôt que des tabulations."""
    imported = students_from_clipboard("Nom;Prénom\nMARTIN;Sophie")

    assert imported is not None
    assert imported.names == ("MARTIN Sophie",)


@pytest.mark.parametrize(
    "clipboard",
    [
        pytest.param(None, id="presse-papiers indisponible"),
        pytest.param("", id="presse-papiers vide"),
        pytest.param("   \n  ", id="blancs"),
        pytest.param("https://exemple.fr/page", id="une adresse"),
        pytest.param("Bonjour, comment ça va ?", id="du texte courant"),
        pytest.param("MARTIN\tSophie\nDURAND\tAntoine", id="tableau sans en-tête"),
        pytest.param("Nom\tClasse\nMARTIN\tCM2C", id="en-tête sans la colonne Prénom"),
        pytest.param("Nom\tPrénom\n", id="en-tête sans aucune ligne"),
    ],
)
def test_anything_that_is_not_a_student_list_is_ignored_silently(clipboard: str | None) -> None:
    assert students_from_clipboard(clipboard) is None


# ------------------------------------------------------- priorité à la saisie


def test_text_widgets_keep_their_own_paste(root) -> None:
    entry = tk.Entry(root)
    text = tk.Text(root)
    try:
        assert is_text_input(entry)
        assert is_text_input(text)
    finally:
        entry.destroy()
        text.destroy()


def test_a_customtkinter_entry_is_recognized_through_the_widget_it_wraps(root) -> None:
    """`focus_get` ne rend jamais le `CTkEntry` lui-même, mais le `tk.Entry` qu'il enveloppe."""
    ctk_entry = ctk.CTkEntry(root)
    try:
        inner = [child for child in ctk_entry.winfo_children() if isinstance(child, tk.Entry)]
        assert inner, "CTkEntry n'enveloppe plus un tk.Entry : revoir `is_text_input`"
        assert is_text_input(inner[0])
    finally:
        ctk_entry.destroy()


def test_other_widgets_do_not_swallow_the_shortcut(root) -> None:
    button = ctk.CTkButton(root, text="Générer")
    try:
        assert not is_text_input(button)
        assert not is_text_input(root)
        assert not is_text_input(None)
    finally:
        button.destroy()
