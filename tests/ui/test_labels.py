"""Tests de la troncature.

Seul l'algorithme est testé ici, avec une mesure factice : le câblage Tk (écoute du
`<Configure>` du conteneur, conversion d'échelle) demande une fenêtre réellement
affichée, ce qu'un test automatisé ne peut pas garantir.
"""

import pytest

from auto_classes.ui.components.labels import ELLIPSIS, ellipsize

CHAR_WIDTH = 10


def measure(text: str) -> int:
    """Police factice à largeur fixe : « … » compte pour un caractère."""
    return CHAR_WIDTH * len(text)


def test_text_that_fits_is_returned_unchanged():
    assert ellipsize("Alice", 100, measure) == "Alice"


def test_text_exactly_at_the_limit_is_kept_whole():
    assert ellipsize("Alice", 5 * CHAR_WIDTH, measure) == "Alice"


def test_too_long_text_is_cut_and_marked():
    result = ellipsize("Marie-Charlotte", 10 * CHAR_WIDTH, measure)

    assert result.endswith(ELLIPSIS)
    assert result == "Marie-Cha" + ELLIPSIS


def test_result_always_fits_the_available_width():
    for available in range(1, 30):
        result = ellipsize("Vandenbrouck", available * CHAR_WIDTH, measure)
        assert measure(result) <= available * CHAR_WIDTH


def test_result_is_a_prefix_of_the_original():
    result = ellipsize("Marie-Charlotte Vandenbrouck", 12 * CHAR_WIDTH, measure)
    kept = result[: -len(ELLIPSIS)]
    assert "Marie-Charlotte Vandenbrouck".startswith(kept)


def test_trailing_space_is_dropped_before_the_ellipsis():
    # « Marie » suivi d'un espace : on ne veut pas « Marie …ays ».
    result = ellipsize("Marie Charlotte", 7 * CHAR_WIDTH, measure)
    assert result == "Marie" + ELLIPSIS


def test_ellipsis_alone_when_nothing_fits():
    assert ellipsize("Alice", CHAR_WIDTH, measure) == ELLIPSIS


def test_zero_width_still_returns_the_marker():
    assert ellipsize("Alice", 0, measure) == ELLIPSIS


def test_empty_text_is_left_alone():
    assert ellipsize("", 100, measure) == ""


@pytest.mark.parametrize("text", ["Léa", "Gaëlle", "Inès"])
def test_accented_names_are_handled_like_any_other(text):
    assert ellipsize(text, 100, measure) == text
