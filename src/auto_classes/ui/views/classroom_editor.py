"""Édition d'une classe, en place dans la bande « Classes ».

Remplace la carte cliquée par un formulaire de même hauteur, sans fenêtre modale. Les
modifications s'appliquent au fil de la saisie (validation à Entrée ou à la perte du
focus) plutôt qu'au moment d'un « Enregistrer » : il n'y a rien à annuler puisque rien
n'est mis en attente.

Le mot « option » est celui des enseignants ; le backend, lui, parle de tags — d'où le
décalage entre les libellés et les identifiants du code.
"""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components import DangerButton, GhostButton, Group, IconButton, TagPill
from auto_classes.ui.session import SessionError, SessionState
from auto_classes.ui.theme import Fonts, Icons, Metrics, Palette

FIELD_HEIGHT = 28


class ClassroomEditor(ctk.CTkFrame):
    """Formulaire d'une classe : nom, effectif, options, suppression."""

    def __init__(
        self,
        master: tk.Misc,
        session: SessionState,
        classroom_id: str,
        *,
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            master,
            width=Metrics.CLASSROOM_EDITOR_WIDTH,
            height=Metrics.CLASSROOM_EDITOR_HEIGHT,
            fg_color=Palette.SURFACE,
            corner_radius=Metrics.RADIUS_SM,
            border_width=2,
            border_color=Palette.SELECTION,
        )

        self._session = session
        self.classroom_id = classroom_id
        self._classroom_id = classroom_id
        self._on_close = on_close
        self._confirming_delete = False

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        classroom = session.classroom(classroom_id)
        if classroom is None:
            on_close()
            return

        self._build_name_row(classroom.name)
        self._build_sizes_row(classroom.min_size, classroom.max_size)
        self._build_options_row()

        self._error = ctk.CTkLabel(
            self,
            text="",
            font=Fonts.small(),
            text_color=Palette.DANGER,
            anchor="w",
            justify="left",
            wraplength=Metrics.CLASSROOM_EDITOR_WIDTH - 2 * Metrics.PAD_MD,
        )

        self._delete = DangerButton(
            self, "Supprimer la classe", self._delete_clicked, height=FIELD_HEIGHT, font=Fonts.small()
        )
        self._delete.grid(
            row=4, column=0, sticky="w", padx=Metrics.PAD_MD, pady=(Metrics.PAD_XS, Metrics.PAD_SM)
        )

        self.refresh()
        self._name_entry.focus_set()

    # ------------------------------------------------------------------ montage

    def _entry(self, parent: tk.Misc, placeholder: str, width: int = 0) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            font=Fonts.body(),
            height=FIELD_HEIGHT,
            width=width,
            corner_radius=Metrics.RADIUS_SM,
            fg_color=Palette.SURFACE_ALT,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT,
        )

    def _build_name_row(self, name: str) -> None:
        row = Group(self)
        row.grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_MD, 0))
        row.grid_columnconfigure(0, weight=1)

        self._name_entry = self._entry(row, "Nom de la classe")
        self._name_entry.insert(0, name)
        self._name_entry.grid(row=0, column=0, sticky="ew")
        self._name_entry.bind("<Return>", lambda _event: self._apply_name())
        self._name_entry.bind("<FocusOut>", lambda _event: self._apply_name(revert_on_error=True))
        self._name_entry.bind("<Escape>", lambda _event: self._on_close())

        IconButton(row, Icons.CLOSE, self._on_close, size=FIELD_HEIGHT).grid(
            row=0, column=1, padx=(Metrics.PAD_XS, 0)
        )

    def _build_sizes_row(self, min_size: int | None, max_size: int | None) -> None:
        row = Group(self)
        row.grid(row=1, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_SM, 0))

        ctk.CTkLabel(
            row, text="Effectif", font=Fonts.small_bold(), text_color=Palette.TEXT_MUTED
        ).pack(side="left", padx=(0, Metrics.PAD_SM))

        self._min_size = self._entry(row, "min", width=56)
        self._max_size = self._entry(row, "max", width=56)
        for entry, value in ((self._min_size, min_size), (self._max_size, max_size)):
            if value is not None:
                entry.insert(0, str(value))
            entry.bind("<Return>", lambda _event: self._apply_sizes())
            entry.bind("<FocusOut>", lambda _event: self._apply_sizes(revert_on_error=True))
            entry.bind("<Escape>", lambda _event: self._on_close())

        self._min_size.pack(side="left")
        ctk.CTkLabel(row, text="à", font=Fonts.small(), text_color=Palette.TEXT_MUTED).pack(
            side="left", padx=Metrics.PAD_XS
        )
        self._max_size.pack(side="left")
        ctk.CTkLabel(
            row, text="vide = libre", font=Fonts.small(), text_color=Palette.TEXT_FAINT
        ).pack(side="left", padx=(Metrics.PAD_SM, 0))

    def _build_options_row(self) -> None:
        row = Group(self)
        row.grid(row=2, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_SM, 0))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text="Options", font=Fonts.small_bold(), text_color=Palette.TEXT_MUTED
        ).grid(row=0, column=0, padx=(0, Metrics.PAD_SM))

        self._option_entry = self._entry(row, "latin, bilangue…")
        self._option_entry.grid(row=0, column=1, sticky="ew")
        self._option_entry.bind("<Return>", lambda _event: self._add_option())
        self._option_entry.bind("<Escape>", lambda _event: self._on_close())

        GhostButton(
            row, "Ajouter", self._add_option, width=76, height=FIELD_HEIGHT, font=Fonts.small()
        ).grid(row=0, column=2, padx=(Metrics.PAD_XS, 0))

        self._option_pills = Group(self)
        self._option_pills.grid(row=3, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_XS, 0))

    # ------------------------------------------------------------- rafraîchissement

    def refresh(self) -> None:
        """Réaligne l'affichage sur la session (options posées, nom renommé ailleurs)."""
        classroom = self._session.classroom(self._classroom_id)
        if classroom is None:
            self._on_close()
            return

        for child in self._option_pills.winfo_children():
            child.destroy()

        if not classroom.tags:
            ctk.CTkLabel(
                self._option_pills,
                text="Aucune option",
                font=Fonts.small(),
                text_color=Palette.TEXT_FAINT,
            ).pack(side="left")
            return

        for tag in sorted(classroom.tags, key=str.casefold):
            TagPill(self._option_pills, tag, on_remove=self._remove_option).pack(
                side="left", padx=(0, Metrics.PAD_XS)
            )

    def commit(self) -> None:
        """Valide la saisie en cours avant que le formulaire ne disparaisse.

        Cliquer une autre classe ne déplace pas le focus clavier (une carte n'en prend
        pas) : sans cet appel, `<FocusOut>` ne partirait jamais et le nom fraîchement
        tapé serait détruit avec le formulaire. Une valeur invalide est abandonnée
        plutôt que signalée — il n'y a plus d'endroit où afficher l'erreur.
        """
        if not self.winfo_exists() or self._session.classroom(self._classroom_id) is None:
            return
        self._apply_name(revert_on_error=True)
        self._apply_sizes(revert_on_error=True)

    # ---------------------------------------------------------------- réactions

    def _apply_name(self, *, revert_on_error: bool = False) -> None:
        try:
            self._session.update_classroom(self._classroom_id, name=self._name_entry.get())
        except SessionError as error:
            self._report(error, self._name_entry, self._current_name(), revert_on_error)
        else:
            self._clear_error()

    def _apply_sizes(self, *, revert_on_error: bool = False) -> None:
        try:
            self._session.update_classroom(
                self._classroom_id,
                min_size=_parse_size(self._min_size.get(), "minimum"),
                max_size=_parse_size(self._max_size.get(), "maximum"),
            )
        except SessionError as error:
            classroom = self._session.classroom(self._classroom_id)
            if revert_on_error and classroom is not None:
                _set(self._min_size, "" if classroom.min_size is None else str(classroom.min_size))
                _set(self._max_size, "" if classroom.max_size is None else str(classroom.max_size))
                self._clear_error()
            else:
                self._show_error(str(error))
        else:
            self._clear_error()

    def _add_option(self) -> None:
        option = self._option_entry.get().strip()
        if not option:
            return
        classroom = self._session.classroom(self._classroom_id)
        if classroom is None:
            return
        try:
            self._session.update_classroom(self._classroom_id, tags=classroom.tags | {option})
        except SessionError as error:
            self._show_error(str(error))
            return
        self._option_entry.delete(0, "end")
        self._clear_error()

    def _remove_option(self, option: str) -> None:
        classroom = self._session.classroom(self._classroom_id)
        if classroom is None:
            return
        self._session.update_classroom(self._classroom_id, tags=classroom.tags - {option})

    def _delete_clicked(self) -> None:
        """Suppression en deux temps : le bouton demande confirmation sur lui-même.

        Une fenêtre de confirmation romprait le principe de l'édition en place.
        """
        if not self._confirming_delete:
            self._confirming_delete = True
            self._delete.configure(
                text="Confirmer la suppression",
                fg_color=Palette.DANGER,
                text_color=Palette.TEXT_ON_ACCENT,
                hover_color=Palette.DANGER_HOVER,
            )
            self._show_error(
                "Ses options quitteront les contraintes des élèves si aucune autre "
                "classe ne les porte."
            )
            return

        self._session.remove_classroom(self._classroom_id)
        self._on_close()

    # ------------------------------------------------------------------ interne

    def _current_name(self) -> str:
        classroom = self._session.classroom(self._classroom_id)
        return "" if classroom is None else classroom.name

    def _report(
        self, error: SessionError, entry: ctk.CTkEntry, fallback: str, revert: bool
    ) -> None:
        if revert:
            _set(entry, fallback)
            self._clear_error()
        else:
            self._show_error(str(error))

    def _show_error(self, message: str) -> None:
        self._error.configure(text=message)
        self._error.grid(row=5, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(0, Metrics.PAD_XS))

    def _clear_error(self) -> None:
        self._error.configure(text="")
        self._error.grid_remove()


def _set(entry: ctk.CTkEntry, value: str) -> None:
    entry.delete(0, "end")
    entry.insert(0, value)


def _parse_size(raw: str, which: str) -> int | None:
    text = raw.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        raise SessionError(f"L'effectif {which} doit être un nombre entier.") from None
