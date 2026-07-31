"""Briques d'interface réutilisables, sans connaissance du modèle de session."""

from auto_classes.ui.components.bindings import bind_recursive, contains_widget, set_cursor_recursive
from auto_classes.ui.components.buttons import (
    DangerButton,
    GhostButton,
    IconButton,
    PrimaryButton,
    ToolButton,
)
from auto_classes.ui.components.chips import (
    RELATION_COLORS,
    TAG_RULE_COLORS,
    ConstraintChip,
    CountBadge,
    TagPill,
)
from auto_classes.ui.components.composer import InlineComposer
from auto_classes.ui.components.dialogs import (
    ConfirmDialog,
    ModalDialog,
    NoticeDialog,
    TextPromptDialog,
)
from auto_classes.ui.components.flow_grid import FlowGrid
from auto_classes.ui.components.labels import EllipsizedLabel
from auto_classes.ui.components.surfaces import (
    ClickableCard,
    EmptyState,
    Group,
    Panel,
    ScrollArea,
    SectionHeader,
)

__all__ = [
    "bind_recursive",
    "contains_widget",
    "set_cursor_recursive",
    "GhostButton",
    "PrimaryButton",
    "DangerButton",
    "IconButton",
    "ToolButton",
    "TagPill",
    "ConstraintChip",
    "CountBadge",
    "RELATION_COLORS",
    "TAG_RULE_COLORS",
    "ModalDialog",
    "TextPromptDialog",
    "ConfirmDialog",
    "NoticeDialog",
    "FlowGrid",
    "InlineComposer",
    "EllipsizedLabel",
    "Group",
    "Panel",
    "ScrollArea",
    "SectionHeader",
    "ClickableCard",
    "EmptyState",
]
