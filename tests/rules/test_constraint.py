from auto_classes.core import ClassroomSet
from auto_classes.rules.constraint import (
    AndConstraint,
    Constraint,
    NotConstraint,
    OrConstraint,
    PredicateConstraint,
)

EMPTY_SET = ClassroomSet([])


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
