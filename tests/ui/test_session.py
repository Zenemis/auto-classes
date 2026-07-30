import pytest

from auto_classes.rules import (
    ClassSizeConstraint,
    StudentsApart,
    StudentsTogether,
    StudentTagPresence,
)
from auto_classes.ui.models import RelationKind, TagRuleKind
from auto_classes.ui.session import SessionError, SessionState


@pytest.fixture
def session() -> SessionState:
    return SessionState()


def _flatten(constraint):
    return list(constraint.constraints)


# ------------------------------------------------------------------------ élèves


def test_add_student_trims_and_returns_model(session):
    student = session.add_student("  Alice  ")
    assert student.name == "Alice"
    assert session.students == [student]


def test_add_student_rejects_empty_name(session):
    with pytest.raises(SessionError):
        session.add_student("   ")


def test_add_student_rejects_duplicate_regardless_of_case(session):
    session.add_student("Alice")
    with pytest.raises(SessionError):
        session.add_student("alice")


def test_students_are_sorted_by_name(session):
    session.add_student("Zoé")
    session.add_student("Alice")
    assert [student.name for student in session.students] == ["Alice", "Zoé"]


def test_add_students_keeps_the_valid_ones_and_reports_the_rest(session):
    session.add_student("Alice")
    added, problems = session.add_students(["Bob", "Alice", "Carole"])
    assert [student.name for student in added] == ["Bob", "Carole"]
    assert len(problems) == 1


def test_rename_student_accepts_its_own_name(session):
    student = session.add_student("Alice")
    session.rename_student(student.id, "Alice")
    assert student.name == "Alice"


def test_rename_student_rejects_another_student_name(session):
    session.add_student("Alice")
    bob = session.add_student("Bob")
    with pytest.raises(SessionError):
        session.rename_student(bob.id, "Alice")


def test_remove_student_prunes_its_constraints(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, tags={"latin"})
    alice = session.add_student("Alice")
    bob = session.add_student("Bob")
    session.add_relation(RelationKind.APART, alice.id, bob.id)
    session.add_tag_rule(TagRuleKind.INCLUDE, alice.id, "latin")

    session.remove_student(alice.id)

    assert session.relations == []
    assert session.tag_rules == []


# ------------------------------------------------------------------------ classes


def test_add_classroom_generates_a_unique_default_name(session):
    first = session.add_classroom()
    second = session.add_classroom()
    assert first.name != second.name


def test_add_classroom_rejects_duplicate_name(session):
    session.add_classroom("6e A")
    with pytest.raises(SessionError):
        session.add_classroom("6e a")


def test_update_classroom_only_touches_the_given_fields(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, min_size=2, max_size=4, tags={"latin"})
    session.update_classroom(classroom.id, name="6e B")

    assert (classroom.name, classroom.min_size, classroom.max_size) == ("6e B", 2, 4)
    assert classroom.tags == {"latin"}


def test_update_classroom_rejects_min_above_max(session):
    classroom = session.add_classroom("6e A")
    with pytest.raises(SessionError):
        session.update_classroom(classroom.id, min_size=5, max_size=3)


def test_update_classroom_drops_blank_tags(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, tags={"latin", "  ", ""})
    assert classroom.tags == {"latin"}


def test_available_tags_is_the_sorted_union(session):
    first = session.add_classroom("6e A")
    second = session.add_classroom("6e B")
    session.update_classroom(first.id, tags={"latin"})
    session.update_classroom(second.id, tags={"bilangue", "latin"})
    assert session.available_tags() == ["bilangue", "latin"]


def test_removing_the_last_classroom_carrying_a_tag_prunes_its_rules(session):
    first = session.add_classroom("6e A")
    second = session.add_classroom("6e B")
    session.update_classroom(first.id, tags={"latin"})
    session.update_classroom(second.id, tags={"latin"})
    alice = session.add_student("Alice")
    session.add_tag_rule(TagRuleKind.INCLUDE, alice.id, "latin")

    session.remove_classroom(first.id)
    assert len(session.tag_rules) == 1  # "latin" existe encore via 6e B

    session.remove_classroom(second.id)
    assert session.tag_rules == []


# -------------------------------------------------------------------- contraintes


def test_add_relation_is_idempotent_for_the_same_pair_and_kind(session):
    alice = session.add_student("Alice")
    bob = session.add_student("Bob")
    first = session.add_relation(RelationKind.APART, alice.id, bob.id)
    second = session.add_relation(RelationKind.APART, bob.id, alice.id)
    assert first is second
    assert len(session.relations) == 1


def test_add_relation_replaces_the_opposite_kind(session):
    alice = session.add_student("Alice")
    bob = session.add_student("Bob")
    session.add_relation(RelationKind.APART, alice.id, bob.id)
    session.add_relation(RelationKind.TOGETHER, alice.id, bob.id)

    assert len(session.relations) == 1
    assert session.relations[0].kind is RelationKind.TOGETHER


