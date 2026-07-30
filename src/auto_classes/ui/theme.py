"""Jetons de style de l'UI : couleurs, métriques, polices, glyphes.

Aucun widget ne doit contenir de littéral de couleur ou d'espacement : tout passe par
`Palette`, `Metrics`, `Fonts` et `Icons`, de sorte que l'apparence globale se retouche
depuis ce seul fichier.
"""

import sys

import customtkinter as ctk

Color = tuple[str, str]
"""Couleur CustomTkinter : (thème clair, thème sombre)."""


class Palette:
    """Gris neutres légèrement chauds, un vert pour l'action principale,
    et une couleur par type de contrainte."""

    WINDOW: Color = ("#F1F1EF", "#191918")
    SURFACE: Color = ("#FFFFFF", "#242423")
    SURFACE_ALT: Color = ("#E9E9E5", "#2C2C2B")
    SURFACE_SUNKEN: Color = ("#E5E5E1", "#1F1F1E")
    HOVER: Color = ("#E2E2DD", "#333332")
    BORDER: Color = ("#DBDBD5", "#383836")
    BORDER_STRONG: Color = ("#C2C2BA", "#4A4A47")

    TEXT: Color = ("#1D1D1B", "#ECECEA")
    TEXT_MUTED: Color = ("#6F6F68", "#9C9C95")
    TEXT_FAINT: Color = ("#9A9A92", "#71716B")
    TEXT_ON_ACCENT: Color = ("#FFFFFF", "#FFFFFF")

    PRIMARY: Color = ("#1B9E57", "#21A25E")
    PRIMARY_HOVER: Color = ("#17864A", "#1A8B50")

    SELECTION: Color = ("#5C6B8A", "#8497BE")
    SELECTION_BG: Color = ("#E9EBF1", "#2E323C")

    DANGER: Color = ("#C2483B", "#D8695A")
    DANGER_HOVER: Color = ("#A83A2F", "#C25546")

    TOGETHER: Color = ("#3C74C4", "#6C9BE0")
    APART: Color = ("#C2483B", "#D8695A")
    INCLUDE: Color = ("#2C8474", "#3FA592")
    EXCLUDE: Color = ("#B0731A", "#D2932F")


class Metrics:
    """Espacements, rayons et dimensions de référence."""

    PAD_XS = 4
    PAD_SM = 8
    PAD_MD = 12
    PAD_LG = 16
    PAD_XL = 24

    RADIUS_SM = 8
    RADIUS_MD = 12
    RADIUS_PILL = 11

    CONTROL_HEIGHT = 32
    ICON_BUTTON_SIZE = 30

    MENU_BAND_HEIGHT = 62
    CLASSES_BAND_HEIGHT = 232
    INSPECTOR_WIDTH = 336
    PROPOSAL_LIST_WIDTH = 232
    # Une carte de classe fixe sa hauteur : sans cela elle réclamerait la hauteur par
    # défaut d'un CTkFrame (200) et se ferait rogner dans la bande.
    CLASSROOM_CARD_WIDTH = 208
    CLASSROOM_CARD_HEIGHT = 132
    STUDENT_TILE_WIDTH = 216


class Fonts:
    """Fabrique de polices mise en cache.

    Une `CTkFont` a besoin d'une fenêtre racine Tk : n'appeler ces méthodes qu'après
    la construction de `App`.
    """

    FAMILY = "Segoe UI" if sys.platform == "win32" else None

    _cache: dict[tuple[int, str, str], ctk.CTkFont] = {}

    @classmethod
    def _font(cls, size: int, weight: str = "normal", slant: str = "roman") -> ctk.CTkFont:
        key = (size, weight, slant)
        if key not in cls._cache:
            kwargs: dict[str, object] = {"size": size, "weight": weight, "slant": slant}
            if cls.FAMILY is not None:
                kwargs["family"] = cls.FAMILY
            cls._cache[key] = ctk.CTkFont(**kwargs)
        return cls._cache[key]

    @classmethod
    def title(cls) -> ctk.CTkFont:
        return cls._font(19, "bold")

    @classmethod
    def heading(cls) -> ctk.CTkFont:
        return cls._font(14, "bold")

    @classmethod
    def body(cls) -> ctk.CTkFont:
        return cls._font(13)

    @classmethod
    def body_bold(cls) -> ctk.CTkFont:
        return cls._font(13, "bold")

    @classmethod
    def small(cls) -> ctk.CTkFont:
        return cls._font(11)

    @classmethod
    def small_bold(cls) -> ctk.CTkFont:
        return cls._font(11, "bold")

    @classmethod
    def italic(cls) -> ctk.CTkFont:
        return cls._font(12, slant="italic")

    @classmethod
    def icon(cls) -> ctk.CTkFont:
        return cls._font(15)


class Icons:
    """Glyphes Unicode rendus par les polices système (pas d'asset externe).

    Choisis parmi ceux que Segoe UI / Segoe UI Symbol dessinent proprement à petite
    taille : les pictogrammes pleins (☁, ✏) sortent en pâtés noirs, les emoji en
    couleur, et un glyphe absent s'affiche en carré vide.
    """

    IMPORT = "↧"
    PRONOTE = "⇄"
    GENERATE = "▶"
    ADD = "+"
    CLOSE = "✕"
    GEAR = "⚙"
    SEARCH = "⌕"
    DOT = "●"
    REFRESH = "↻"
