"""Bande fine du haut : import, Pronote, nombre de propositions, génération."""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui import assets
from auto_classes.ui.components import GhostButton, Panel, PrimaryButton
from auto_classes.ui.session import SessionState
from auto_classes.ui.theme import Fonts, Icons, Metrics, Palette

SOLUTION_CHOICES = ("1", "3", "5", "10", "20")

ICON_SIZE = 18


class MenuBar(Panel):
    """Barre d'actions. N'exécute rien elle-même : elle relaie vers les rappels fournis."""

    def __init__(
        self,
        master: tk.Misc,
        session: SessionState,
        *,
        on_import: Callable[[], None],
        on_pronote: Callable[[], None],
        on_generate: Callable[[], None],
    ) -> None:
        super().__init__(master, height=Metrics.MENU_BAND_HEIGHT)
        self._session = session

        self.grid_propagate(False)
        self.grid_columnconfigure(2, weight=1)

        # Le pictogramme d'import est reteint avec la couleur du texte (il est livré en
        # quasi noir) ; le logo Pronote garde ses propres couleurs de marque.
        GhostButton(
            self,
            "Importer",
            on_import,
            width=124,
            image=assets.icon(assets.IMPORT_ICON, size=ICON_SIZE, tint=Palette.TEXT),
            compound="left",
            anchor="center",
        ).grid(row=0, column=0, padx=(Metrics.PAD_MD, Metrics.PAD_SM), pady=Metrics.PAD_LG)

        GhostButton(
            self,
            "Pronote",
            on_pronote,
            width=118,
            image=assets.icon(assets.PRONOTE_ICON, size=ICON_SIZE),
            compound="left",
            anchor="center",
        ).grid(row=0, column=1, pady=Metrics.PAD_LG)

        ctk.CTkLabel(
            self, text="Propositions", font=Fonts.small(), text_color=Palette.TEXT_MUTED
        ).grid(row=0, column=3, padx=(0, Metrics.PAD_SM))

        self._solutions = ctk.CTkOptionMenu(
            self,
            values=list(SOLUTION_CHOICES),
            command=self._on_solutions_changed,
            width=76,
            height=Metrics.CONTROL_HEIGHT,
            corner_radius=Metrics.RADIUS_SM,
            fg_color=Palette.SURFACE_ALT,
            button_color=Palette.SURFACE_ALT,
            button_hover_color=Palette.HOVER,
            text_color=Palette.TEXT,
            dropdown_fg_color=Palette.SURFACE,
            dropdown_hover_color=Palette.HOVER,
            dropdown_text_color=Palette.TEXT,
            font=Fonts.body(),
            dropdown_font=Fonts.body(),
        )
        self._solutions.set(str(session.num_solutions))
        self._solutions.grid(row=0, column=4, padx=(0, Metrics.PAD_MD))

        self._generate = PrimaryButton(
            self, "Générer", on_generate, icon=Icons.GENERATE, width=132
        )
        self._generate.grid(row=0, column=5, padx=(0, Metrics.PAD_MD))

    def set_generating(self, generating: bool) -> None:
        self._generate.configure(
            text="Génération…" if generating else f"{Icons.GENERATE}  Générer",
            state="disabled" if generating else "normal",
        )

    def _on_solutions_changed(self, value: str) -> None:
        self._session.num_solutions = int(value)