def test_add_relation_rejects_a_student_with_itself(session):
    alice = session.add_student("Alice")
    with pytest.raises(SessionError):
        session.add_relation(RelationKind.APART, alice.id, alice.id)


def test_add_tag_rule_replaces_the_opposite_kind(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, tags={"latin"})
    alice = session.add_student("Alice")
    session.add_tag_rule(TagRuleKind.EXCLUDE, alice.id, "latin")
    session.add_tag_rule(TagRuleKind.INCLUDE, alice.id, "latin")

    assert len(session.tag_rules) == 1
    assert session.tag_rules[0].kind is TagRuleKind.INCLUDE


def test_constraint_count_of_sums_both_families(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, tags={"latin"})
    alice = session.add_student("Alice")
    bob = session.add_student("Bob")
    session.add_relation(RelationKind.APART, alice.id, bob.id)
    session.add_tag_rule(TagRuleKind.INCLUDE, alice.id, "latin")

    assert session.constraint_count_of(alice.id) == 2
    assert session.constraint_count_of(bob.id) == 1


# ---------------------------------------------------------------- vers le backend


def test_build_constraint_is_empty_without_any_rule(session):
    session.add_classroom("6e A")
    session.add_student("Alice")
    assert _flatten(session.build_constraint()) == []


def test_build_constraint_emits_one_constraint_per_rule(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, min_size=1, max_size=4, tags={"latin"})
    alice = session.add_student("Alice")
    bob = session.add_student("Bob")
    carole = session.add_student("Carole")
    session.add_relation(RelationKind.TOGETHER, alice.id, bob.id)
    session.add_relation(RelationKind.APART, alice.id, carole.id)
    session.add_tag_rule(TagRuleKind.INCLUDE, alice.id, "latin")
    session.add_tag_rule(TagRuleKind.EXCLUDE, bob.id, "latin")

    parts = _flatten(session.build_constraint())
    kinds = [type(part) for part in parts]

    assert kinds.count(ClassSizeConstraint) == 1
    assert kinds.count(StudentsTogether) == 1
    assert kinds.count(StudentsApart) == 1
    assert kinds.count(StudentTagPresence) == 2

    presences = {part.student.name: part.present for part in parts if isinstance(part, StudentTagPresence)}
    assert presences == {"Alice": True, "Bob": False}


def test_build_constraint_skips_classrooms_without_size_rule(session):
    session.add_classroom("6e A")
    constrained = session.add_classroom("6e B")
    session.update_classroom(constrained.id, max_size=3)

    sizes = [part for part in _flatten(session.build_constraint()) if isinstance(part, ClassSizeConstraint)]
    assert [part.classroom_name for part in sizes] == ["6e B"]


def test_build_constraint_follows_renames(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, max_size=3)
    session.update_classroom(classroom.id, name="6e A latin")

    size = _flatten(session.build_constraint())[0]
    assert size.classroom_name == "6e A latin"
    assert session.core_classrooms()[0].name == "6e A latin"


def test_core_students_are_backend_students_in_display_order(session):
    session.add_student("Zoé")
    session.add_student("Alice")
    assert [student.name for student in session.core_students()] == ["Alice", "Zoé"]


# ----------------------------------------------------------------------- validation


def test_validate_requires_students_and_classrooms(session):
    assert len(session.validate()) == 2


def test_validate_accepts_a_workable_session(session):
    session.add_classroom("6e A")
    session.add_student("Alice")
    assert session.validate() == []


def test_validate_detects_insufficient_capacity(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, max_size=1)
    session.add_students(["Alice", "Bob"])

    assert any("trop bas" in problem for problem in session.validate())


def test_validate_ignores_capacity_when_a_classroom_is_unbounded(session):
    bounded = session.add_classroom("6e A")
    session.update_classroom(bounded.id, max_size=1)
    session.add_classroom("6e B")
    session.add_students(["Alice", "Bob", "Carole"])

    assert session.validate() == []


def test_validate_detects_excessive_minimums(session):
    classroom = session.add_classroom("6e A")
    session.update_classroom(classroom.id, min_size=5)
    session.add_student("Alice")

    assert any("trop hauts" in problem for problem in session.validate())


def test_num_solutions_never_drops_below_one(session):
    session.num_solutions = 0
    assert session.num_solutions == 1


# -------------------------------------------------------------------------- signaux


def test_signals_fire_on_the_matching_change(session):
    seen: list[str] = []
    session.students_changed.connect(lambda: seen.append("students"))
    session.classrooms_changed.connect(lambda: seen.append("classrooms"))
    session.constraints_changed.connect(lambda: seen.append("constraints"))

    classroom = session.add_classroom("6e A")
    alice = session.add_student("Alice")
    bob = session.add_student("Bob")
    session.add_relation(RelationKind.APART, alice.id, bob.id)
    session.update_classroom(classroom.id, max_size=2)

    assert seen == ["classrooms", "students", "students", "constraints", "classrooms"]
