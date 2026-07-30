"""Lisibilité et distinction des couleurs d'outil.

Le code couleur porte du sens : quatre familles nettement séparées, et un texte
lisible sur chacune dans les deux thèmes.
"""

import itertools

import pytest

from auto_classes.ui.theme import MIN_CONTRAST, Palette, _contrast, readable_on

TOOL_COLORS = {
    "mettre avec": Palette.TOGETHER,
    "séparer de": Palette.APART,
    "inclure dans": Palette.INCLUDE,
    "exclure de": Palette.EXCLUDE,
}

LIGHT, DARK = 0, 1


def perceptual_distance(first: str, second: str) -> float:
    """Écart perceptuel approché (moyenne rouge pondérée) : ~30 = confusable."""
    red_a, green_a, blue_a = (int(first[i : i + 2], 16) for i in (1, 3, 5))
    red_b, green_b, blue_b = (int(second[i : i + 2], 16) for i in (1, 3, 5))
    mean_red = (red_a + red_b) / 2
    return (
        (2 + mean_red / 256) * (red_a - red_b) ** 2
        + 4 * (green_a - green_b) ** 2
        + (2 + (255 - mean_red) / 256) * (blue_a - blue_b) ** 2
    ) ** 0.5


@pytest.mark.parametrize("theme", [LIGHT, DARK], ids=["clair", "sombre"])
@pytest.mark.parametrize(("name", "color"), TOOL_COLORS.items())
def test_tool_labels_stay_readable(name, color, theme):
    assert _contrast(color[theme], readable_on(color)[theme]) >= MIN_CONTRAST


@pytest.mark.parametrize("theme", [LIGHT, DARK], ids=["clair", "sombre"])
@pytest.mark.parametrize(
    ("first", "second"), list(itertools.combinations(TOOL_COLORS, 2))
)
def test_tools_are_told_apart(first, second, theme):
    """« Mettre avec » et « Inclure dans » étaient trop proches : plus jamais."""
    distance = perceptual_distance(TOOL_COLORS[first][theme], TOOL_COLORS[second][theme])
    assert distance > 100, f"{first} et {second} se confondent ({distance:.0f})"


def test_together_is_a_green_leaning_cyan():
    red, green, blue = (int(Palette.TOGETHER[LIGHT][i : i + 2], 16) for i in (1, 3, 5))
    assert green > red and blue > red, "le vert doit dominer, avec une pointe de cyan"
    assert green > blue, "sans basculer dans le bleu"


def test_readable_on_prefers_white_when_it_holds():
    assert readable_on(("#014D40", "#014D40")) == Palette.TEXT_ON_ACCENT


def test_readable_on_falls_back_to_ink_on_pale_backgrounds():
    assert readable_on(("#FFE9A8", "#FFE9A8")) == Palette.INK


def test_contrast_is_symmetric_and_bounded():
    assert _contrast("#000000", "#FFFFFF") == pytest.approx(21, abs=0.1)
    assert _contrast("#FFFFFF", "#000000") == pytest.approx(21, abs=0.1)
    assert _contrast("#123456", "#123456") == pytest.approx(1.0)
