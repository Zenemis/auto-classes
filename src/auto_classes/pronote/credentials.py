"""Conservation des identifiants de connexion par jeton, entre deux lancements.

C'est la seule chose que l'application écrive sur le disque, et ce n'est pas un choix de
confort : **PRONOTE régénère le jeton à chaque connexion**. Un jeton qu'on ne réécrit
pas est un jeton mort au lancement suivant, et l'utilisateur devrait refaire un QR code
à chaque import.

Ce qui est enregistré (l'URL, l'identifiant, le jeton, l'UUID de l'application) vaut un
mot de passe : cela ouvre l'accès aux listes d'élèves de l'établissement. Le fichier vit
donc dans le profil de l'utilisateur (`%LOCALAPPDATA%`), lisible par lui seul sur une
machine correctement configurée — mais **en clair**. Sur un poste partagé sous un compte
commun, c'est insuffisant : d'où le bouton « Oublier ce compte » dans l'interface, et
`forget_credentials` ici.
"""

from __future__ import annotations

import json
import os
import uuid as uuid_module
from dataclasses import asdict, dataclass
from pathlib import Path

APPLICATION_DIRECTORY = "auto-classes"
CREDENTIALS_FILE = "pronote-credentials.json"


@dataclass(frozen=True)
class SavedCredentials:
    """Ce qu'il faut pour se reconnecter sans mot de passe.

    Les noms des champs sont ceux de `pronotepy` (`ClientBase.export_credentials`), pour
    que le passage de l'un à l'autre reste littéral.
    """

    pronote_url: str
    username: str
    password: str  # jeton, renouvelé par PRONOTE à chaque connexion
    uuid: str
    client_identifier: str | None = None

    @property
    def server(self) -> str:
        """Hôte du serveur, pour rappeler à l'utilisateur quel compte est enregistré."""
        without_scheme = self.pronote_url.split("//", 1)[-1]
        return without_scheme.split("/", 1)[0]


def default_credentials_path() -> Path:
    """Emplacement du fichier : le profil de l'utilisateur, jamais le dossier du programme.

    L'exécutable peut vivre sur une clé USB ou dans `Program Files`, où l'écriture est
    refusée ou visible par tous.
    """
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME")
    root = Path(base) if base else Path.home() / ".local" / "state"
    return root / APPLICATION_DIRECTORY / CREDENTIALS_FILE


def new_uuid() -> str:
    """Identifiant de cette installation, exigé stable d'une connexion à l'autre.

    PRONOTE s'en sert pour reconnaître l'appareil ; il est généré une fois, à
    l'enregistrement du QR code, puis relu avec le reste.
    """
    return uuid_module.uuid4().hex


def load_credentials(path: Path | None = None) -> SavedCredentials | None:
    """Identifiants enregistrés, ou None s'il n'y en a pas d'exploitables.

    Un fichier absent, tronqué, écrit par une version antérieure ou trafiqué à la main
    rend None : il n'y a rien à signaler à l'utilisateur, seulement un compte à
    reconfigurer.
    """
    target = path or default_credentials_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    if not isinstance(payload, dict):
        return None

    required = ("pronote_url", "username", "password", "uuid")
    if not all(isinstance(payload.get(key), str) and payload[key] for key in required):
        return None

    identifier = payload.get("client_identifier")
    return SavedCredentials(
        pronote_url=payload["pronote_url"],
        username=payload["username"],
        password=payload["password"],
        uuid=payload["uuid"],
        client_identifier=identifier if isinstance(identifier, str) else None,
    )


def save_credentials(credentials: SavedCredentials, path: Path | None = None) -> None:
    """Réécrit le fichier. Silencieux en cas d'échec d'écriture.

    Un disque plein ou un dossier en lecture seule ne doit pas faire perdre un import
    déjà réussi : l'utilisateur devra refaire un QR code au prochain lancement, ce qui
    est un moindre mal comparé à une erreur en pleine figure après une connexion réussie.
    """
    target = path or default_credentials_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        # `0o600` n'a d'effet réel que hors de Windows, où c'est l'emplacement dans le
        # profil de l'utilisateur qui protège le fichier. Le poser coûte une ligne et
        # rend le fichier correct partout ailleurs.
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(asdict(credentials), file, indent=2)
    except OSError:
        return


def forget_credentials(path: Path | None = None) -> None:
    """Efface le compte enregistré. Sans effet s'il n'y en a pas."""
    target = path or default_credentials_path()
    try:
        target.unlink(missing_ok=True)
    except OSError:
        return
