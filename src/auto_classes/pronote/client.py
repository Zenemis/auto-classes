"""Connexion à Pronote et lecture des listes d'élèves, via pronotepy.

## Quel espace Pronote ?

pronotepy ne gère que les espaces Élève, Parent et — partiellement — Vie scolaire.
**L'espace Professeurs n'est pas supporté** : Index Éducation n'y expose pas la même API,
et rien dans pronotepy ne sait s'y connecter. Or c'est justement l'espace Vie scolaire
qui publie `listeClasses`, la liste des classes de l'établissement avec leurs élèves.

Conséquence pratique, à connaître avant de lire la suite : un enseignant ne peut pas
importer ses élèves avec son compte professeur. Il lui faut un compte **Vie scolaire**,
que l'établissement délivre (souvent au CPE ou au secrétariat). Le code ne peut pas
contourner ça ; il se contente de le diagnostiquer et de le dire clairement, plutôt que
de laisser remonter une `KeyError` sur du JSON.

## Adresse du serveur

L'URL saisie est réécrite vers `viescolaire.html` : un enseignant a sous la main
l'adresse de *son* espace (`professeur.html`), voire la racine `/pronote/`. Corriger la
page à sa place évite un échec dont la cause serait invisible.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

from auto_classes.pronote.credentials import SavedCredentials, new_uuid
from auto_classes.pronote.errors import PronoteError

# Page de connexion de l'espace Vie scolaire, le seul qui expose les listes de classes.
SPACE_PAGE = "viescolaire.html"

ENT_NONE = "Aucun (identifiants Pronote)"


@dataclass(frozen=True)
class StudentClass:
    """Une classe de l'établissement et les élèves qui y sont inscrits."""

    name: str
    students: tuple[str, ...]


@dataclass(frozen=True)
class Roster:
    """Ce que l'établissement expose au compte connecté."""

    classes: tuple[StudentClass, ...]

    @property
    def student_names(self) -> list[str]:
        """Tous les élèves, sans doublon, dans l'ordre des classes.

        Un élève peut apparaître dans deux classes (un groupe d'option, par exemple) :
        le dédoublonnage évite de le proposer deux fois à la répartition.
        """
        seen: dict[str, None] = {}
        for student_class in self.classes:
            for name in student_class.students:
                seen.setdefault(name, None)
        return list(seen)

    @property
    def is_empty(self) -> bool:
        return not self.student_names


def normalize_url(raw: str) -> str:
    """Adresse de connexion à l'espace Vie scolaire, déduite de ce qui a été saisi.

    Accepte la racine (`.../pronote/`), une page d'espace quelconque
    (`.../pronote/professeur.html`) ou l'adresse complète, avec ou sans schéma.
    """
    address = raw.strip()
    if not address:
        raise PronoteError("Renseignez l'adresse Pronote de l'établissement.")

    # Sans schéma, `urlparse` prend l'hôte pour un chemin : on impose https, que tous
    # les serveurs Pronote exigent de toute façon.
    if "//" not in address:
        address = f"https://{address}"

    parsed = urlparse(address)
    if not parsed.netloc:
        raise PronoteError(f"Adresse Pronote incompréhensible : « {raw.strip()} »")

    segments = [segment for segment in parsed.path.split("/") if segment]
    if segments and segments[-1].endswith(".html"):
        segments[-1] = SPACE_PAGE
    else:
        segments.append(SPACE_PAGE)

    # Requête et fragment sont retirés : pronotepy ajoute lui-même `?login=true`, et un
    # `?login=true` déjà présent dans une adresse copiée depuis le navigateur le gênerait.
    return urlunparse((parsed.scheme, parsed.netloc, "/" + "/".join(segments), "", "", ""))


def available_ents() -> dict[str, Callable[..., Any]]:
    """ENT reconnus par pronotepy, indexés par un libellé lisible.

    La liste est lue dans le module `pronotepy.ent` plutôt que recopiée : elle bouge à
    chaque version de la bibliothèque, et une copie périmée ferait échouer des connexions
    parfaitement valides.
    """
    try:
        from pronotepy import ent
    except ImportError:
        return {}

    functions = {
        name.replace("_", " "): getattr(ent, name)
        for name in dir(ent)
        if not name.startswith("_") and callable(getattr(ent, name))
    }
    return dict(sorted(functions.items()))


def _default_client_factory(*args: Any, **kwargs: Any) -> Any:
    return _pronotepy().VieScolaireClient(*args, **kwargs)


