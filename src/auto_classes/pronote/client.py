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

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

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
    try:
        import pronotepy
    except ImportError as error:  # paquet absent d'une installation bricolée
        raise PronoteError(
            "La bibliothèque pronotepy n'est pas installée : la connexion Pronote est indisponible."
        ) from error
    return pronotepy.VieScolaireClient(*args, **kwargs)


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
