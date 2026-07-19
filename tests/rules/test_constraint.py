import pytest

from auto_classes.core import ClassroomSet, Student
from auto_classes.rules.classroom_invariant import ClassSizeConstraint
from auto_classes.rules.constraint import (
    AndConstraint,
    Constraint,
    NotConstraint,
    OrConstraint,
    PredicateConstraint,
)
from auto_classes.rules.student_relation import StudentsApart, StudentsTogether

EMPTY_SET = ClassroomSet([])
alice = Student("Alice")
bob = Student("Bob")


class AlwaysTrue(Constraint):
    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return True


class AlwaysFalse(Constraint):
    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return False


def test_and_constraint_is_satisfied_only_when_all_are() -> None:
    assert AndConstraint(AlwaysTrue(), AlwaysTrue()).is_satisfied_by(EMPTY_SET)
    assert not AndConstraint(AlwaysTrue(), AlwaysFalse()).is_satisfied_by(EMPTY_SET)


def test_or_constraint_is_satisfied_when_any_is() -> None:
    assert OrConstraint(AlwaysFalse(), AlwaysTrue()).is_satisfied_by(EMPTY_SET)
    assert not OrConstraint(AlwaysFalse(), AlwaysFalse()).is_satisfied_by(EMPTY_SET)


def test_not_constraint_negates() -> None:
    assert NotConstraint(AlwaysFalse()).is_satisfied_by(EMPTY_SET)
    assert not NotConstraint(AlwaysTrue()).is_satisfied_by(EMPTY_SET)


def test_and_operator_overload() -> None:
    assert (AlwaysTrue() & AlwaysTrue()).is_satisfied_by(EMPTY_SET)
    assert not (AlwaysTrue() & AlwaysFalse()).is_satisfied_by(EMPTY_SET)


def test_or_operator_overload() -> None:
    assert (AlwaysFalse() | AlwaysTrue()).is_satisfied_by(EMPTY_SET)


def test_invert_operator_overload() -> None:
    assert (~AlwaysFalse()).is_satisfied_by(EMPTY_SET)


def test_predicate_constraint_wraps_function() -> None:
    constraint = PredicateConstraint(lambda cs: len(cs) == 0)
    assert constraint.is_satisfied_by(EMPTY_SET)


def test_default_scope_is_global() -> None:
    assert AlwaysTrue().scope() is None


def test_and_scope_merges_children_scopes() -> None:
    class ScopedOnAlice(Constraint):
        def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
            return True

        def scope(self):
            return {"alice"}

    class ScopedOnBob(Constraint):
        def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
            return True

        def scope(self):
            return {"bob"}

    assert AndConstraint(ScopedOnAlice(), ScopedOnBob()).scope() == {"alice", "bob"}
    assert OrConstraint(ScopedOnAlice(), ScopedOnBob()).scope() == {"alice", "bob"}


def test_composite_scope_is_global_when_any_child_is() -> None:
    class ScopedOnAlice(Constraint):
        def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
            return True

        def scope(self):
            return {"alice"}

    assert AndConstraint(ScopedOnAlice(), AlwaysTrue()).scope() is None


def test_not_scope_delegates_to_wrapped_constraint() -> None:
    class ScopedOnAlice(Constraint):
        def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
            return True

        def scope(self):
            return {"alice"}

    assert NotConstraint(ScopedOnAlice()).scope() == {"alice"}


def test_default_is_still_satisfiable_is_true() -> None:
    assert AlwaysFalse().is_still_satisfiable(EMPTY_SET)


def test_and_is_still_satisfiable_only_when_all_are() -> None:
    class NeverSatisfiable(Constraint):
        def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
            return False

        def is_still_satisfiable(self, classroom_set: ClassroomSet) -> bool:
            return False

    assert AndConstraint(AlwaysTrue(), AlwaysFalse()).is_still_satisfiable(EMPTY_SET)
    assert not AndConstraint(AlwaysTrue(), NeverSatisfiable()).is_still_satisfiable(EMPTY_SET)


def test_and_to_dict_nests_children() -> None:
    assert AndConstraint(StudentsTogether(alice, bob), ClassSizeConstraint(max_size=25)).to_dict() == {
        "type": "and",
        "constraints": [
            {"type": "students_together", "student_a": "Alice", "student_b": "Bob"},
            {"type": "class_size", "min_size": None, "max_size": 25},
        ],
    }


def test_and_from_dict_nests_children() -> None:
    constraint = Constraint.from_dict(
        {
            "type": "and",
            "constraints": [
                {"type": "students_together", "student_a": "Alice", "student_b": "Bob"},
                {"type": "class_size", "min_size": None, "max_size": 25},
            ],
        }
    )
    assert isinstance(constraint, AndConstraint)
    assert len(constraint.constraints) == 2
    assert isinstance(constraint.constraints[0], StudentsTogether)
    assert isinstance(constraint.constraints[1], ClassSizeConstraint)


def test_or_to_dict_nests_children() -> None:
    dumped = OrConstraint(StudentsTogether(alice, bob), StudentsApart(alice, bob)).to_dict()
    assert dumped == {
        "type": "or",
        "constraints": [
            {"type": "students_together", "student_a": "Alice", "student_b": "Bob"},
            {"type": "students_apart", "student_a": "Alice", "student_b": "Bob"},
        ],
    }


def test_or_from_dict_nests_children() -> None:
    constraint = Constraint.from_dict(
        {
            "type": "or",
            "constraints": [
                {"type": "students_together", "student_a": "Alice", "student_b": "Bob"},
                {"type": "students_apart", "student_a": "Alice", "student_b": "Bob"},
            ],
        }
    )
    assert isinstance(constraint, OrConstraint)


def test_not_to_dict_wraps_child() -> None:
    assert NotConstraint(StudentsTogether(alice, bob)).to_dict() == {
        "type": "not",
        "constraint": {"type": "students_together", "student_a": "Alice", "student_b": "Bob"},
    }


def test_not_from_dict_wraps_child() -> None:
    constraint = Constraint.from_dict(
        {"type": "not", "constraint": {"type": "students_together", "student_a": "Alice", "student_b": "Bob"}}
    )
    assert isinstance(constraint, NotConstraint)
    assert isinstance(constraint.constraint, StudentsTogether)


def test_dict_round_trips_nested_tree() -> None:
    original = AndConstraint(
        OrConstraint(StudentsTogether(alice, bob), StudentsApart(alice, bob)),
        NotConstraint(StudentsApart(alice, bob)),
        ClassSizeConstraint(min_size=10, max_size=30),
    )
    assert Constraint.from_dict(original.to_dict()).to_dict() == original.to_dict()


def test_to_dict_default_raises_for_non_serializable_constraint() -> None:
    with pytest.raises(TypeError):
        AlwaysTrue().to_dict()


def test_predicate_constraint_to_dict_raises() -> None:
    with pytest.raises(TypeError):
        PredicateConstraint(lambda cs: True).to_dict()


def test_from_dict_raises_for_unknown_type() -> None:
    with pytest.raises(ValueError):
        Constraint.from_dict({"type": "some_future_constraint"})
