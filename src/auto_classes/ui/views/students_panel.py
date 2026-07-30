"""Bande basse : liste des élèves à gauche, inspecteur de l'élève sélectionné à droite.

C'est ici qu'un outil armé se transforme en contrainte : quand l'utilisateur a choisi
« Séparer de » ou « Mettre avec » dans l'inspecteur, le clic suivant sur une tuile crée
la relation au lieu de changer la sélection.
"""

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components import (
    EmptyState,
    FlowGrid,
    IconButton,
    InlineComposer,
    Panel,
    SectionHeader,
)
from auto_classes.ui.interaction import InteractionState
from auto_classes.ui.session import SessionError, SessionState
from auto_classes.ui.theme import Fonts, Icons, Metrics, Palette
from auto_classes.ui.views.student_inspector import TOOL_ACCENTS, StudentInspector
from auto_classes.ui.views.student_tile import StudentTile

NAME_SEPARATORS = (",", ";", "\t")

# Lignes de la bande, nommées : la liste, l'état vide et l'inspecteur doivent occuper
# la même, sous peine de voir la liste glisser d'un cran à la sélection d'un élève.
ROW_HEADER = 0
ROW_COMPOSER = 1
ROW_BODY = 2

COLUMN_LIST = 0
COLUMN_INSPECTOR = 1


