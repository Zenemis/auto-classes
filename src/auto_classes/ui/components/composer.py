"""Barre de saisie rapide qui s'ouvre sur place, sans fenêtre modale."""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components.buttons import IconButton, PrimaryButton
from auto_classes.ui.components.surfaces import Group
from auto_classes.ui.theme import Fonts, Icons, Metrics, Palette


class InlineComposer(Group):
    """Champ de saisie apparaissant dans la page, pour un ajout enchaîné.

    Reste ouvert après un ajout réussi, champ vidé et focus conservé : saisir dix
    élèves d'affilée ne doit pas demander dix ouvertures. `on_submit` renvoie un
    message d'erreur (affiché sous le champ, saisie conservée) ou None si tout est
    passé.

    Le placement appartient à l'appelant : `open()` et `close()` se contentent de
    remettre ou retirer la barre de sa cellule.
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_submit: Callable[[str], str | None],
        placeholder: str = "",
        submit_text: str = "Ajouter",
    ) -> None:
        super().__init__(master)

        self._on_submit = on_submit
        self._is_open = False

        self.grid_columnconfigure(0, weight=1)

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=Fonts.body(),
            height=Metrics.CONTROL_HEIGHT,
            corner_radius=Metrics.RADIUS_SM,
            fg_color=Palette.SURFACE,
            border_color=Palette.BORDER_STRONG,
            text_color=Palette.TEXT,
        )
        self._entry.grid(row=0, column=0, sticky="ew")
        self._entry.bind("<Return>", lambda _event: self._submit())
        self._entry.bind("<Escape>", lambda _event: self.close())

        PrimaryButton(self, submit_text, self._submit, width=96).grid(
            row=0, column=1, padx=(Metrics.PAD_SM, 0)
        )
        IconButton(self, Icons.CLOSE, self.close).grid(row=0, column=2, padx=(Metrics.PAD_XS, 0))

        self._error = ctk.CTkLabel(
            self,
            text="",
            font=Fonts.small(),
            text_color=Palette.DANGER,
            anchor="w",
            justify="left",
        )

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        self._is_open = True
        self.grid()
        self._entry.focus_set()

    def close(self) -> None:
        self._is_open = False
        self._entry.delete(0, "end")
        self._clear_error()
        self.grid_remove()

    def toggle(self) -> None:
        self.close() if self._is_open else self.open()

    def set_text(self, text: str) -> None:
        self._entry.delete(0, "end")
        self._entry.insert(0, text)

    def _submit(self) -> None:
        value = self._entry.get().strip()
        if not value:
            self.close()  # valider à vide revient à renoncer
            return

        self._clear_error()
        problem = self._on_submit(value)
        if problem is None:
            self._entry.delete(0, "end")
        else:
            self._error.configure(text=problem)
            self._error.grid(
                row=1, column=0, columnspan=3, sticky="ew", pady=(Metrics.PAD_XS, 0)
            )
        self._entry.focus_set()

    def _clear_error(self) -> None:
        self._error.configure(text="")
        self._error.grid_remove()