def fetch_roster(
    url: str,
    username: str,
    password: str,
    ent: Callable[..., Any] | None = None,
    *,
    client_factory: Callable[..., Any] = _default_client_factory,
) -> Roster:
    """Se connecte à l'espace Vie scolaire et lit toutes les classes accessibles.

    `client_factory` n'existe que pour les tests : ils injectent un faux client plutôt
    que d'appeler un vrai serveur Pronote.
    """
    if not username.strip():
        raise PronoteError("Renseignez votre identifiant Pronote.")
    if not password:
        raise PronoteError("Renseignez votre mot de passe Pronote.")

    address = normalize_url(url)

    try:
        client = client_factory(address, username.strip(), password, ent)
    except PronoteError:
        raise
    except Exception as error:
        raise PronoteError(_diagnose(error)) from error

    # `logged_in` à False sans exception : pronotepy a mené l'échange jusqu'au bout mais
    # le serveur n'a pas délivré de clé de session.
    if not getattr(client, "logged_in", True):
        raise PronoteError(
            "Connexion refusée par Pronote. Vérifiez l'identifiant, le mot de passe et l'ENT."
        )

    try:
        classes = tuple(_read_classes(client))
    except PronoteError:
        raise
    except Exception as error:
        raise PronoteError(_diagnose(error)) from error

    roster = Roster(classes=classes)
    if roster.is_empty:
        raise PronoteError(NO_CLASS_ACCESS)
    return roster


@dataclass(frozen=True)
class Connection:
    """Une connexion par jeton : les classes lues, et le jeton à réécrire.

    Les deux vont ensemble parce que PRONOTE renouvelle le jeton pendant la connexion :
    séparer la lecture des classes de la récupération du nouveau jeton laisserait la
    porte ouverte à un import réussi suivi d'un jeton perdu.
    """

    roster: Roster
    credentials: SavedCredentials


def parse_qr_payload(text: str) -> dict[str, str]:
    """Contenu d'un QR code PRONOTE, tel qu'il est collé depuis un lecteur de QR code.

    C'est du JSON, mais collé à la main : il traîne régulièrement des guillemets typo­
    graphiques ou des retours à la ligne. Seule la structure est vérifiée ici — les trois
    clés dont `pronotepy` a besoin.
    """
    raw = text.strip()
    if not raw:
        raise PronoteError("Collez le contenu du QR code affiché par PRONOTE.")

    try:
        payload = json.loads(raw)
    except ValueError as error:
        raise PronoteError(
            "Ce n'est pas un contenu de QR code PRONOTE.\n\n"
            "Attendu : le texte lu dans le QR code, de la forme "
            '{"jeton": "…", "login": "…", "url": "…"}.'
        ) from error

    if not isinstance(payload, dict):
        raise PronoteError("Ce n'est pas un contenu de QR code PRONOTE.")

    missing = [key for key in ("jeton", "login", "url") if not payload.get(key)]
    if missing:
        raise PronoteError(
            f"Contenu de QR code incomplet : il manque {', '.join(missing)}.\n\n"
            "Recopiez la totalité du texte lu dans le QR code."
        )
    return {key: str(value) for key, value in payload.items()}


def connect_with_qr_code(
    qr_payload: str,
    pin: str,
    *,
    client_factory: Callable[..., Any] | None = None,
) -> Connection:
    """Première connexion par QR code : échange le QR contre un jeton réutilisable.

    Le QR code porte l'adresse du serveur — l'utilisateur n'a donc rien à saisir d'autre
    que le code à quatre chiffres choisi dans PRONOTE au moment de l'afficher. C'est
    aussi ce qui rend ce chemin insensible à l'ENT : il n'y a plus de portail à franchir.
    """
    payload = parse_qr_payload(qr_payload)
    code = pin.strip()
    if not code:
        raise PronoteError("Renseignez le code à quatre chiffres choisi dans PRONOTE.")

    factory = client_factory or _qr_code_client_factory
    client = _connect(lambda: factory(payload, code, new_uuid()))
    return _connection_from(client)


def connect_with_token(
    credentials: SavedCredentials,
    *,
    client_factory: Callable[..., Any] | None = None,
) -> Connection:
    """Reconnexion silencieuse avec le jeton enregistré au précédent import."""
    factory = client_factory or _token_client_factory
    client = _connect(lambda: factory(credentials))
    return _connection_from(client)


def _connect(login: Callable[[], Any]) -> Any:
    try:
        client = login()
    except PronoteError:
        raise
    except Exception as error:
        raise PronoteError(_diagnose(error)) from error

    if not getattr(client, "logged_in", True):
        raise PronoteError(EXPIRED_TOKEN)
    return client


def _connection_from(client: Any) -> Connection:
    """Classes lues et jeton renouvelé, dans cet ordre : le jeton n'a de valeur que si
    la lecture a abouti."""
    try:
        classes = tuple(_read_classes(client))
    except PronoteError:
        raise
    except Exception as error:
        raise PronoteError(_diagnose(error)) from error

    roster = Roster(classes=classes)
    if roster.is_empty:
        raise PronoteError(NO_CLASS_ACCESS)

    exported = client.export_credentials()
    return Connection(
        roster=roster,
        credentials=SavedCredentials(
            pronote_url=str(exported["pronote_url"]),
            username=str(exported["username"]),
            password=str(exported["password"]),
            uuid=str(exported["uuid"]),
            client_identifier=exported.get("client_identifier"),
        ),
    )


