import pytest

from auto_classes.ui.interaction import InteractionState, Tool
from auto_classes.ui.models import RelationKind, TagRuleKind


@pytest.fixture
def interaction() -> InteractionState:
    return InteractionState()


def test_starts_empty(interaction):
    assert interaction.selected_student_id is None
    assert interaction.active_tool is None


def test_select_student_emits_once(interaction):
    seen: list[str | None] = []
    interaction.selection_changed.connect(seen.append)

    interaction.select_student("student-1")
    interaction.select_student("student-1")

    assert seen == ["student-1"]


def test_a_tool_needs_a_selected_student(interaction):
    interaction.set_tool(Tool.APART)
    assert interaction.active_tool is None


def test_changing_student_disarms_the_tool(interaction):
    interaction.select_student("student-1")
    interaction.set_tool(Tool.APART)

    interaction.select_student("student-2")

    assert interaction.active_tool is None


def test_clear_selection_disarms_the_tool(interaction):
    interaction.select_student("student-1")
    interaction.set_tool(Tool.TOGETHER)

    interaction.clear_selection()

    assert interaction.selected_student_id is None
    assert interaction.active_tool is None


def test_toggle_tool_arms_then_disarms(interaction):
    interaction.select_student("student-1")

    interaction.toggle_tool(Tool.EXCLUDE)
    assert interaction.active_tool is Tool.EXCLUDE

    interaction.toggle_tool(Tool.EXCLUDE)
    assert interaction.active_tool is None


def test_toggle_tool_switches_between_tools(interaction):
    interaction.select_student("student-1")
    interaction.toggle_tool(Tool.EXCLUDE)
    interaction.toggle_tool(Tool.INCLUDE)
    assert interaction.active_tool is Tool.INCLUDE


def test_tool_changed_emits_only_on_change(interaction):
    seen: list[Tool | None] = []
    interaction.tool_changed.connect(seen.append)

    interaction.select_student("student-1")
    interaction.set_tool(Tool.APART)
    interaction.set_tool(Tool.APART)
    interaction.set_tool(None)

    assert seen == [Tool.APART, None]


@pytest.mark.parametrize(
    ("tool", "targets_students"),
    [(Tool.APART, True), (Tool.TOGETHER, True), (Tool.EXCLUDE, False), (Tool.INCLUDE, False)],
)
def test_targets_students(tool, targets_students):
    assert tool.targets_students is targets_students


@pytest.mark.parametrize(
    ("tool", "kind"),
    [(Tool.APART, RelationKind.APART), (Tool.TOGETHER, RelationKind.TOGETHER)],
)
def test_relation_kind_mapping(tool, kind):
    assert tool.relation_kind is kind


@pytest.mark.parametrize(
    ("tool", "kind"),
    [(Tool.EXCLUDE, TagRuleKind.EXCLUDE), (Tool.INCLUDE, TagRuleKind.INCLUDE)],
)
def test_tag_rule_kind_mapping(tool, kind):
    assert tool.tag_rule_kind is kind


def test_relation_kind_is_refused_for_tag_tools():
    with pytest.raises(ValueError):
        Tool.INCLUDE.relation_kind


def test_tag_rule_kind_is_refused_for_student_tools():
    with pytest.raises(ValueError):
        Tool.APART.tag_rule_kind
