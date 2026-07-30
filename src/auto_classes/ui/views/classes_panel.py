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
from auto_classes.ui.views.classroom_editor import ClassroomEditor

MAX_VISIBLE_OPTIONS = 3


class ClassroomCard(ClickableCard):
    """Carte d'une classe : nom, effectif visé, aperçu des options. Clic = édition."""

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

        options = Group(self)
        options.grid(row=2, column=0, sticky="new", padx=Metrics.PAD_MD)
        self._fill_options(options, sorted(classroom.tags, key=str.casefold))

        self.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(
            self,
            text=f"{Icons.GEAR}  Configurer",
            font=Fonts.small(),
            text_color=Palette.TEXT_FAINT,
            anchor="w",
        ).grid(row=4, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(0, Metrics.PAD_SM))

        self.activate()

    def _fill_options(self, holder: ctk.CTkFrame, options: list[str]) -> None:
        if not options:
            ctk.CTkLabel(
                holder, text="Aucune option", font=Fonts.small(), text_color=Palette.TEXT_FAINT
            ).pack(anchor="w")
            return

        for option in options[:MAX_VISIBLE_OPTIONS]:
            TagPill(holder, option, color=Palette.SURFACE).pack(anchor="w", pady=1)
        remaining = len(options) - MAX_VISIBLE_OPTIONS
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
        self._editing_id: str | None = None
        self._editor: ClassroomEditor | None = None
        self._rendered_ids: list[str] = []
        self._rebuilding = False

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
            "Ajoutez une classe avec « + » : son nom, son effectif et ses options.",
        )

        session.classrooms_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        """Reconstruit la bande : une carte par classe, un formulaire pour celle éditée.

        L'éditeur écrit dans la session à chaque champ validé, ce qui rappelle cette
        méthode. Tant qu'il porte toujours sur la bonne classe et que la liste n'a pas
        bougé, il est conservé tel quel : le reconstruire ferait perdre le focus au
        beau milieu d'une saisie.
        """
        if self._rebuilding:
            return  # ré-entrée provoquée par la validation de la saisie ci-dessous

        identifiers = [classroom.id for classroom in self._session.classrooms]
        if self._editing_id is not None and self._editing_id not in identifiers:
            self._editing_id = None  # la classe éditée vient d'être supprimée

        if self._can_keep_editor(identifiers):
            self._editor.refresh()
            self._set_detail(self._session.classrooms)
            return

        self._rebuilding = True
        try:
            if self._editor is not None and self._editor.winfo_exists():
                self._editor.commit()
            self._rebuild()
        finally:
            self._rebuilding = False

    def _rebuild(self) -> None:
        """Détruit et reconstruit le contenu de la bande, session relue après validation."""
        for child in self._strip.winfo_children():
            if child is not self._empty:
                child.destroy()
        self._editor = None

        classrooms = self._session.classrooms
        self._rendered_ids = [classroom.id for classroom in classrooms]
        self._set_detail(classrooms)
        self.configure(
            height=Metrics.CLASSES_BAND_EDITING_HEIGHT
            if self._editing_id is not None
            else Metrics.CLASSES_BAND_HEIGHT
        )

        if not classrooms:
            self._empty.pack(pady=Metrics.PAD_XL, padx=Metrics.PAD_XL)
            return

        self._empty.pack_forget()
        for classroom in classrooms:
            if classroom.id == self._editing_id:
                self._editor = ClassroomEditor(
                    self._strip, self._session, classroom.id, on_close=self._close_editor
                )
                widget: tk.Widget = self._editor
            else:
                widget = ClassroomCard(
                    self._strip,
                    classroom,
                    lambda classroom_id=classroom.id: self._edit_classroom(classroom_id),
                )
            widget.pack(side="left", padx=(0, Metrics.PAD_SM), pady=Metrics.PAD_XS, anchor="n")

    def _can_keep_editor(self, identifiers: list[str]) -> bool:
        """Le formulaire en place ne survit que s'il porte encore sur la classe éditée.

        Sans la comparaison des identifiants, cliquer une autre classe changeait l'état
        sans changer le formulaire : on éditait toujours la première.
        """
        return (
            self._editor is not None
            and self._editor.winfo_exists()
            and self._editing_id is not None
            and self._editor.classroom_id == self._editing_id
            and identifiers == self._rendered_ids
        )

    def _set_detail(self, classrooms: list[ClassroomModel]) -> None:
        self._header.set_detail(f"{len(classrooms)} créée" + ("s" if len(classrooms) > 1 else ""))

    def _add_classroom(self) -> None:
        """Crée la classe et ouvre aussitôt son formulaire : elle n'a encore qu'un nom
        provisoire, l'enseignant a forcément quelque chose à y saisir."""
        try:
            classroom = self._session.add_classroom()
        except SessionError as error:
            NoticeDialog.inform(self, "Ajout impossible", str(error))
            return
        self._edit_classroom(classroom.id)

    def _edit_classroom(self, classroom_id: str) -> None:
        self._editing_id = classroom_id
        self.refresh()

    def _close_editor(self) -> None:
        self._editing_id = None
        self.refresh()
