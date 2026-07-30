"""Panneau de droite : outils de contrainte et contraintes existantes d'un élève.

L'inspecteur n'écrit jamais dans la liste des élèves : il arme un outil dans
`InteractionState`, et c'est `StudentsPanel` qui interprète le clic suivant.
"""

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components import (
    ConfirmDialog,
    ConstraintChip,
    DangerButton,
    GhostButton,
    Group,
    IconButton,
    NoticeDialog,
    Panel,
    ScrollArea,
    TagPill,
    TextPromptDialog,
    ToolButton,
)
from auto_classes.ui.interaction import InteractionState, Tool
from auto_classes.ui.session import SessionError, SessionState
from auto_classes.ui.theme import Color, Fonts, Icons, Metrics, Palette

TOOL_ACCENTS: dict[Tool, Color] = {
    Tool.APART: Palette.APART,
    Tool.TOGETHER: Palette.TOGETHER,
    Tool.EXCLUDE: Palette.EXCLUDE,
    Tool.INCLUDE: Palette.INCLUDE,
}

TOOL_LAYOUT = ((Tool.APART, Tool.TOGETHER), (Tool.EXCLUDE, Tool.INCLUDE))


class StudentInspector(Panel):
    """Fiche de l'élève sélectionné. Masquée (par le parent) quand rien n'est sélectionné."""

    def __init__(
        self,
        master: tk.Misc,
        session: SessionState,
        interaction: InteractionState,
    ) -> None:
        super().__init__(master, width=Metrics.INSPECTOR_WIDTH, fg_color=Palette.SURFACE_ALT)
        self._session = session
        self._interaction = interaction

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()

        session.students_changed.connect(self.refresh)
        session.constraints_changed.connect(self.refresh)
        session.classrooms_changed.connect(self.refresh)
        interaction.selection_changed.connect(lambda _student_id: self.refresh())
        interaction.tool_changed.connect(lambda _tool: self.refresh())

    # ------------------------------------------------------------------ montage

    def _build_header(self) -> None:
        header = Group(self)
        header.grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_MD, 0))
        header.grid_columnconfigure(0, weight=1)

        self._name = ctk.CTkLabel(
            header, text="", font=Fonts.heading(), text_color=Palette.TEXT, anchor="w"
        )
        self._name.grid(row=0, column=0, sticky="ew")

        # Libellé plutôt qu'un crayon : aucun glyphe de crayon ne se dessine proprement
        # à cette taille dans les polices système.
        GhostButton(
            header, "Renommer", self._rename, width=88, height=26, font=Fonts.small()
        ).grid(row=0, column=1, padx=(Metrics.PAD_SM, Metrics.PAD_XS))
        IconButton(header, Icons.CLOSE, self._interaction.clear_selection).grid(row=0, column=2)

    def _build_body(self) -> None:
        self._body = ScrollArea(self)
        self._body.grid(row=1, column=0, sticky="nsew", padx=Metrics.PAD_SM, pady=Metrics.PAD_SM)
        self._body.grid_columnconfigure(0, weight=1)

        self._tools: dict[Tool, ToolButton] = {}
        tools = Group(self._body)
        tools.pack(fill="x")
        tools.grid_columnconfigure((0, 1), weight=1, uniform="tool")
        for row_index, row_tools in enumerate(TOOL_LAYOUT):
            for column, tool in enumerate(row_tools):
                button = ToolButton(
                    tools,
                    tool.label,
                    TOOL_ACCENTS[tool],
                    lambda tool=tool: self._interaction.toggle_tool(tool),
                )
                button.grid(
                    row=row_index,
                    column=column,
                    sticky="ew",
                    padx=(0, Metrics.PAD_XS if column == 0 else 0),
                    pady=(0, Metrics.PAD_XS),
                )
                self._tools[tool] = button

        self._hint = ctk.CTkLabel(
            self._body,
            text="",
            font=Fonts.small(),
            text_color=Palette.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=Metrics.INSPECTOR_WIDTH - 60,
        )

        self._tag_chooser = Group(self._body)

        self._constraints_title = ctk.CTkLabel(
            self._body,
            text="CONTRAINTES",
            font=Fonts.small_bold(),
            text_color=Palette.TEXT_MUTED,
            anchor="w",
        )
        self._constraints = Group(self._body)

        # Ordre vertical fixé une fois pour toutes : re-`pack`er un widget masqué le
        # renverrait en fin de liste, et le choix des tags se retrouverait sous les
        # contraintes. Seul le sélecteur de tags apparaît et disparaît ensuite.
        self._hint.pack(fill="x", pady=Metrics.PAD_SM)
        self._constraints_title.pack(fill="x", pady=(Metrics.PAD_SM, Metrics.PAD_XS))
        self._constraints.pack(fill="x")

        self._delete = DangerButton(self, "Retirer l'élève", self._remove)
        self._delete.grid(row=2, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(0, Metrics.PAD_MD))

    # ------------------------------------------------------------- rafraîchissement

    def refresh(self) -> None:
        student = self._current_student()
        if student is None:
            return

        self._name.configure(text=student.name)

        active = self._interaction.active_tool
        for tool, button in self._tools.items():
            button.set_active(tool is active)

        self._refresh_hint(active)
        self._refresh_tag_chooser(active)
        self._refresh_constraints(student.id)

    def _refresh_hint(self, active: Tool | None) -> None:
        if active is None:
            self._hint.configure(
                text="Choisissez un outil, puis désignez l'élève ou le tag concerné."
            )
        else:
            self._hint.configure(text=f"{active.label} — {active.hint}")

    def _refresh_tag_chooser(self, active: Tool | None) -> None:
        for child in self._tag_chooser.winfo_children():
            child.destroy()

        if active is None or active.targets_students:
            self._tag_chooser.pack_forget()
            return

        tags = self._session.available_tags()
        if not tags:
            ctk.CTkLabel(
                self._tag_chooser,
                text="Aucun tag disponible : ajoutez-en dans la bande « Classes ».",
                font=Fonts.small(),
                text_color=Palette.TEXT_FAINT,
                anchor="w",
                justify="left",
                wraplength=Metrics.INSPECTOR_WIDTH - 60,
            ).pack(anchor="w")
        else:
            accent = TOOL_ACCENTS[active]
            for tag in tags:
                TagPill(
                    self._tag_chooser,
                    tag,
                    on_click=lambda chosen, tool=active: self._apply_tag(tool, chosen),
                    color=accent,
                    text_color=Palette.TEXT_ON_ACCENT,
                ).pack(anchor="w", pady=1)

        self._tag_chooser.pack(
            fill="x", pady=(0, Metrics.PAD_SM), before=self._constraints_title
        )

    def _refresh_constraints(self, student_id: str) -> None:
        for child in self._constraints.winfo_children():
            child.destroy()

        relations = self._session.relations_of(student_id)
        rules = self._session.tag_rules_of(student_id)

        if not relations and not rules:
            ctk.CTkLabel(
                self._constraints,
                text="Aucune contrainte pour cet élève.",
                font=Fonts.small(),
                text_color=Palette.TEXT_FAINT,
                anchor="w",
            ).pack(fill="x")
            return

        for relation in relations:
            other = self._session.student(relation.other_than(student_id))
            ConstraintChip.for_relation(
                self._constraints,
                relation,
                other.name if other else "?",
                lambda relation_id=relation.id: self._session.remove_relation(relation_id),
            ).pack(fill="x", pady=(0, Metrics.PAD_XS))

        for rule in rules:
            ConstraintChip.for_tag_rule(
                self._constraints,
                rule,
                lambda rule_id=rule.id: self._session.remove_tag_rule(rule_id),
            ).pack(fill="x", pady=(0, Metrics.PAD_XS))

    # ---------------------------------------------------------------- réactions

    def _current_student(self):
        student_id = self._interaction.selected_student_id
        return None if student_id is None else self._session.student(student_id)

    def _apply_tag(self, tool: Tool, tag: str) -> None:
        student = self._current_student()
        if student is None:
            return
        try:
            self._session.add_tag_rule(tool.tag_rule_kind, student.id, tag)
        except SessionError as error:
            NoticeDialog.inform(self, "Contrainte impossible", str(error))

    def _rename(self) -> None:
        student = self._current_student()
        if student is None:
            return

        new_name = TextPromptDialog(
            self,
            "Renommer l'élève",
            "Nom de l'élève",
            initial=student.name,
            submit_text="Renommer",
            validator=lambda value: self._validate_rename(student.id, value),
        ).show()
        if new_name:
            self._session.rename_student(student.id, new_name)

    def _validate_rename(self, student_id: str, value: str) -> str | None:
        clean = value.strip()
        if not clean:
            return "Le nom de l'élève ne peut pas être vide."
        clash = next(
            (
                other
                for other in self._session.students
                if other.id != student_id and other.name.casefold() == clean.casefold()
            ),
            None,
        )
        return f"« {clean} » figure déjà dans la liste." if clash else None

    def _remove(self) -> None:
        student = self._current_student()
        if student is None:
            return
        if not ConfirmDialog.ask(
            self,
            "Retirer l'élève",
            f"Retirer « {student.name} » de la liste ? Ses contraintes seront supprimées.",
            confirm_text="Retirer",
        ):
            return
        self._interaction.clear_selection()
        self._session.remove_student(student.id)
