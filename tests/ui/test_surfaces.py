"""États visuels d'une carte cliquable.

La sélection et l'accentuation doivent être *réversibles* : c'est le piège, car
CustomTkinter range la couleur de bordure courante dans `_border_color` et l'écrase à
chaque `configure`. Une carte qui garde son pourtour après désélection signale
qu'un attribut de la classe masque à nouveau celui du widget.
"""

import tkinter as tk

import customtkinter as ctk
import pytest

from auto_classes.ui.components.surfaces import ClickableCard
from auto_classes.ui.theme import Palette


@pytest.fixture(scope="module")
def window():
    try:
        root = ctk.CTk()
    except tk.TclError as error:
        pytest.skip(f"pas d'affichage disponible : {error}")
    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def card(window):
    widget = ClickableCard(window)
    yield widget
    widget.destroy()


def test_idle_card_wears_the_plain_border(card):
    assert card.cget("border_color") == Palette.BORDER
    assert card.cget("border_width") == 1


def test_selection_is_reversible(card):
    card.set_selected(True)
    assert card.cget("border_color") == Palette.SELECTION

    card.set_selected(False)
    assert card.cget("border_color") == Palette.BORDER


def test_selection_survives_several_round_trips(card):
    for _ in range(3):
        card.set_selected(True)
        assert card.cget("border_color") == Palette.SELECTION
        card.set_selected(False)
        assert card.cget("border_color") == Palette.BORDER


def test_accent_is_reversible(card):
    card.set_accent(Palette.APART)
    assert card.cget("border_color") == Palette.APART

    card.set_accent(None)
    assert card.cget("border_color") == Palette.BORDER


def test_filled_accent_thickens_then_restores_the_border(card):
    card.set_accent(Palette.TOGETHER, filled=True)
    assert card.cget("border_width") == 2

    card.set_accent(None)
    assert card.cget("border_width") == 1
    assert card.cget("border_color") == Palette.BORDER


def test_accent_takes_precedence_over_selection(card):
    card.set_selected(True)
    card.set_accent(Palette.APART)
    assert card.cget("border_color") == Palette.APART

    # L'accent retiré, la sélection reprend la main, pas la bordure de repos.
    card.set_accent(None)
    assert card.cget("border_color") == Palette.SELECTION

    card.set_selected(False)
    assert card.cget("border_color") == Palette.BORDER


def test_selection_changes_the_fill_too(card):
    assert card.cget("fg_color") == Palette.SURFACE
    card.set_selected(True)
    assert card.cget("fg_color") == Palette.SELECTION_BG
    card.set_selected(False)
    assert card.cget("fg_color") == Palette.SURFACE


def test_a_custom_idle_border_is_preserved(window):
    """Une carte peut naître avec sa propre bordure : elle doit y revenir."""
    widget = ClickableCard(window, border_color=Palette.BORDER_STRONG)
    widget.set_selected(True)
    widget.set_selected(False)
    assert widget.cget("border_color") == Palette.BORDER_STRONG
    widget.destroy()
