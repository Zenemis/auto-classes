"""Fenêtre de connexion Pronote : ce qu'elle envoie, et ce qu'elle fait du résultat.

La connexion tourne sur un thread et le résultat est relevé par `after` : les tests
laissent donc tourner la boucle Tk jusqu'à ce que la fenêtre se referme (succès) ou
affiche une erreur, plutôt que d'inspecter le thread.
"""

import time

import pytest

from auto_classes.pronote import ENT_NONE, PronoteError, Roster
from auto_classes.pronote.client import StudentClass
from auto_classes.ui.views.pronote_dialog import PronoteDialog

ROSTER = Roster(classes=(StudentClass("3A", ("MARTIN Léa", "DUPONT Hugo")),))

TIMEOUT_S = 5


def settle(root, dialog) -> None:
    """Fait tourner la boucle Tk jusqu'à l'issue de la connexion."""
    deadline = time.monotonic() + TIMEOUT_S
    while time.monotonic() < deadline:
        root.update()
        if not dialog.winfo_exists() or dialog.error_message:
            return
        time.sleep(0.01)
    pytest.fail("la connexion Pronote n'a rendu ni élèves ni erreur")


def fill(dialog, *, url="demo.fr/pronote", username="cpe", password="secret") -> None:
    for entry, value in ((dialog._url, url), (dialog._username, username), (dialog._password, password)):
        entry.delete(0, "end")
        entry.insert(0, value)


@pytest.fixture
def open_dialog(root):
    """Ouvre une fenêtre par test et la referme, même si le test échoue en route."""
    dialogs = []

    def factory(**kwargs):
        dialog = PronoteDialog(root, **kwargs)
        dialogs.append(dialog)
        root.update()
        return dialog

    yield factory

    for dialog in dialogs:
        if dialog.winfo_exists():
            dialog.destroy()
    root.update()


def test_successful_connection_returns_the_roster(root, open_dialog) -> None:
    dialog = open_dialog(fetcher=lambda *args: ROSTER, ents={})
    fill(dialog)

    dialog._submit()
    settle(root, dialog)

    assert dialog._result == ROSTER
    assert not dialog.winfo_exists()  # refermée : `show()` rendrait la main


def test_connection_failure_is_shown_without_closing_the_window(root, open_dialog) -> None:
    def refuse(*args):
        raise PronoteError("Identifiant ou mot de passe refusé par Pronote.")

    dialog = open_dialog(fetcher=refuse, ents={})
    fill(dialog, password="faux")

    dialog._submit()
    settle(root, dialog)

    assert dialog.error_message == "Identifiant ou mot de passe refusé par Pronote."
    assert dialog.winfo_exists()  # l'utilisateur corrige sans tout ressaisir


def test_unexpected_failure_is_surfaced_rather_than_swallowed(root, open_dialog) -> None:
    def explode(*args):
        raise RuntimeError("panne inédite")

    dialog = open_dialog(fetcher=explode, ents={})
    fill(dialog)

    dialog._submit()
    settle(root, dialog)

    assert "panne inédite" in dialog.error_message


def test_credentials_and_ent_reach_the_fetcher(root, open_dialog) -> None:
    calls = []
    ent_function = object()

    dialog = open_dialog(
        fetcher=lambda *args: (calls.append(args), ROSTER)[1],
        ents={"mon ent": ent_function},
    )
    fill(dialog, url="demo.fr/pronote", username="cpe", password="secret")
    dialog._ent.set("mon ent")

    dialog._submit()
    settle(root, dialog)

    assert calls == [("demo.fr/pronote", "cpe", "secret", ent_function)]


def test_no_ent_selected_sends_none(root, open_dialog) -> None:
    calls = []

    dialog = open_dialog(
        fetcher=lambda *args: (calls.append(args), ROSTER)[1],
        ents={"mon ent": object()},
    )
    fill(dialog)
    dialog._ent.set(ENT_NONE)

    dialog._submit()
    settle(root, dialog)

    assert calls[0][3] is None
