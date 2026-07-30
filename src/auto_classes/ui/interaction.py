"""État d'interaction de l'onglet Configuration : élève sélectionné et outil armé.

Séparé de `SessionState` : ici rien n'est une donnée métier, seulement « où en est
l'utilisateur ». Le panneau des élèves et l'inspecteur communiquent uniquement à travers
cet objet — l'un arme un outil, l'autre réagit aux clics.
"""

from enum import Enum

from auto_classes.ui.models import RelationKind, TagRuleKind
from auto_classes.ui.signal import Signal


class Tool(Enum):
    """Outil de création de contraintes armé dans l'inspecteur."""

    APART = "apart"
    TOGETHER = "together"
    EXCLUDE = "exclude"
    INCLUDE = "include"

    @property
    def label(self) -> str:
        return {
            Tool.APART: "Séparer de",
            Tool.TOGETHER: "Mettre avec",
            Tool.EXCLUDE: "Exclu de",
            Tool.INCLUDE: "Inclus dans",
        }[self]

    @property
    def targets_students(self) -> bool:
        """Vrai si l'outil se complète en cliquant un autre élève, faux s'il visait un tag."""
        return self in (Tool.APART, Tool.TOGETHER)

    @property
    def hint(self) -> str:
        if self.targets_students:
            return "Cliquez un autre élève dans la liste pour créer la contrainte."
        return "Choisissez un tag de classe ci-dessous."

    @property
    def relation_kind(self) -> RelationKind:
        if not self.targets_students:
            raise ValueError(f"{self} ne produit pas de relation entre élèves")
        return RelationKind.APART if self is Tool.APART else RelationKind.TOGETHER

    @property
    def tag_rule_kind(self) -> TagRuleKind:
        if self.targets_students:
            raise ValueError(f"{self} ne produit pas de règle de tag")
        return TagRuleKind.EXCLUDE if self is Tool.EXCLUDE else TagRuleKind.INCLUDE


class InteractionState:
    """Sélection courante et outil armé."""

    def __init__(self) -> None:
        self._selected_student_id: str | None = None
        self._active_tool: Tool | None = None

        self.selection_changed = Signal("selection_changed")
        self.tool_changed = Signal("tool_changed")

    @property
    def selected_student_id(self) -> str | None:
        return self._selected_student_id

    @property
    def active_tool(self) -> Tool | None:
        return self._active_tool

    def select_student(self, student_id: str | None) -> None:
        """Sélectionner un autre élève désarme l'outil : un outil appartient à un élève."""
        if student_id == self._selected_student_id:
            return
        self._selected_student_id = student_id
        self.set_tool(None)
        self.selection_changed.emit(student_id)

    def clear_selection(self) -> None:
        self.select_student(None)

    def set_tool(self, tool: Tool | None) -> None:
        if tool is not None and self._selected_student_id is None:
            return
        if tool == self._active_tool:
            return
        self._active_tool = tool
        self.tool_changed.emit(tool)

    def toggle_tool(self, tool: Tool) -> None:
        self.set_tool(None if tool == self._active_tool else tool)
