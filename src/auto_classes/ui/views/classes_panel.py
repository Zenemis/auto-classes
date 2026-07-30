"""Bande moyenne : les classes à créer, sous forme de cartes défilant horizontalement."""

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components import (
    ClickableCard,
    EmptyState,
    Group,
    IconButton,
    NoticeDialog,
    Panel,
    ScrollArea,
    SectionHeader,
    TagPill,
)
from auto_classes.ui.models import ClassroomModel
from auto_classes.ui.session import SessionError, SessionState
from auto_classes.ui.theme import Fonts, Icons, Metrics, Palette
from auto_classes.ui.views.classroom_dialog import ClassroomDialog

MAX_VISIBLE_TAGS = 3


class ClassroomCard(ClickableCard):
    """Carte d'une classe : nom, effectif visé, aperçu des tags. Clic = configuration."""

    def __init__(self, master: tk.Misc, classroom: ClassroomModel, on_open: object) -> None:
        super().__init__(
            master,
            on_click=on_open,  # type: ignore[arg-type]
            width=Metrics.CLASSROOM_CARD_WIDTH,
            height=Metrics.CLASSROOM_CARD_HEIGHT,
            base_color=Palette.SURFACE_ALT,
        )
        self.classroom_id = classroom.id
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text=classroom.name, font=Fonts.heading(), text_color=Palette.TEXT, anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_MD, 0))

        ctk.CTkLabel(
            self,
            text=classroom.size_label(),
            font=Fonts.small(),
            text_color=Palette.TEXT_MUTED if classroom.has_size_rule else Palette.TEXT_FAINT,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(2, Metrics.PAD_SM))

        tags = Group(self)
        tags.grid(row=2, column=0, sticky="new", padx=Metrics.PAD_MD)
        self._fill_tags(tags, sorted(classroom.tags, key=str.casefold))

        self.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(
            self,
            text=f"{Icons.GEAR}  Configurer",
            font=Fonts.small(),
            text_color=Palette.TEXT_FAINT,
            anchor="w",
        ).grid(row=4, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(0, Metrics.PAD_SM))

        self.activate()

    def _fill_tags(self, holder: ctk.CTkFrame, tags: list[str]) -> None:
        if not tags:
            ctk.CTkLabel(
                holder, text="Aucun tag", font=Fonts.small(), text_color=Palette.TEXT_FAINT
            ).pack(anchor="w")
            return

        for tag in tags[:MAX_VISIBLE_TAGS]:
            TagPill(holder, tag, color=Palette.SURFACE).pack(anchor="w", pady=1)
        remaining = len(tags) - MAX_VISIBLE_TAGS
        if remaining > 0:
            ctk.CTkLabel(
                holder,
                text=f"+ {remaining} autre" + ("s" if remaining > 1 else ""),
                font=Fonts.small(),
                text_color=Palette.TEXT_FAINT,
            ).pack(anchor="w", pady=(2, 0))


class ClassesPanel(Panel):
    """Bande « Classes » : en-tête avec « + », puis les cartes des classes créées."""

    def __init__(self, master: tk.Misc, session: SessionState) -> None:
        super().__init__(master, height=Metrics.CLASSES_BAND_HEIGHT)
        self._session = session

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._header = SectionHeader(self, "Classes")
        self._header.grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_MD, 0))
        IconButton(self._header.actions, Icons.ADD, self._add_classroom, fg_color=Palette.SURFACE_ALT).pack()

        self._strip = ScrollArea(self, orientation="horizontal")
        self._strip.grid(row=1, column=0, sticky="nsew", padx=Metrics.PAD_SM, pady=Metrics.PAD_SM)

        self._empty = EmptyState(
            self._strip,
            "Aucune classe",
            "Ajoutez une classe avec « + » : son nom, son effectif et ses tags.",
        )

        session.classrooms_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        for child in self._strip.winfo_children():
            if child is not self._empty:
                child.destroy()

        classrooms = self._session.classrooms
        self._header.set_detail(f"{len(classrooms)} créée" + ("s" if len(classrooms) > 1 else ""))

        if not classrooms:
            self._empty.pack(pady=Metrics.PAD_XL, padx=Metrics.PAD_XL)
            return

        self._empty.pack_forget()
        for classroom in classrooms:
            card = ClassroomCard(
                self._strip,
                classroom,
                lambda classroom_id=classroom.id: self._open_classroom(classroom_id),
            )
            card.pack(side="left", padx=(0, Metrics.PAD_SM), pady=Metrics.PAD_XS, fill="y")

    def _add_classroom(self) -> None:
        try:
            self._session.add_classroom()
        except SessionError as error:
            NoticeDialog.inform(self, "Ajout impossible", str(error))

    def _open_classroom(self, classroom_id: str) -> None:
        ClassroomDialog(self, self._session, classroom_id).show()
