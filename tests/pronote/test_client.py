"""Lecture des listes d'élèves Pronote, sans serveur Pronote.

Aucun test ne se connecte : `fetch_roster` reçoit une fabrique de client factice. Ce qui
est vérifié ici, c'est ce que le module fait de ce que pronotepy lui rend — y compris
quand pronotepy lève.
"""

import pytest

from auto_classes.pronote import PronoteError, Roster, fetch_roster, normalize_url
from auto_classes.pronote.client import SPACE_PAGE, StudentClass


class FakeStudent:
    def __init__(self, full_name: str = "", last_name: str = "", first_names: str = "") -> None:
        self.full_name = full_name
        self.last_name = last_name
        self.first_names = first_names


class FakeStudentClass:
    def __init__(self, name: str, students: list[FakeStudent]) -> None:
        self.name = name
        self._students = students

    def students(self) -> list[FakeStudent]:
        return self._students


class FakeClient:
    def __init__(self, classes: list[FakeStudentClass], *, logged_in: bool = True) -> None:
        self.classes = classes
        self.logged_in = logged_in


def client_returning(*classes: FakeStudentClass, logged_in: bool = True):
    """Fabrique de client qui mémorise les arguments reçus, pour les inspecter ensuite."""

    def factory(url, username, password, ent):
        factory.call = (url, username, password, ent)
        return FakeClient(list(classes), logged_in=logged_in)

    factory.call = None
    return factory


def client_raising(error: Exception):
    def factory(url, username, password, ent):
        raise error

    return factory


# --------------------------------------------------------------------- adresse


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param(
            "https://0123456a.index-education.net/pronote/professeur.html",
            f"https://0123456a.index-education.net/pronote/{SPACE_PAGE}",
            id="espace professeurs corrigé",
        ),
        pytest.param(
            "https://0123456a.index-education.net/pronote/",
            f"https://0123456a.index-education.net/pronote/{SPACE_PAGE}",
            id="racine complétée",
        ),
        pytest.param(
            "0123456a.index-education.net/pronote/eleve.html",
            f"https://0123456a.index-education.net/pronote/{SPACE_PAGE}",
            id="schéma ajouté",
        ),
        pytest.param(
            f"https://demo.fr/pronote/{SPACE_PAGE}?login=true",
            f"https://demo.fr/pronote/{SPACE_PAGE}",
            id="paramètres retirés",
        ),
        pytest.param(
            "  https://demo.fr/pronote  ",
            f"https://demo.fr/pronote/{SPACE_PAGE}",
            id="espaces et page manquante",
        ),
    ],
)
def test_normalize_url_targets_the_vie_scolaire_space(raw: str, expected: str) -> None:
    assert normalize_url(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "https://"])
def test_normalize_url_rejects_what_it_cannot_read(raw: str) -> None:
    with pytest.raises(PronoteError):
        normalize_url(raw)


# ------------------------------------------------------------------ récupération


def test_fetch_roster_reads_every_class() -> None:
    factory = client_returning(
        FakeStudentClass("3A", [FakeStudent("MARTIN Léa"), FakeStudent("DUPONT Hugo")]),
        FakeStudentClass("3B", [FakeStudent("NGUYEN Kim")]),
    )

    roster = fetch_roster("demo.fr/pronote", "cpe", "secret", None, client_factory=factory)

    assert roster == Roster(
        classes=(
            StudentClass("3A", ("MARTIN Léa", "DUPONT Hugo")),
            StudentClass("3B", ("NGUYEN Kim",)),
        )
    )
    assert roster.student_names == ["MARTIN Léa", "DUPONT Hugo", "NGUYEN Kim"]


def test_fetch_roster_connects_to_the_normalized_address() -> None:
    factory = client_returning(FakeStudentClass("3A", [FakeStudent("MARTIN Léa")]))

    fetch_roster("demo.fr/pronote/professeur.html", "  cpe  ", "secret", None, client_factory=factory)

    url, username, password, ent = factory.call
    assert url == f"https://demo.fr/pronote/{SPACE_PAGE}"
    assert (username, password, ent) == ("cpe", "secret", None)


