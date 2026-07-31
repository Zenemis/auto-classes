"""Connexion par QR code puis par jeton, sans serveur Pronote.

Le point sensible n'est pas la lecture des classes — elle est commune avec la connexion
par mot de passe — mais le jeton : Pronote en délivre un neuf à chaque connexion, et
c'est celui-là qu'il faut ressortir.
"""

import pytest

from auto_classes.pronote import (
    PronoteError,
    SavedCredentials,
    connect_with_qr_code,
    connect_with_token,
    parse_qr_payload,
)

QR_PAYLOAD = '{"jeton": "AABBCC", "login": "DDEEFF", "url": "https://demo.fr/pronote/viescolaire.html"}'

CREDENTIALS = SavedCredentials(
    pronote_url="https://demo.fr/pronote/mobile.viescolaire.html",
    username="cpe",
    password="ANCIEN_JETON",
    uuid="uuid-stable",
)


class FakeStudent:
    def __init__(self, full_name: str) -> None:
        self.full_name = full_name
        self.last_name = ""
        self.first_names = ""


class FakeStudentClass:
    def __init__(self, name: str, students: list[FakeStudent]) -> None:
        self.name = name
        self._students = students

    def students(self) -> list[FakeStudent]:
        return self._students


class FakeClient:
    """Client dont la connexion a renouvelé le jeton, comme le fait Pronote."""

    def __init__(self, *, token: str = "NOUVEAU_JETON", classes=None, logged_in: bool = True) -> None:
        self.classes = (
            classes if classes is not None else [FakeStudentClass("3A", [FakeStudent("MARTIN Sophie")])]
        )
        self.logged_in = logged_in
        self._token = token

    def export_credentials(self) -> dict:
        return {
            "pronote_url": "https://demo.fr/pronote/mobile.viescolaire.html",
            "username": "cpe",
            "password": self._token,
            "uuid": "uuid-stable",
            "client_identifier": "ABCDEF",
        }


# ------------------------------------------------------------- contenu du QR


def test_a_valid_payload_is_accepted() -> None:
    assert parse_qr_payload(QR_PAYLOAD)["jeton"] == "AABBCC"


def test_surrounding_whitespace_is_tolerated() -> None:
    """Un collage depuis un lecteur de QR code traîne souvent un retour à la ligne."""
    assert parse_qr_payload(f"\n  {QR_PAYLOAD}  \n")["login"] == "DDEEFF"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        pytest.param("", "Collez le contenu", id="vide"),
        pytest.param("pas du json", "pas un contenu de QR code", id="texte quelconque"),
        pytest.param('"une chaîne"', "pas un contenu de QR code", id="json qui n'est pas un objet"),
        pytest.param('{"jeton": "AA", "login": "BB"}', "url", id="url manquante"),
        pytest.param('{"login": "BB", "url": "https://demo.fr"}', "jeton", id="jeton manquant"),
    ],
)
def test_an_unusable_payload_says_what_is_expected(payload: str, expected: str) -> None:
    with pytest.raises(PronoteError, match=expected):
        parse_qr_payload(payload)


# ------------------------------------------------------------ première connexion


def test_the_qr_code_yields_a_roster_and_a_token() -> None:
    calls = []

    def factory(payload, pin, uuid):
        calls.append((payload, pin, uuid))
        return FakeClient()

    connection = connect_with_qr_code(QR_PAYLOAD, "1234", client_factory=factory)

    assert connection.roster.student_names == ["MARTIN Sophie"]
    assert connection.credentials.password == "NOUVEAU_JETON"
    assert connection.credentials.client_identifier == "ABCDEF"

    payload, pin, uuid = calls[0]
    assert (payload["jeton"], pin) == ("AABBCC", "1234")
    assert uuid, "un UUID stable doit être fourni à Pronote"


def test_the_four_digit_code_is_required() -> None:
    def factory(*args):
        raise AssertionError("aucune connexion ne doit être tentée")

    with pytest.raises(PronoteError, match="quatre chiffres"):
        connect_with_qr_code(QR_PAYLOAD, "   ", client_factory=factory)


class QRCodeDecryptError(Exception):
    """Homonyme de l'exception pronotepy levée sur un code de confirmation erroné."""


def test_a_wrong_confirmation_code_is_explained() -> None:
    def factory(*args):
        raise QRCodeDecryptError("invalid confirmation code")

    with pytest.raises(PronoteError, match="Code à quatre chiffres incorrect"):
        connect_with_qr_code(QR_PAYLOAD, "0000", client_factory=factory)


# ------------------------------------------------------------ reconnexions


def test_the_saved_token_is_sent_and_a_new_one_comes_back() -> None:
    calls = []

    def factory(credentials):
        calls.append(credentials)
        return FakeClient(token="JETON_SUIVANT")

    connection = connect_with_token(CREDENTIALS, client_factory=factory)

    assert calls == [CREDENTIALS]
    assert connection.credentials.password == "JETON_SUIVANT"
    assert connection.roster.student_names == ["MARTIN Sophie"]


def test_an_expired_token_tells_the_user_to_start_over() -> None:
    def factory(_credentials):
        return FakeClient(logged_in=False)

    with pytest.raises(PronoteError, match="Refaites un QR code"):
        connect_with_token(CREDENTIALS, client_factory=factory)


def test_an_account_without_classes_is_reported_rather_than_saved() -> None:
    """Un QR code fabriqué depuis l'espace Professeurs : la connexion passe, les classes manquent."""

    def factory(*args):
        return FakeClient(classes=[])

    with pytest.raises(PronoteError, match="Vie scolaire"):
        connect_with_qr_code(QR_PAYLOAD, "1234", client_factory=factory)
