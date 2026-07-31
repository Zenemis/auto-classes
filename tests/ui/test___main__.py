"""Choix de la session au démarrage : vide, ou jeu d'essai.

`run` est remplacé partout ici : ouvrir une vraie fenêtre n'apprendrait rien de plus sur
la décision qui précède, et bloquerait sur la boucle d'évènements Tk.
"""

import sys

import pytest

from auto_classes.ui import __main__ as entry_point
from auto_classes.ui.session import SessionState


@pytest.fixture
def launched_session(monkeypatch: pytest.MonkeyPatch) -> list[SessionState]:
    """Collecte la session que `main` transmet à `run`."""
    sessions: list[SessionState] = []
    monkeypatch.setattr(entry_point, "run", sessions.append)
    monkeypatch.setattr(sys, "argv", ["auto-classes-ui"])
    return sessions


def is_demo(session: SessionState) -> bool:
    return bool(session.students)


def test_plain_launch_starts_on_an_empty_session(
    monkeypatch: pytest.MonkeyPatch, launched_session: list[SessionState]
) -> None:
    monkeypatch.setattr(entry_point, "both_control_keys_held", lambda: False)
    entry_point.main()
    assert not is_demo(launched_session[0])


def test_both_control_keys_held_starts_the_demo(
    monkeypatch: pytest.MonkeyPatch, launched_session: list[SessionState]
) -> None:
    monkeypatch.setattr(entry_point, "both_control_keys_held", lambda: True)
    entry_point.main()
    assert is_demo(launched_session[0])


def test_demo_flag_starts_the_demo_without_the_shortcut(
    monkeypatch: pytest.MonkeyPatch, launched_session: list[SessionState]
) -> None:
    monkeypatch.setattr(entry_point, "both_control_keys_held", lambda: False)
    monkeypatch.setattr(sys, "argv", ["auto-classes-ui", "--demo"])
    entry_point.main()
    assert is_demo(launched_session[0])