class StudentsPanel(Panel):
    """Bande « Élèves »."""

    def __init__(self, master: tk.Misc, session: SessionState, interaction: InteractionState) -> None:
        super().__init__(master)
        self._session = session
        self._interaction = interaction
        self._tiles: dict[str, StudentTile] = {}
        self._filter = ""

        self.grid_columnconfigure(COLUMN_LIST, weight=1)
        self.grid_rowconfigure(ROW_BODY, weight=1)

        self._build_header()

        self._composer = InlineComposer(
            self,
            on_submit=self._submit_students,
            placeholder="Nom de l'élève — plusieurs noms séparés par des virgules",
        )
        self._composer.grid(
            row=ROW_COMPOSER,
            column=COLUMN_LIST,
            sticky="ew",
            padx=Metrics.PAD_MD,
            pady=(0, Metrics.PAD_SM),
        )
        self._composer.close()  # replié tant que « + » n'a pas été cliqué

        self._list = FlowGrid(
            self,
            min_tile_width=Metrics.STUDENT_TILE_WIDTH,
        )
        self._list.grid(
            row=ROW_BODY,
            column=COLUMN_LIST,
            sticky="nsew",
            padx=(Metrics.PAD_SM, 0),
            pady=(0, Metrics.PAD_SM),
        )

        self._empty = EmptyState(
            self,
            "Aucun élève",
            "Ajoutez un élève avec « + », ou importez une liste depuis le menu.",
        )

        self._inspector = StudentInspector(self, session, interaction)

        session.students_changed.connect(self._sync_tiles)
        session.constraints_changed.connect(self._refresh_tiles)
        interaction.selection_changed.connect(self._on_selection_changed)
        interaction.tool_changed.connect(self._on_tool_changed)

        self._sync_tiles()

    # ------------------------------------------------------------------ montage

    def _build_header(self) -> None:
        self._header = SectionHeader(self, "Élèves")
        self._header.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=Metrics.PAD_MD, pady=Metrics.PAD_MD
        )

        self._search = ctk.CTkEntry(
            self._header.actions,
            placeholder_text=f"{Icons.SEARCH} Rechercher",
            width=180,
            height=Metrics.ICON_BUTTON_SIZE,
            corner_radius=Metrics.RADIUS_SM,
            fg_color=Palette.SURFACE_ALT,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT,
            font=Fonts.small(),
        )
        self._search.pack(side="left", padx=(0, Metrics.PAD_SM))
        self._search.bind("<KeyRelease>", self._on_search)

        IconButton(
            self._header.actions, Icons.ADD, self._toggle_composer, fg_color=Palette.SURFACE_ALT
        ).pack(side="left")

    # ------------------------------------------------------------------ synchro

    def _sync_tiles(self) -> None:
        """Crée/détruit les tuiles pour coller à la liste d'élèves, puis les replace."""
        students = self._session.students
        alive = {student.id for student in students}

        for student_id in list(self._tiles):
            if student_id not in alive:
                self._tiles.pop(student_id).destroy()

        for student in students:
            if student.id not in self._tiles:
                self._tiles[student.id] = StudentTile(
                    self._list, student, self._session, self._on_tile_clicked
                )

        self._refresh_tiles()
        self._layout_tiles(students)
        self._header.set_detail(f"{len(students)} au total")

    def _refresh_tiles(self) -> None:
        for tile in self._tiles.values():
            tile.refresh()
        self._apply_visual_state()

    def _layout_tiles(self, students) -> None:
        visible = [student for student in students if self._matches(student.name)]
        self._list.set_tiles([self._tiles[student.id] for student in visible])

        if students:
            self._empty.grid_remove()
            self._list.grid()
        else:
            self._list.grid_remove()
            self._empty.grid(
                row=ROW_BODY, column=COLUMN_LIST, sticky="nsew", pady=Metrics.PAD_XL
            )

    def _matches(self, name: str) -> bool:
        return self._filter in name.casefold()

    def _apply_visual_state(self) -> None:
        """Sélection et, si un outil d'élève est armé, mise en évidence des cibles."""
        selected = self._interaction.selected_student_id
        tool = self._interaction.active_tool
        accent = TOOL_ACCENTS[tool] if tool is not None and tool.targets_students else None

        for student_id, tile in self._tiles.items():
            tile.set_selected(student_id == selected)
            tile.set_accent(None if student_id == selected else accent)

    # ---------------------------------------------------------------- réactions

    def _on_tile_clicked(self, student_id: str) -> None:
        tool = self._interaction.active_tool
        selected = self._interaction.selected_student_id

        if tool is not None and tool.targets_students and selected is not None and selected != student_id:
            try:
                self._session.add_relation(tool.relation_kind, selected, student_id)
            except SessionError as error:
                NoticeDialog.inform(self, "Contrainte impossible", str(error))
            return  # l'outil reste armé : plusieurs contraintes s'enchaînent

        self._interaction.select_student(student_id)

    def _on_selection_changed(self, student_id: str | None) -> None:
        if student_id is None:
            self._inspector.grid_remove()
        else:
            self._inspector.grid(
                row=ROW_BODY,
                column=COLUMN_INSPECTOR,
                sticky="nsew",
                padx=Metrics.PAD_SM,
                pady=(0, Metrics.PAD_SM),
            )
        self._apply_visual_state()

    def _on_tool_changed(self, _tool) -> None:
        self._apply_visual_state()

    def _on_search(self, _event: tk.Event) -> None:
        self._filter = self._search.get().strip().casefold()
        self._layout_tiles(self._session.students)

    def _toggle_composer(self) -> None:
        self._composer.toggle()

    def _submit_students(self, raw: str) -> str | None:
        """Ajoute les noms saisis ; ne garde dans le champ que ceux qui ont été refusés."""
        added, rejected = self._session.add_students(_split_names(raw))
        if not rejected:
            return None

        self._composer.set_text(", ".join(name for name, _reason in rejected))
        reasons = list(dict.fromkeys(reason for _name, reason in rejected))
        if added:
            plural = "s" if len(added) > 1 else ""
            reasons.insert(0, f"{len(added)} élève{plural} ajouté{plural}.")
        return " ".join(reasons)


def _split_names(raw: str) -> list[str]:
    text = raw
    for separator in NAME_SEPARATORS:
        text = text.replace(separator, "\n")
    return [line.strip() for line in text.splitlines() if line.strip()]