def _qr_code_client_factory(payload: dict[str, str], pin: str, uuid: str) -> Any:
    return _pronotepy().VieScolaireClient.qrcode_login(payload, pin, uuid)


def _token_client_factory(credentials: SavedCredentials) -> Any:
    return _pronotepy().VieScolaireClient.token_login(
        credentials.pronote_url,
        credentials.username,
        credentials.password,
        credentials.uuid,
        client_identifier=credentials.client_identifier,
    )


def _pronotepy() -> Any:
    try:
        import pronotepy
    except ImportError as error:  # paquet absent d'une installation bricolée
        raise PronoteError(
            "La bibliothèque pronotepy n'est pas installée : la connexion Pronote est indisponible."
        ) from error
    return pronotepy


def _read_classes(client: Any) -> Iterable[StudentClass]:
    for student_class in getattr(client, "classes", []):
        students = tuple(_student_name(student) for student in student_class.students())
        yield StudentClass(name=str(student_class.name), students=students)


def _student_name(student: Any) -> str:
    """Nom affichable d'un élève, quel que soit ce que Pronote a renseigné.

    `full_name` est le champ normal ; il arrive qu'il soit vide alors que le nom et les
    prénoms sont là, d'où la reconstitution.
    """
    full_name = str(getattr(student, "full_name", "") or "").strip()
    if full_name:
        return full_name
    parts = [
        str(getattr(student, "first_names", "") or "").strip(),
        str(getattr(student, "last_name", "") or "").strip(),
    ]
    return " ".join(part for part in parts if part) or "Élève sans nom"


EXPIRED_TOKEN = (
    "Le compte enregistré n'est plus reconnu par Pronote.\n\n"
    "PRONOTE renouvelle le jeton à chaque connexion et l'invalide au bout d'un certain "
    "temps sans usage. Refaites un QR code depuis Pronote pour réenregistrer le compte."
)

NO_CLASS_ACCESS = (
    "Ce compte ne donne accès à aucune liste de classe.\n\n"
    "L'import passe par l'espace Vie scolaire : c'est le seul que Pronote ouvre aux "
    "outils externes avec les listes d'élèves de l'établissement. Un compte Professeurs "
    "ne convient pas — demandez un accès Vie scolaire à votre établissement."
)

# Diagnostic par nom de type plutôt que par `isinstance` : pronotepy n'est chargé que
# lorsqu'une connexion est tentée (l'application doit démarrer sans lui), et les tests
# lèvent des exceptions homonymes sans dépendre de la bibliothèque.
_DIAGNOSTICS: tuple[tuple[str, str], ...] = (
    (
        # Sous-classe de `CryptoError`, donc placée avant elle : c'est le déchiffrement
        # du QR code qui a échoué, pas une authentification par mot de passe.
        "QRCodeDecryptError",
        "Code à quatre chiffres incorrect, ou QR code expiré.\n\n"
        "Un QR code PRONOTE n'est valable que dix minutes : affichez-en un nouveau et "
        "recollez son contenu.",
    ),
    (
        "CryptoError",
        "Identifiant ou mot de passe refusé par Pronote.",
    ),
    (
        "ENTLoginError",
        "Échec de la connexion via l'ENT. Vérifiez l'ENT choisi et vos identifiants ENT "
        "(ce ne sont pas toujours ceux de Pronote).",
    ),
    (
        "MFAError",
        "Ce compte est protégé par une validation à deux facteurs, que l'application ne "
        "sait pas franchir. Connectez-vous une fois depuis un navigateur, ou utilisez un "
        "compte sans code PIN.",
    ),
    (
        "SSLError",
        "Certificat du serveur Pronote refusé. Vérifiez l'adresse saisie.",
    ),
    (
        "ConnectionError",
        "Serveur Pronote injoignable. Vérifiez l'adresse et votre connexion internet.",
    ),
    (
        "Timeout",
        "Le serveur Pronote n'a pas répondu à temps. Réessayez dans un instant.",
    ),
    (
        "KeyError",
        NO_CLASS_ACCESS,
    ),
    (
        "ParsingError",
        "Réponse inattendue du serveur Pronote. L'établissement utilise peut-être une "
        "version de Pronote que la bibliothèque ne gère pas encore.",
    ),
)


def _diagnose(error: Exception) -> str:
    """Message utilisateur déduit du type de l'exception remontée par pronotepy."""
    type_names = {base.__name__ for base in type(error).__mro__}
    for name, message in _DIAGNOSTICS:
        if name in type_names:
            return message

    detail = str(error).strip()
    suffix = f"\n\n{type(error).__name__} : {detail}" if detail else ""
    return f"La connexion à Pronote a échoué.{suffix}"
