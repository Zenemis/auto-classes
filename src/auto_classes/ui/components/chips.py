"""Étiquettes compactes : options de classe et contraintes d'un élève."""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

from auto_classes.ui.components.bindings import bind_recursive, set_cursor_recursive
from auto_classes.ui.components.buttons import IconButton
from auto_classes.ui.models import RelationKind, StudentRelation, TagRule, TagRuleKind
from auto_classes.ui.theme import Color, Fonts, Icons, Metrics, Palette

RELATION_COLORS: dict[RelationKind, Color] = {
    RelationKind.TOGETHER: Palette.TOGETHER,
    RelationKind.APART: Palette.APART,
}

TAG_RULE_COLORS: dict[TagRuleKind, Color] = {
    TagRuleKind.INCLUDE: Palette.INCLUDE,
    TagRuleKind.EXCLUDE: Palette.EXCLUDE,
}


class TagPill(ctk.CTkFrame):
    """Option de classe. Cliquable (choix d'une option) et/ou supprimable (édition d'une classe).

    `outlined` sert aux tags proposés mais pas encore posés : pleine, la pastille dit
    « contrainte active, un clic la retire » ; en contour, « un clic la pose ».
    """

    def __init__(
        self,
        master: tk.Misc,
        tag: str,
        *,
        on_click: Callable[[str], None] | None = None,
        on_remove: Callable[[str], None] | None = None,
        color: Color = Palette.SURFACE_ALT,
        text_color: Color = Palette.TEXT_MUTED,
        outlined: bool = False,
    ) -> None:
        super().__init__(
            master,
            fg_color="transparent" if outlined else color,
            border_width=1 if outlined else 0,
            border_color=color,
            corner_radius=Metrics.RADIUS_PILL,
            height=22,
        )
        if outlined:
            text_color = color

        self.tag = tag
        ctk.CTkLabel(self, text=tag, font=Fonts.small(), text_color=text_color).pack(
            side="left", padx=(Metrics.PAD_SM, Metrics.PAD_SM if on_remove is None else 2), pady=1
        )

        if on_remove is not None:
            IconButton(
                self,
                Icons.CLOSE,
                lambda: on_remove(tag),
                size=18,
                text_color=text_color,
            ).pack(side="left", padx=(0, 3))

        if on_click is not None:
            bind_recursive(self, "<Button-1>", lambda _event: on_click(tag))
            set_cursor_recursive(self, "hand2")


class ConstraintChip(ctk.CTkFrame):
    """Contrainte d'un élève : point coloré, libellé, et croix de suppression."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        accent: Color,
        on_remove: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            master,
            fg_color=Palette.SURFACE_ALT,
            corner_radius=Metrics.RADIUS_SM,
            border_width=1,
            border_color=Palette.BORDER,
        )
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=Icons.DOT, font=Fonts.small(), text_color=accent, width=12).grid(
            row=0, column=0, padx=(Metrics.PAD_SM, 0), pady=Metrics.PAD_XS
        )
        ctk.CTkLabel(self, text=text, font=Fonts.small(), text_color=Palette.TEXT, anchor="w").grid(
            row=0, column=1, sticky="ew", padx=(Metrics.PAD_XS, 0)
        )
        if on_remove is not None:
            IconButton(self, Icons.CLOSE, on_remove, size=20).grid(
                row=0, column=2, padx=(0, Metrics.PAD_XS), pady=2
            )

    @classmethod
    def for_relation(
        cls,
        master: tk.Misc,
        relation: StudentRelation,
        other_name: str,
        on_remove: Callable[[], None] | None = None,
    ) -> "ConstraintChip":
        return cls(master, relation.kind.describe(other_name), RELATION_COLORS[relation.kind], on_remove)

    @classmethod
    def for_tag_rule(
        cls,
        master: tk.Misc,
        rule: TagRule,
        on_remove: Callable[[], None] | None = None,
    ) -> "ConstraintChip":
        return cls(master, rule.kind.describe(rule.tag), TAG_RULE_COLORS[rule.kind], on_remove)


class CountBadge(ctk.CTkLabel):
    """Pastille colorée signalant les contraintes d'un type sur une tuile d'élève.

    Le nombre n'est affiché qu'à partir de deux : sur une tuile étroite, « ● » suffit à
    dire « il y en a une », et quatre pastilles chiffrées ne tiendraient pas.
    """

    def __init__(self, master: tk.Misc, count: int, accent: Color) -> None:
        super().__init__(
            master,
            text=Icons.DOT if count < 2 else f"{Icons.DOT}{count}",
            font=Fonts.small_bold(),
            text_color=accent,
        )
