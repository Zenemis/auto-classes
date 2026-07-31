"""Le raccourci « deux Ctrl » ne se déclenche que sur la combinaison exacte.

Ces tests ne peuvent pas presser de vraies touches : ils remplacent la lecture du
clavier par des états choisis, et vérifient la logique qui les interprète.
"""

import sys

import pytest

from auto_classes.ui import debug_mode
from auto_classes.ui.debug_mode import VK_LCONTROL, VK_RCONTROL, both_control_keys_held

DOWN = -32768  # bit de poids fort à 1, tel que le renvoie GetAsyncKeyState (SHORT signé)
UP = 0
# Le bit de poids faible seul : la touche a été relâchée depuis le dernier appel, elle
# n'est pas enfoncée maintenant.
RELEASED_SINCE_LAST_CALL = 1


@pytest.fixture
def on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")


def fake_keyboard(monkeypatch: pytest.MonkeyPatch, states: dict[int, int]) -> None:
    monkeypatch.setattr(debug_mode, "_async_key_state", lambda key: states.get(key, UP))


def test_both_control_keys_down_triggers_the_shortcut(monkeypatch: pytest.MonkeyPatch, on_windows: None) -> None:
    fake_keyboard(monkeypatch, {VK_LCONTROL: DOWN, VK_RCONTROL: DOWN})
    assert both_control_keys_held()


@pytest.mark.parametrize(
    "states",
    [
        pytest.param({VK_LCONTROL: DOWN}, id="ctrl gauche seul"),
        pytest.param({VK_RCONTROL: DOWN}, id="ctrl droit seul"),
        pytest.param({}, id="aucune touche"),
        pytest.param(
            {VK_LCONTROL: RELEASED_SINCE_LAST_CALL, VK_RCONTROL: RELEASED_SINCE_LAST_CALL},
            id="touches relâchées avant le lancement",
        ),
    ],
)
def test_partial_or_stale_combination_does_not_trigger(
    monkeypatch: pytest.MonkeyPatch, on_windows: None, states: dict[int, int]
) -> None:
    fake_keyboard(monkeypatch, states)
    assert not both_control_keys_held()


def test_shortcut_is_inert_outside_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")

    def explode(key: int) -> int:
        raise AssertionError("l'API Windows ne doit pas être appelée hors de Windows")

    monkeypatch.setattr(debug_mode, "_async_key_state", explode)
    assert not both_control_keys_held()


def test_unreachable_keyboard_api_falls_back_to_normal_startup(
    monkeypatch: pytest.MonkeyPatch, on_windows: None
) -> None:
    """Une session sans `user32` accessible démarre normalement plutôt que d'échouer."""

    def explode(key: int) -> int:
        raise OSError("user32 introuvable")

    monkeypatch.setattr(debug_mode, "_async_key_state", explode)
    assert not both_control_keys_held()
