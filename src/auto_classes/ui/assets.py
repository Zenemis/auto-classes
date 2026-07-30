"""Chargement des images de `ui/assets/`.

Les PNG sont mis en cache sous forme d'images Pillow (indépendantes de Tk), mais une
`CTkImage` neuve est construite à chaque appel : une `CTkImage` fabrique ses
`PhotoImage` pour le compte d'une racine Tk précise, en recycler une entre deux
fenêtres la lierait à une racine détruite.
"""

from functools import lru_cache
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageColor

from auto_classes.ui.theme import Color

ASSETS_DIR = Path(__file__).parent / "assets"

IMPORT_ICON = "import-icon.png"
PRONOTE_ICON = "pronote-icon.png"


@lru_cache(maxsize=None)
def _load(name: str) -> Image.Image:
    path = ASSETS_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Image absente du paquet : {path}")
    return Image.open(path).convert("RGBA")


@lru_cache(maxsize=None)
def _recolored(name: str, color: str) -> Image.Image:
    """Remplace les pixels par `color` en conservant la transparence.

    `import-icon.png` est un pictogramme quasi noir : il faut le reteindre pour qu'il
    reste lisible sur fond sombre.
    """
    source = _load(name)
    red, green, blue = ImageColor.getrgb(color)
    tinted = Image.new("RGBA", source.size, (red, green, blue, 255))
    tinted.putalpha(source.getchannel("A"))
    return tinted


def icon(name: str, *, size: int, tint: Color | None = None) -> ctk.CTkImage:
    """Image carrée de `size` points, déclinée pour les thèmes clair et sombre.

    `tint` reteint le pictogramme avec la couleur du thème courant ; sans lui, l'image
    est utilisée telle quelle (cas d'un logo, qui garde ses propres couleurs).
    """
    if tint is None:
        light = dark = _load(name)
    else:
        light, dark = _recolored(name, tint[0]), _recolored(name, tint[1])
    return ctk.CTkImage(light_image=light, dark_image=dark, size=(size, size))
