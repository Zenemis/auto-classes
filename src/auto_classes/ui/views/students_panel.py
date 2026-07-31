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
    NoticeDialog,
    Panel,
    SectionHeader,
    contains_widget,
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

        # `bind_all` est global à toute l'application, pas seulement à cette bande :
        # avec 100+ élèves la liste n'a plus un pixel de fond visible pour cliquer
        # dessus, donc le clic « ailleurs » doit fonctionner depuis n'importe où dans
        # la fenêtre — menu, bande des classes, onglet Propositions. CustomTkinter
        # interdit `bind_all` sur ses propres widgets (« pourrait avoir un effet
        # indéfini ») ; on passe donc par l'implémentation Tk d'origine, que CTk
        # n'utilise lui-même que pour la molette et les touches Maj — jamais pour
        # `<Button-1>`, donc sans risque de collision avec son fonctionnement interne.
        #
        # `bind_all` vit au niveau de l'application, pas du widget : sans le retirer
        # explicitement à la destruction, il survivrait à cette bande et planterait au
        # clic suivant en essayant d'interroger un widget qui n'existe plus. Une seule
        # bande « Élèves » existe jamais à la fois, donc tout retirer pour la séquence
        # à la destruction ne perd rien.
        tk.Misc.bind_all(self, "<Button-1>", self._on_window_click, add="+")
        tk.Misc.bind(
            self, "<Destroy>", lambda _event: tk.Misc.unbind_all(self, "<Button-1>"), add="+"
        )

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
        """Sélection et, si un outil d'élève est armé, mise en évidence des cibles.

        Les élèves qui portent déjà la contrainte de l'outil armé sont marqués : un clic
        les libérerait, il faut le voir avant de cliquer.
        """
        selected = self._interaction.selected_student_id
        tool = self._interaction.active_tool
        armed = tool is not None and tool.targets_students and selected is not None
        accent = TOOL_ACCENTS[tool] if armed else None

        for student_id, tile in self._tiles.items():
            tile.set_selected(student_id == selected)
            if not armed or student_id == selected:
                tile.set_accent(None)
                continue
            relation = self._session.relation_between(selected, student_id)
            tile.set_accent(accent, filled=relation is not None and relation.kind is tool.relation_kind)

    # ---------------------------------------------------------------- réactions

    def _on_tile_clicked(self, student_id: str) -> None:
        tool = self._interaction.active_tool
        selected = self._interaction.selected_student_id

        if selected == student_id:
            # Recliquer sur l'élève déjà sélectionné le désélectionne (et désarme
            # l'outil au passage) : cliquer sa propre tuile n'a de toute façon aucun
            # sens pour un outil, qui vise toujours un *autre* élève ou une option.
            self._interaction.clear_selection()
            return

        if tool is not None and tool.targets_students and selected is not None:
            # Un clic pose la contrainte, un second la retire.
            try:
                self._session.toggle_relation(tool.relation_kind, selected, student_id)
            except SessionError as error:
                NoticeDialog.inform(self, "Contrainte impossible", str(error))
            return  # l'outil reste armé : plusieurs contraintes s'enchaînent

        self._interaction.select_student(student_id)

    def _on_window_click(self, event: tk.Event) -> None:
        """Un clic n'importe où hors des zones actives désélectionne (et désarme
        l'outil au passage, via `clear_selection`).

        « Zones actives » : chaque tuile (elle gère déjà son propre clic — la laisser
        aussi désélectionner bousculerait sélection et bascule d'outil sur le même
        clic), l'ascenseur de la liste (faire défiler 100+ élèves ne doit pas vider la
        sélection), l'inspecteur (lire une contrainte ou armer un outil n'est pas
        « cliquer ailleurs »), le composeur et l'en-tête (recherche, « + »). Le fond
        vide de la liste elle-même n'est PAS exclu : avec 100+ élèves il ne reste
        plus grand-chose à voir, mais ce qui en reste doit continuer à désélectionner.
        Tout le reste de la fenêtre — bande des classes, menu, onglet Propositions —
        désélectionne aussi.
        """
        toplevel = event.widget.winfo_toplevel()
        if toplevel is not self.winfo_toplevel():
            return  # une fenêtre modale (renommer, confirmer…) a le clic : ne pas y toucher

        managed_areas = (
            self._inspector,
            self._composer,
            self._header,
            self._list._scrollbar,
            *self._tiles.values(),
        )
        if any(contains_widget(area, event.widget) for area in managed_areas):
            return

        self._interaction.clear_selection()

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
