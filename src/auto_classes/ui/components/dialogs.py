"""Fenêtres modales : base commune, saisie de texte, confirmation, information."""

from collections.abc import Callable
from typing import Any

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components.buttons import DangerButton, GhostButton, PrimaryButton
from auto_classes.ui.components.surfaces import Group
from auto_classes.ui.theme import Fonts, Metrics, Palette


class ModalDialog(ctk.CTkToplevel):
    """Fenêtre modale centrée sur son parent, fermable par Échap.

    Les sous-classes remplissent `self.content` et `self.footer`, puis l'appelant
    obtient le résultat via `show()` — qui bloque jusqu'à la fermeture.
    """

    def __init__(self, master: tk.Misc, title: str, *, width: int = 420) -> None:
        super().__init__(master)

        self._result: Any = None
        self._preferred_width = width

        self.title(title)
        self.configure(fg_color=Palette.WINDOW)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda _event: self.cancel())

        self.content = Group(self)
        self.content.pack(fill="both", expand=True, padx=Metrics.PAD_XL, pady=(Metrics.PAD_XL, 0))

        self._error = ctk.CTkLabel(
            self,
            text="",
            font=Fonts.small(),
            text_color=Palette.DANGER,
            anchor="w",
            justify="left",
            wraplength=width - 2 * Metrics.PAD_XL,
        )

        self.footer = Group(self)
        self.footer.pack(fill="x", padx=Metrics.PAD_XL, pady=Metrics.PAD_LG)

    def show(self) -> Any:
        self.update_idletasks()
        self._center_on_parent()
        # grab_set échoue tant que la fenêtre n'est pas mappée par le gestionnaire de fenêtres.
        self.after(80, self._grab)
        self.wait_window()
        return self._result

    def show_error(self, message: str) -> None:
        self._error.configure(text=message)
        self._error.pack(fill="x", padx=Metrics.PAD_XL, pady=(Metrics.PAD_SM, 0), before=self.footer)

    def clear_error(self) -> None:
        self._error.configure(text="")
        self._error.pack_forget()

    def cancel(self) -> None:
        self._result = None
        self.destroy()

    def accept(self, result: Any) -> None:
        self._result = result
        self.destroy()

    def _center_on_parent(self) -> None:
        parent = self.master.winfo_toplevel()
        width = max(self._preferred_width, self.winfo_reqwidth())
        height = self.winfo_reqheight()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 3)
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def _grab(self) -> None:
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass  # fenêtre déjà refermée entre-temps


class TextPromptDialog(ModalDialog):
    """Saisie d'une ligne de texte, avec validation en place.

    `validator` renvoie un message d'erreur (la fenêtre reste ouverte) ou None.
    """

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        label: str,
        *,
        initial: str = "",
        placeholder: str = "",
        detail: str = "",
        submit_text: str = "Ajouter",
        validator: Callable[[str], str | None] | None = None,
    ) -> None:
        super().__init__(master, title)
        self._validator = validator

        ctk.CTkLabel(self.content, text=label, font=Fonts.body_bold(), text_color=Palette.TEXT).pack(
            anchor="w"
        )
        if detail:
            ctk.CTkLabel(
                self.content,
                text=detail,
                font=Fonts.small(),
                text_color=Palette.TEXT_MUTED,
                anchor="w",
                justify="left",
                wraplength=360,
            ).pack(anchor="w", pady=(2, 0))

        self._entry = ctk.CTkEntry(
            self.content,
            placeholder_text=placeholder,
            font=Fonts.body(),
            height=Metrics.CONTROL_HEIGHT,
            fg_color=Palette.SURFACE,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT,
        )
        self._entry.pack(fill="x", pady=(Metrics.PAD_SM, 0))
        self._entry.insert(0, initial)
        self._entry.bind("<Return>", lambda _event: self._submit())
        self._entry.after(120, self._entry.focus_set)

        GhostButton(self.footer, "Annuler", self.cancel, width=96).pack(side="right")
        PrimaryButton(self.footer, submit_text, self._submit, width=112).pack(
            side="right", padx=(0, Metrics.PAD_SM)
        )

    def _submit(self) -> None:
        value = self._entry.get().strip()
        if self._validator is not None:
            problem = self._validator(value)
            if problem is not None:
                self.show_error(problem)
                return
        self.accept(value)


class ConfirmDialog(ModalDialog):
    """Confirmation d'une action destructive. `show()` renvoie True ou None."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        message: str,
        *,
        confirm_text: str = "Supprimer",
    ) -> None:
        super().__init__(master, title)

        ctk.CTkLabel(
            self.content,
            text=message,
            font=Fonts.body(),
            text_color=Palette.TEXT,
            justify="left",
            wraplength=360,
        ).pack(anchor="w")

        GhostButton(self.footer, "Annuler", self.cancel, width=96).pack(side="right")
        DangerButton(self.footer, confirm_text, lambda: self.accept(True), width=112).pack(
            side="right", padx=(0, Metrics.PAD_SM)
        )

    @classmethod
    def ask(cls, master: tk.Misc, title: str, message: str, **kwargs: Any) -> bool:
        return bool(cls(master, title, message, **kwargs).show())


class NoticeDialog(ModalDialog):
    """Information simple : un message, un bouton pour fermer."""

    def __init__(self, master: tk.Misc, title: str, message: str) -> None:
        super().__init__(master, title)

        ctk.CTkLabel(
            self.content,
            text=message,
            font=Fonts.body(),
            text_color=Palette.TEXT,
            justify="left",
            wraplength=360,
        ).pack(anchor="w")

        PrimaryButton(self.footer, "Compris", lambda: self.accept(True), width=112).pack(side="right")

    @classmethod
    def inform(cls, master: tk.Misc, title: str, message: str) -> None:
        cls(master, title, message).show()
