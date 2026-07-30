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
    """Gris froids, le vert-canard de Pronote pour l'action principale,
    et une couleur par type de contrainte.

    Les deux teintes de marque sont relevées sur `assets/pronote-icon.png` :
    vert-canard `#018673` et jaune `#FECD06`.
    """

    BRAND: Color = ("#018673", "#018673")
    BRAND_YELLOW: Color = ("#FECD06", "#FECD06")

    WINDOW: Color = ("#EFF1F3", "#171A1B")
    SURFACE: Color = ("#FFFFFF", "#212527")
    SURFACE_ALT: Color = ("#E7EBEE", "#282D2F")
    SURFACE_SUNKEN: Color = ("#E1E6EA", "#1C2021")
    HOVER: Color = ("#DEE4E9", "#2F3538")
    BORDER: Color = ("#D6DDE2", "#343A3D")
    BORDER_STRONG: Color = ("#B8C3CA", "#464D51")

    TEXT: Color = ("#1B2124", "#E9ECED")
    TEXT_MUTED: Color = ("#636E77", "#98A2A8")
    TEXT_FAINT: Color = ("#909DA6", "#6D767B")
    TEXT_ON_ACCENT: Color = ("#FFFFFF", "#FFFFFF")

    PRIMARY: Color = ("#018673", "#0A9C87")
    PRIMARY_HOVER: Color = ("#016B5C", "#018673")

    SELECTION: Color = ("#2E7D8F", "#57A5B4")
    SELECTION_BG: Color = ("#E1EDF1", "#22333A")

    DANGER: Color = ("#C2483B", "#D8695A")
    DANGER_HOVER: Color = ("#A83A2F", "#C25546")

    TOGETHER: Color = ("#2C6FB5", "#6199DE")
    APART: Color = ("#C2483B", "#D8695A")
    # Volontairement pas vert : la couleur « inclus » ne doit pas se confondre avec le
    # vert-canard de l'action principale, notamment sur les pastilles d'option.
    INCLUDE: Color = ("#6152B5", "#9186DC")
    EXCLUDE: Color = ("#B0731A", "#D2932F")


class Metrics:
    """Espacements, rayons et dimensions de référence."""

    PAD_XS = 4
    PAD_SM = 8
    PAD_MD = 12
    PAD_LG = 16
    PAD_XL = 24

    RADIUS_SM = 10
    RADIUS_MD = 14
    RADIUS_PILL = 12

    CONTROL_HEIGHT = 32
    ICON_BUTTON_SIZE = 30

    MENU_BAND_HEIGHT = 62
    CLASSES_BAND_HEIGHT = 232
    # La bande s'agrandit le temps d'une édition : réserver en permanence la hauteur du
    # formulaire laisserait une large bande vide le reste du temps.
    CLASSES_BAND_EDITING_HEIGHT = 324
    INSPECTOR_WIDTH = 336
    PROPOSAL_LIST_WIDTH = 232
    # Une carte de classe fixe sa hauteur : sans cela elle réclamerait la hauteur par
    # défaut d'un CTkFrame (200) et se ferait rogner dans la bande.
    CLASSROOM_CARD_WIDTH = 208
    CLASSROOM_CARD_HEIGHT = 132
    # L'éditeur remplace la carte sur place : plus large et plus haut, pour loger le
    # formulaire (nom, effectif, options, suppression).
    CLASSROOM_EDITOR_WIDTH = 430
    CLASSROOM_EDITOR_HEIGHT = 228
    # Tuiles d'élève étroites : une classe entière (100 élèves et plus) doit tenir à
    # l'écran sans défilement interminable. Hauteur fixée pour une grille régulière.
    STUDENT_TILE_WIDTH = 108
    STUDENT_TILE_HEIGHT = 54


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

    # Importer et Pronote portent de vraies images (cf. `ui.assets`), pas des glyphes.
    GENERATE = "▶"
    ADD = "+"
    CLOSE = "✕"
    GEAR = "⚙"
    SEARCH = "⌕"
    DOT = "●"
    REFRESH = "↻"