def test_a_student_in_two_classes_is_imported_once() -> None:
    """Un élève d'un groupe d'option apparaît dans deux listes ; la répartition n'en veut qu'une."""
    factory = client_returning(
        FakeStudentClass("3A", [FakeStudent("MARTIN Léa"), FakeStudent("DUPONT Hugo")]),
        FakeStudentClass("Latin", [FakeStudent("MARTIN Léa")]),
    )

    roster = fetch_roster("demo.fr/pronote", "cpe", "secret", None, client_factory=factory)

    assert roster.student_names == ["MARTIN Léa", "DUPONT Hugo"]


def test_student_name_falls_back_on_first_and_last_names() -> None:
    factory = client_returning(
        FakeStudentClass("3A", [FakeStudent(last_name="MARTIN", first_names="Léa")])
    )

    roster = fetch_roster("demo.fr/pronote", "cpe", "secret", None, client_factory=factory)

    assert roster.student_names == ["Léa MARTIN"]


@pytest.mark.parametrize(
    "missing",
    [pytest.param("username", id="identifiant"), pytest.param("password", id="mot de passe")],
)
def test_missing_credentials_are_refused_before_any_connection(missing: str) -> None:
    credentials = {"username": "cpe", "password": "secret", missing: ""}

    def factory(*args, **kwargs):
        raise AssertionError("aucune connexion ne doit être tentée")

    with pytest.raises(PronoteError):
        fetch_roster("demo.fr/pronote", client_factory=factory, **credentials)


# ---------------------------------------------------------------------- échecs


def test_account_without_class_access_is_named_as_such() -> None:
    """Le symptôme d'un compte Professeurs : la connexion passe, les classes manquent."""
    factory = client_returning()

    with pytest.raises(PronoteError, match="Vie scolaire"):
        fetch_roster("demo.fr/pronote", "prof", "secret", None, client_factory=factory)


def test_refused_login_without_exception_is_reported() -> None:
    factory = client_returning(FakeStudentClass("3A", []), logged_in=False)

    with pytest.raises(PronoteError, match="refusée"):
        fetch_roster("demo.fr/pronote", "cpe", "faux", None, client_factory=factory)


class CryptoError(Exception):
    """Homonyme de l'exception pronotepy levée sur mauvais mot de passe."""


class ENTLoginError(Exception):
    pass


class MFAError(Exception):
    pass


class ParsingError(Exception):
    pass


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        pytest.param(CryptoError("bad password"), "mot de passe", id="identifiants"),
        pytest.param(ENTLoginError("ent"), "ENT", id="ent"),
        pytest.param(MFAError("pin"), "deux facteurs", id="2fa"),
        pytest.param(ConnectionError("down"), "injoignable", id="réseau"),
        pytest.param(KeyError("listeClasses"), "Vie scolaire", id="espace sans classes"),
        pytest.param(ParsingError("bad json"), "Réponse inattendue", id="json"),
    ],
)
def test_library_failures_become_actionable_messages(error: Exception, expected: str) -> None:
    with pytest.raises(PronoteError, match=expected):
        fetch_roster("demo.fr/pronote", "cpe", "secret", None, client_factory=client_raising(error))


def test_unknown_failure_keeps_the_original_message() -> None:
    factory = client_raising(RuntimeError("quelque chose d'inédit"))

    with pytest.raises(PronoteError, match="quelque chose d'inédit"):
        fetch_roster("demo.fr/pronote", "cpe", "secret", None, client_factory=factory)


def test_failures_keep_the_original_exception_as_cause() -> None:
    """La cause reste attachée : sans elle, un incident réseau serait indébogable."""
    original = ConnectionError("down")

    with pytest.raises(PronoteError) as caught:
        fetch_roster("demo.fr/pronote", "cpe", "secret", None, client_factory=client_raising(original))

    assert caught.value.__cause__ is original
