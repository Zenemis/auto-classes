"""Tuile d'un élève dans la liste : nom, compteurs de contraintes, états visuels."""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components import ClickableCard, CountBadge, Group
from auto_classes.ui.components.chips import RELATION_COLORS, TAG_RULE_COLORS
from auto_classes.ui.models import RelationKind, StudentModel, TagRuleKind
from auto_classes.ui.session import SessionState
from auto_classes.ui.theme import Fonts, Metrics, Palette


class StudentTile(ClickableCard):
    """Une tuile par élève, réutilisée d'un rafraîchissement à l'autre.

    Reconstruire toutes les tuiles à chaque ajout de contrainte serait perceptible sur
    une centaine d'élèves : `refresh` remet à jour le contenu sans recréer le widget.
    """

    def __init__(
        self,
        master: tk.Misc,
        student: StudentModel,
        session: SessionState,
        on_click: Callable[[str], None],
    ) -> None:
        super().__init__(master, on_click=lambda: on_click(student.id))

        self.student_id = student.id
        self._session = session
        self.grid_columnconfigure(0, weight=1)

        self._name = ctk.CTkLabel(
            self, text=student.name, font=Fonts.body_bold(), text_color=Palette.TEXT, anchor="w"
        )
        self._name.grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_SM, 0))

        self._badges = Group(self)
        self._badges.grid(row=1, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(2, Metrics.PAD_SM))

        # Bindings d'abord, contenu ensuite : `refresh` ne rebinde que la zone des badges.
        self.activate()
        self.refresh()

    def refresh(self) -> None:
        student = self._session.student(self.student_id)
        if student is None:
            return

        self._name.configure(text=student.name)
        for child in self._badges.winfo_children():
            child.destroy()

        counts: list[tuple[int, object]] = []
        relations = self._session.relations_of(self.student_id)
        for kind in RelationKind:
            total = sum(1 for relation in relations if relation.kind is kind)
            if total:
                counts.append((total, RELATION_COLORS[kind]))

        rules = self._session.tag_rules_of(self.student_id)
        for tag_kind in TagRuleKind:
            total = sum(1 for rule in rules if rule.kind is tag_kind)
            if total:
                counts.append((total, TAG_RULE_COLORS[tag_kind]))

        if not counts:
            ctk.CTkLabel(
                self._badges,
                text="Aucune contrainte",
                font=Fonts.small(),
                text_color=Palette.TEXT_FAINT,
            ).pack(side="left")
        else:
            for total, accent in counts:
                CountBadge(self._badges, total, accent).pack(  # type: ignore[arg-type]
                    side="left", padx=(0, Metrics.PAD_SM)
                )

        self.activate(self._badges)
