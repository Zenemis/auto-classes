"""Conservation du jeton entre deux lancements.

Un fichier illisible ne doit jamais faire échouer le démarrage : il n'y a pas d'erreur à
signaler, seulement un compte à réenregistrer. Ces tests vérifient surtout cette
tolérance, parce que c'est elle qui casse en silence.
"""

import json
from pathlib import Path

import pytest

from auto_classes.pronote.credentials import (
    SavedCredentials,
    default_credentials_path,
    forget_credentials,
    load_credentials,
    new_uuid,
    save_credentials,
)

CREDENTIALS = SavedCredentials(
    pronote_url="https://0123456a.index-education.net/pronote/mobile.viescolaire.html",
    username="cpe",
    password="JETON",
    uuid="uuid-stable",
    client_identifier="ABCDEF",
)


@pytest.fixture
def store(tmp_path: Path) -> Path:
    return tmp_path / "pronote-credentials.json"


def test_saved_credentials_are_read_back_identically(store: Path) -> None:
    save_credentials(CREDENTIALS, store)

    assert load_credentials(store) == CREDENTIALS


def test_saving_replaces_the_previous_token(store: Path) -> None:
    """Pronote en délivre un neuf à chaque connexion ; l'ancien ne doit pas survivre."""
    save_credentials(CREDENTIALS, store)
    renewed = SavedCredentials(
        pronote_url=CREDENTIALS.pronote_url,
        username=CREDENTIALS.username,
        password="JETON_NEUF",
        uuid=CREDENTIALS.uuid,
    )

    save_credentials(renewed, store)

    assert load_credentials(store) == renewed
    assert "JETON" not in store.read_text(encoding="utf-8").replace("JETON_NEUF", "")


def test_the_directory_is_created_if_needed(tmp_path: Path) -> None:
    nested = tmp_path / "auto-classes" / "pronote-credentials.json"

    save_credentials(CREDENTIALS, nested)

    assert load_credentials(nested) == CREDENTIALS


def test_no_file_means_no_account(store: Path) -> None:
    assert load_credentials(store) is None


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("", id="fichier vide"),
        pytest.param("{ceci n'est pas du json", id="json tronqué"),
        pytest.param('"une chaîne"', id="json qui n'est pas un objet"),
        pytest.param('{"username": "cpe"}', id="champs manquants"),
        pytest.param(
            '{"pronote_url": "https://demo.fr", "username": "cpe", "password": "", "uuid": "u"}',
            id="jeton vide",
        ),
        pytest.param(
            '{"pronote_url": "https://demo.fr", "username": "cpe", "password": 42, "uuid": "u"}',
            id="jeton du mauvais type",
        ),
    ],
)
def test_an_unusable_file_reads_as_no_account(store: Path, content: str) -> None:
    store.write_text(content, encoding="utf-8")

    assert load_credentials(store) is None


def test_a_missing_client_identifier_is_accepted(store: Path) -> None:
    """Il n'est délivré que par les comptes à sécurité renforcée."""
    store.write_text(
        json.dumps(
            {
                "pronote_url": "https://demo.fr",
                "username": "cpe",
                "password": "JETON",
                "uuid": "uuid-stable",
            }
        ),
        encoding="utf-8",
    )

    credentials = load_credentials(store)

    assert credentials is not None
    assert credentials.client_identifier is None


def test_forgetting_removes_the_file(store: Path) -> None:
    save_credentials(CREDENTIALS, store)

    forget_credentials(store)

    assert not store.exists()
    assert load_credentials(store) is None


def test_forgetting_a_missing_account_is_harmless(store: Path) -> None:
    forget_credentials(store)


def test_an_unwritable_location_does_not_raise(tmp_path: Path) -> None:
    """Un import réussi ne doit pas se solder par une erreur parce que le disque est plein."""
    blocking_file = tmp_path / "fichier"
    blocking_file.write_text("", encoding="utf-8")

    save_credentials(CREDENTIALS, blocking_file / "sous-dossier" / "credentials.json")


def test_the_store_lives_in_the_user_profile() -> None:
    """Jamais à côté de l'exécutable : il peut être sur une clé USB ou dans Program Files."""
    path = default_credentials_path()

    assert path.name == "pronote-credentials.json"
    assert path.parent.name == "auto-classes"
    assert path.is_absolute()


def test_each_installation_gets_its_own_uuid() -> None:
    assert new_uuid() != new_uuid()


def test_the_server_is_readable_for_display() -> None:
    assert CREDENTIALS.server == "0123456a.index-education.net"
