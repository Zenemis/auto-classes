"""Surfaces de base : bandes, en-têtes de section, cartes cliquables, état vide."""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components.bindings import (
    bind_recursive,
    contains_widget,
    set_cursor_recursive,
)
from auto_classes.ui.theme import Color, Fonts, Metrics, Palette


class Group(ctk.CTkFrame):
    """Conteneur transparent sans taille propre.

    Un `CTkFrame` demande 200×200 par défaut. Tant qu'il a des enfants, la propagation
    de géométrie remplace cette demande par la taille du contenu — mais un conteneur
    momentanément vide (une zone d'actions sans bouton, une liste de tags vide) garderait
    200×200 et disloquerait la mise en page de son parent. Tout regroupement purement
    structurel passe donc par cette classe.
    """

    def __init__(self, master: tk.Misc, **kwargs: object) -> None:
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("width", 0)
        kwargs.setdefault("height", 0)
        super().__init__(master, **kwargs)


class Panel(ctk.CTkFrame):
    """Bloc de surface bordé : base des trois bandes de l'onglet Configuration."""

    def __init__(self, master: tk.Misc, **kwargs: object) -> None:
        kwargs.setdefault("fg_color", Palette.SURFACE)
        kwargs.setdefault("corner_radius", Metrics.RADIUS_MD)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Palette.BORDER)
        super().__init__(master, **kwargs)


class ScrollArea(ctk.CTkScrollableFrame):
    """Zone défilante au style de l'application.

    CustomTkinter garde la barre de défilement visible même quand tout le contenu tient
    à l'écran : rail transparent et curseur au ton de la bordure, pour qu'elle se lise
    comme un liseré plutôt que comme un bandeau gris.
    """

    def __init__(self, master: tk.Misc, **kwargs: object) -> None:
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("scrollbar_fg_color", "transparent")
        kwargs.setdefault("scrollbar_button_color", Palette.BORDER)
        kwargs.setdefault("scrollbar_button_hover_color", Palette.BORDER_STRONG)
        super().__init__(master, **kwargs)


class SectionHeader(Group):
    """Ligne de titre d'une bande : libellé, précision, et zone d'actions à droite.

    Les boutons sont ajoutés par l'appelant dans `self.actions`.
    """

    def __init__(self, master: tk.Misc, title: str, detail: str = "") -> None:
        super().__init__(master)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text=title.upper(),
            font=Fonts.small_bold(),
            text_color=Palette.TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w")

        self._detail = ctk.CTkLabel(
            self, text=detail, font=Fonts.small(), text_color=Palette.TEXT_FAINT, anchor="w"
        )
        self._detail.grid(row=0, column=1, sticky="w", padx=(Metrics.PAD_SM, 0))

        self.actions = Group(self)
        self.actions.grid(row=0, column=2, sticky="e")

    def set_detail(self, detail: str) -> None:
        self._detail.configure(text=detail)


class ClickableCard(ctk.CTkFrame):
    """Carte réagissant au survol, au clic et à la sélection.

    Les sous-classes construisent leur contenu puis appellent `activate()` : les
    bindings sont propagés à toute la descendance créée entre-temps.
    """

    def __init__(
        self,
        master: tk.Misc,
        on_click: Callable[[], None] | None = None,
        *,
        base_color: Color = Palette.SURFACE,
        hover_color: Color = Palette.HOVER,
        selected_color: Color = Palette.SELECTION_BG,
        border_color: Color = Palette.BORDER,
        selected_border_color: Color = Palette.SELECTION,
        **kwargs: object,
    ) -> None:
        kwargs.setdefault("corner_radius", Metrics.RADIUS_SM)
        super().__init__(master, fg_color=base_color, border_width=1, border_color=border_color, **kwargs)

        self._on_click = on_click
        self._base_color = base_color
        self._hover_color = hover_color
        self._selected_color = selected_color
        self._border_color = border_color
        self._selected_border_color = selected_border_color

        self._hovered = False
        self._selected = False
        self._accent: Color | None = None

    def activate(self, target: tk.Misc | None = None) -> None:
        """Propage les bindings sur `target` (la carte entière par défaut).

        À rappeler avec le sous-arbre concerné après avoir reconstruit une partie du
        contenu — les bindings s'ajoutent (`add="+"`), les repasser sur toute la carte
        empilerait plusieurs fois le même gestionnaire.
        """
        subtree = self if target is None else target
        bind_recursive(subtree, "<Button-1>", self._on_press)
        bind_recursive(subtree, "<Enter>", self._on_enter)
        bind_recursive(subtree, "<Leave>", self._on_leave)
        if self._on_click is not None:
            set_cursor_recursive(subtree, "hand2")

    def set_selected(self, selected: bool) -> None:
        if selected != self._selected:
            self._selected = selected
            self._apply_style()

    def set_accent(self, accent: Color | None) -> None:
        """Bordure colorée signalant que la carte est une cible d'action (outil armé)."""
        if accent != self._accent:
            self._accent = accent
            self._apply_style()

    @property
    def is_selected(self) -> bool:
        return self._selected

    def _on_press(self, _event: tk.Event) -> None:
        if self._on_click is not None:
            self._on_click()

    def _on_enter(self, _event: tk.Event) -> None:
        if not self._hovered:
            self._hovered = True
            self._apply_style()

    def _on_leave(self, _event: tk.Event) -> None:
        # Passer d'un enfant à l'autre émet <Leave> : ne quitter l'état survolé que si
        # le pointeur a réellement quitté la carte.
        pointer = self.winfo_containing(*self.winfo_pointerxy())
        if contains_widget(self, pointer):
            return
        if self._hovered:
            self._hovered = False
            self._apply_style()

    def _apply_style(self) -> None:
        if self._selected:
            fill = self._selected_color
        elif self._hovered:
            fill = self._hover_color
        else:
            fill = self._base_color

        if self._accent is not None:
            border = self._accent
        elif self._selected:
            border = self._selected_border_color
        else:
            border = self._border_color

        self.configure(fg_color=fill, border_color=border)


class EmptyState(Group):
    """Message centré affiché à la place d'une liste vide."""

    def __init__(self, master: tk.Misc, title: str, detail: str = "") -> None:
        super().__init__(master)

        ctk.CTkLabel(self, text=title, font=Fonts.body_bold(), text_color=Palette.TEXT_MUTED).pack()
        if detail:
            ctk.CTkLabel(
                self,
                text=detail,
                font=Fonts.small(),
                text_color=Palette.TEXT_FAINT,
                justify="center",
                wraplength=420,
            ).pack(pady=(Metrics.PAD_XS, 0))
