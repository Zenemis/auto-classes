"""Onglet 1 — Configuration : les trois bandes horizontales empilées."""

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.interaction import InteractionState
from auto_classes.ui.session import SessionState
from auto_classes.ui.theme import Metrics
from auto_classes.ui.views.classes_panel import ClassesPanel
from auto_classes.ui.views.menu_bar import MenuBar
from auto_classes.ui.views.students_panel import StudentsPanel


class SetupTab(ctk.CTkFrame):
    """Menu (bande fine), Classes (bande moyenne), Élèves (reste de la fenêtre)."""

    def __init__(
        self,
        master: tk.Misc,
        session: SessionState,
        interaction: InteractionState,
        *,
        on_import,
        on_pronote,
        on_generate,
    ) -> None:
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.menu_bar = MenuBar(
            self,
            session,
            on_import=on_import,
            on_pronote=on_pronote,
            on_generate=on_generate,
        )
        self.menu_bar.grid(row=0, column=0, sticky="ew", pady=(0, Metrics.PAD_MD))

        self.classes_panel = ClassesPanel(self, session)
        self.classes_panel.grid(row=1, column=0, sticky="ew", pady=(0, Metrics.PAD_MD))

        self.students_panel = StudentsPanel(self, session, interaction)
        self.students_panel.grid(row=2, column=0, sticky="nsew")
