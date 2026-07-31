"""Fenêtre de connexion Pronote : ce qu'elle envoie, et ce qu'elle fait du résultat.

La connexion tourne sur un thread et le résultat est relevé par `after` : les tests
laissent donc tourner la boucle Tk jusqu'à ce que la fenêtre se referme (succès) ou
affiche une erreur, plutôt que d'inspecter le thread.
"""

import time

import pytest

from auto_classes.pronote import ENT_NONE, Connection, PronoteError, Roster, SavedCredentials
from auto_classes.pronote.client import StudentClass
from auto_classes.ui.views.pronote_dialog import (
    MODE_PASSWORD,
    MODE_QR,
    MODE_SAVED,
    PronoteDialog,
)

ROSTER = Roster(classes=(StudentClass("3A", ("MARTIN Sophie", "DURAND Antoine")),))

CREDENTIALS = SavedCredentials(
    pronote_url="https://demo.fr/pronote/mobile.viescolaire.html",
    username="cpe",
    password="JETON_INITIAL",
    uuid="uuid-stable",
)
REFRESHED = SavedCredentials(
    pronote_url=CREDENTIALS.pronote_url,
    username="cpe",
    password="JETON_RENOUVELE",
    uuid="uuid-stable",
)

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


def fill_password_form(dialog, *, url="demo.fr/pronote", username="cpe", password="secret") -> None:
    for entry, value in ((dialog._url, url), (dialog._username, username), (dialog._password, password)):
        entry.delete(0, "end")
        entry.insert(0, value)


def fill_qr_form(dialog, *, payload='{"jeton": "aa", "login": "bb", "url": "https://demo.fr"}', pin="1234") -> None:
    dialog._qr_payload.delete("1.0", "end")
    dialog._qr_payload.insert("1.0", payload)
    dialog._qr_pin.delete(0, "end")
    dialog._qr_pin.insert(0, pin)


@pytest.fixture
def open_dialog(root):
    """Ouvre une fenêtre par test et la referme, même si le test échoue en route."""
    dialogs = []

    def factory(**kwargs):
        kwargs.setdefault("ents", {})
        kwargs.setdefault("credentials", None)
        kwargs.setdefault("on_credentials_changed", lambda _credentials: None)
        dialog = PronoteDialog(root, **kwargs)
        dialogs.append(dialog)
        root.update()
        return dialog

    yield factory

    for dialog in dialogs:
        if dialog.winfo_exists():
            dialog.destroy()
    root.update()


# ------------------------------------------------------------- mot de passe


def test_successful_connection_returns_the_roster(root, open_dialog) -> None:
    dialog = open_dialog(fetcher=lambda *args: ROSTER)
    dialog._mode.set(MODE_PASSWORD)
    dialog._on_mode_changed(MODE_PASSWORD)
    fill_password_form(dialog)

    dialog._submit()
    settle(root, dialog)

    assert dialog._result == ROSTER
    assert not dialog.winfo_exists()  # refermée : `show()` rendrait la main


def test_connection_failure_is_shown_without_closing_the_window(root, open_dialog) -> None:
    def refuse(*args):
        raise PronoteError("Identifiant ou mot de passe refusé par Pronote.")

    dialog = open_dialog(fetcher=refuse)
    dialog._mode.set(MODE_PASSWORD)
    dialog._on_mode_changed(MODE_PASSWORD)
    fill_password_form(dialog, password="faux")

    dialog._submit()
    settle(root, dialog)

    assert dialog.error_message == "Identifiant ou mot de passe refusé par Pronote."
    assert dialog.winfo_exists()  # l'utilisateur corrige sans tout ressaisir


def test_unexpected_failure_is_surfaced_rather_than_swallowed(root, open_dialog) -> None:
    def explode(*args):
        raise RuntimeError("panne inédite")

    dialog = open_dialog(fetcher=explode)
    dialog._mode.set(MODE_PASSWORD)
    dialog._on_mode_changed(MODE_PASSWORD)
    fill_password_form(dialog)

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
    dialog._mode.set(MODE_PASSWORD)
    dialog._on_mode_changed(MODE_PASSWORD)
    fill_password_form(dialog, url="demo.fr/pronote", username="cpe", password="secret")
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
    dialog._mode.set(MODE_PASSWORD)
    dialog._on_mode_changed(MODE_PASSWORD)
    fill_password_form(dialog)
    dialog._ent.set(ENT_NONE)

    dialog._submit()
    settle(root, dialog)

    assert calls[0][3] is None


# ------------------------------------------------------------------ QR code


def test_qr_code_is_the_default_mode_without_a_saved_account(root, open_dialog) -> None:
    dialog = open_dialog()

    assert dialog._mode.get() == MODE_QR


def test_qr_connection_saves_the_returned_credentials(root, open_dialog) -> None:
    saved = []
    calls = []

    def connect(payload, pin):
        calls.append((payload.strip(), pin))
        return Connection(roster=ROSTER, credentials=REFRESHED)

    dialog = open_dialog(qr_connector=connect, on_credentials_changed=saved.append)
    fill_qr_form(dialog, payload='{"jeton": "aa", "login": "bb", "url": "https://demo.fr"}', pin="4321")

    dialog._submit()
    settle(root, dialog)

    assert calls == [('{"jeton": "aa", "login": "bb", "url": "https://demo.fr"}', "4321")]
    assert saved == [REFRESHED]
    assert dialog._result == ROSTER


def test_a_refused_qr_code_saves_nothing(root, open_dialog) -> None:
    saved = []

    def refuse(payload, pin):
        raise PronoteError("Code à quatre chiffres incorrect, ou QR code expiré.")

    dialog = open_dialog(qr_connector=refuse, on_credentials_changed=saved.append)
    fill_qr_form(dialog, pin="0000")

    dialog._submit()
    settle(root, dialog)

    assert saved == []
    assert "QR code expiré" in dialog.error_message


# --------------------------------------------------------- compte enregistré


def test_a_saved_account_becomes_the_default_mode(root, open_dialog) -> None:
    dialog = open_dialog(credentials=CREDENTIALS)

    assert dialog._mode.get() == MODE_SAVED


def test_the_saved_account_connects_without_any_input(root, open_dialog) -> None:
    calls = []
    saved = []

    def connect(credentials):
        calls.append(credentials)
        return Connection(roster=ROSTER, credentials=REFRESHED)

    dialog = open_dialog(
        credentials=CREDENTIALS, token_connector=connect, on_credentials_changed=saved.append
    )

    dialog._submit()
    settle(root, dialog)

    assert calls == [CREDENTIALS]
    assert dialog._result == ROSTER


def test_the_renewed_token_replaces_the_previous_one(root, open_dialog) -> None:
    """Pronote invalide l'ancien jeton : ne pas réécrire condamnerait le prochain import."""
    saved = []

    dialog = open_dialog(
        credentials=CREDENTIALS,
        token_connector=lambda _credentials: Connection(roster=ROSTER, credentials=REFRESHED),
        on_credentials_changed=saved.append,
    )

    dialog._submit()
    settle(root, dialog)

    assert saved == [REFRESHED]


def test_forgetting_the_account_erases_it_and_falls_back_to_the_qr_code(root, open_dialog) -> None:
    saved = []

    dialog = open_dialog(credentials=CREDENTIALS, on_credentials_changed=saved.append)
    dialog._forget()
    root.update()

    assert saved == [None]  # None = effacement demandé
    assert dialog._mode.get() == MODE_QR
    assert MODE_SAVED not in dialog._mode.cget("values")
