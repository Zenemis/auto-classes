"""Fenêtre d'édition d'une classe : nom, effectifs, tags, suppression.

Les tags sont édités sur une copie locale et n'atteignent la session qu'à
l'enregistrement, pour qu'« Annuler » annule vraiment.
"""

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components import (
    ConfirmDialog,
    DangerButton,
    GhostButton,
    Group,
    ModalDialog,
    PrimaryButton,
    TagPill,
)
from auto_classes.ui.session import SessionError, SessionState
from auto_classes.ui.theme import Fonts, Metrics, Palette


class ClassroomDialog(ModalDialog):
    """Édition d'une classe existante. `show()` renvoie "saved", "deleted" ou None."""

    def __init__(self, master: tk.Misc, session: SessionState, classroom_id: str) -> None:
        super().__init__(master, "Configurer la classe", width=460)

        self._session = session
        self._classroom_id = classroom_id

        classroom = session.classroom(classroom_id)
        if classroom is None:
            self.after(0, self.cancel)
            return

        self._tags: set[str] = set(classroom.tags)

        self._name = self._field("Nom de la classe", classroom.name, placeholder="6e A, latin…")

        sizes = Group(self.content)
        sizes.pack(fill="x", pady=(Metrics.PAD_LG, 0))
        sizes.grid_columnconfigure((0, 1), weight=1)

        self._min_size = self._size_field(sizes, 0, "Effectif minimum", classroom.min_size)
        self._max_size = self._size_field(sizes, 1, "Effectif maximum", classroom.max_size)

        ctk.CTkLabel(
            self.content,
            text="Laisser vide pour ne pas contraindre l'effectif.",
            font=Fonts.small(),
            text_color=Palette.TEXT_FAINT,
            anchor="w",
        ).pack(fill="x", pady=(Metrics.PAD_XS, 0))

        self._build_tags_section()

        DangerButton(self.footer, "Supprimer la classe", self._delete, width=170).pack(side="left")
        GhostButton(self.footer, "Annuler", self.cancel, width=96).pack(side="right")
        PrimaryButton(self.footer, "Enregistrer", self._save, width=120).pack(
            side="right", padx=(0, Metrics.PAD_SM)
        )

    # ------------------------------------------------------------------ montage

    def _field(self, label: str, value: str, *, placeholder: str = "") -> ctk.CTkEntry:
        ctk.CTkLabel(
            self.content, text=label, font=Fonts.body_bold(), text_color=Palette.TEXT, anchor="w"
        ).pack(fill="x")
        entry = self._entry(self.content, placeholder)
        entry.pack(fill="x", pady=(Metrics.PAD_SM, 0))
        entry.insert(0, value)
        entry.bind("<Return>", lambda _event: self._save())
        return entry

    def _size_field(self, parent: tk.Misc, column: int, label: str, value: int | None) -> ctk.CTkEntry:
        holder = Group(parent)
        holder.grid(row=0, column=column, sticky="ew", padx=(0, Metrics.PAD_SM if column == 0 else 0))

        ctk.CTkLabel(
            holder, text=label, font=Fonts.body_bold(), text_color=Palette.TEXT, anchor="w"
        ).pack(fill="x")
        entry = self._entry(holder, "libre")
        entry.pack(fill="x", pady=(Metrics.PAD_SM, 0))
        if value is not None:
            entry.insert(0, str(value))
        entry.bind("<Return>", lambda _event: self._save())
        return entry

    def _entry(self, parent: tk.Misc, placeholder: str) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            font=Fonts.body(),
            height=Metrics.CONTROL_HEIGHT,
            fg_color=Palette.SURFACE,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT,
        )

    def _build_tags_section(self) -> None:
        ctk.CTkLabel(
            self.content, text="Tags", font=Fonts.body_bold(), text_color=Palette.TEXT, anchor="w"
        ).pack(fill="x", pady=(Metrics.PAD_LG, 0))
        ctk.CTkLabel(
            self.content,
            text="Options portées par la classe (latin, bilangue…). Les contraintes des élèves s'appuient dessus.",
            font=Fonts.small(),
            text_color=Palette.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=400,
        ).pack(fill="x", pady=(2, Metrics.PAD_SM))

        row = Group(self.content)
        row.pack(fill="x")
        self._tag_entry = self._entry(row, "latin")
        self._tag_entry.pack(side="left", fill="x", expand=True)
        self._tag_entry.bind("<Return>", lambda _event: self._add_tag())
        GhostButton(row, "Ajouter", self._add_tag, width=88).pack(side="left", padx=(Metrics.PAD_SM, 0))

        self._tag_holder = Group(self.content)
        self._tag_holder.pack(fill="x", pady=(Metrics.PAD_SM, 0))
        self._refresh_tags()

    # ---------------------------------------------------------------- réactions

    def _refresh_tags(self) -> None:
        for child in self._tag_holder.winfo_children():
            child.destroy()

        if not self._tags:
            ctk.CTkLabel(
                self._tag_holder,
                text="Aucun tag",
                font=Fonts.small(),
                text_color=Palette.TEXT_FAINT,
            ).pack(anchor="w")
            return

        for tag in sorted(self._tags, key=str.casefold):
            TagPill(self._tag_holder, tag, on_remove=self._remove_tag).pack(
                side="left", padx=(0, Metrics.PAD_XS)
            )

    def _add_tag(self) -> None:
        tag = self._tag_entry.get().strip()
        if not tag:
            return
        self._tags.add(tag)
        self._tag_entry.delete(0, "end")
        self._refresh_tags()

    def _remove_tag(self, tag: str) -> None:
        self._tags.discard(tag)
        self._refresh_tags()

    def _save(self) -> None:
        self.clear_error()
        try:
            min_size = _parse_size(self._min_size.get(), "minimum")
            max_size = _parse_size(self._max_size.get(), "maximum")
            self._session.update_classroom(
                self._classroom_id,
                name=self._name.get(),
                min_size=min_size,
                max_size=max_size,
                tags=self._tags,
            )
        except SessionError as error:
            self.show_error(str(error))
            return
        self.accept("saved")

    def _delete(self) -> None:
        classroom = self._session.classroom(self._classroom_id)
        if classroom is None:
            self.cancel()
            return
        # La modale de confirmation doit prendre le grab : on relâche le nôtre le temps du choix.
        self.grab_release()
        confirmed = ConfirmDialog.ask(
            self,
            "Supprimer la classe",
            f"Supprimer « {classroom.name} » ? Les contraintes portant sur ses tags "
            "seront retirées si aucune autre classe ne les porte.",
        )
        if not confirmed:
            self._grab()
            return
        self._session.remove_classroom(self._classroom_id)
        self.accept("deleted")


def _parse_size(raw: str, which: str) -> int | None:
    text = raw.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        raise SessionError(f"L'effectif {which} doit être un nombre entier.") from None
