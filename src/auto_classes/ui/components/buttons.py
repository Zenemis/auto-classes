"""Boutons dérivés de `CTkButton`, préréglés sur la palette de l'application.

Chaque style pose ses valeurs via `setdefault` : un appelant peut donc surcharger
n'importe quelle option (hauteur, police, couleur) sans se heurter à un argument
déjà fourni.
"""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.theme import Color, Fonts, Metrics, Palette, readable_on


def _label(text: str, icon: str | None) -> str:
    return f"{icon}  {text}" if icon else text


class GhostButton(ctk.CTkButton):
    """Bouton secondaire : surface claire, bordure fine. Le cas par défaut."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command: Callable[[], None] | None = None,
        *,
        icon: str | None = None,
        **kwargs: object,
    ) -> None:
        kwargs.setdefault("width", 0)
        kwargs.setdefault("height", Metrics.CONTROL_HEIGHT)
        kwargs.setdefault("corner_radius", Metrics.RADIUS_SM)
        kwargs.setdefault("fg_color", Palette.SURFACE)
        kwargs.setdefault("hover_color", Palette.HOVER)
        kwargs.setdefault("text_color", Palette.TEXT)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Palette.BORDER)
        kwargs.setdefault("font", Fonts.body())
        super().__init__(master, text=_label(text, icon), command=command, **kwargs)


class PrimaryButton(ctk.CTkButton):
    """Action principale : le vert de « Générer »."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command: Callable[[], None] | None = None,
        *,
        icon: str | None = None,
        **kwargs: object,
    ) -> None:
        kwargs.setdefault("width", 0)
        kwargs.setdefault("height", Metrics.CONTROL_HEIGHT)
        kwargs.setdefault("corner_radius", Metrics.RADIUS_SM)
        kwargs.setdefault("fg_color", Palette.PRIMARY)
        kwargs.setdefault("hover_color", Palette.PRIMARY_HOVER)
        kwargs.setdefault("text_color", Palette.TEXT_ON_ACCENT)
        kwargs.setdefault("font", Fonts.body_bold())
        super().__init__(master, text=_label(text, icon), command=command, **kwargs)


class DangerButton(ctk.CTkButton):
    """Suppression : texte rouge sur fond transparent, cadré au survol."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command: Callable[[], None] | None = None,
        **kwargs: object,
    ) -> None:
        kwargs.setdefault("width", 0)
        kwargs.setdefault("height", Metrics.CONTROL_HEIGHT)
        kwargs.setdefault("corner_radius", Metrics.RADIUS_SM)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", Palette.HOVER)
        kwargs.setdefault("text_color", Palette.DANGER)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Palette.BORDER)
        kwargs.setdefault("font", Fonts.body())
        super().__init__(master, text=text, command=command, **kwargs)


class IconButton(ctk.CTkButton):
    """Bouton carré ne portant qu'un glyphe (« + », « ✕ », « ⚙ »…)."""

    def __init__(
        self,
        master: tk.Misc,
        icon: str,
        command: Callable[[], None] | None = None,
        *,
        size: int = Metrics.ICON_BUTTON_SIZE,
        **kwargs: object,
    ) -> None:
        kwargs.setdefault("width", size)
        kwargs.setdefault("height", size)
        kwargs.setdefault("corner_radius", Metrics.RADIUS_SM)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", Palette.HOVER)
        kwargs.setdefault("text_color", Palette.TEXT_MUTED)
        kwargs.setdefault("font", Fonts.icon())
        kwargs.setdefault("cursor", "hand2")
        super().__init__(master, text=icon, command=command, **kwargs)


class ToolButton(ctk.CTkButton):
    """Bouton bistable de l'inspecteur : prend la couleur de son outil une fois armé."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        accent: Color,
        command: Callable[[], None] | None = None,
        **kwargs: object,
    ) -> None:
        kwargs.setdefault("width", 0)
        kwargs.setdefault("height", Metrics.CONTROL_HEIGHT)
        kwargs.setdefault("corner_radius", Metrics.RADIUS_SM)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("font", Fonts.small_bold())
        super().__init__(master, text=text, command=command, **kwargs)

        self._accent = accent
        self._active = False
        self._apply_style()

    def set_active(self, active: bool) -> None:
        if active != self._active:
            self._active = active
            self._apply_style()

    def _apply_style(self) -> None:
        if self._active:
            self.configure(
                fg_color=self._accent,
                hover_color=self._accent,
                text_color=readable_on(self._accent),
                border_color=self._accent,
            )
        else:
            self.configure(
                fg_color=Palette.SURFACE_ALT,
                hover_color=Palette.HOVER,
                text_color=Palette.TEXT,
                border_color=Palette.BORDER,
            )
