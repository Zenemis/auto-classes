from auto_classes.core import Classroom, ClassroomSet, Student
from auto_classes.rules.classroom_invariant import ClassSizeConstraint
from auto_classes.rules.constraint import Constraint

alice = Student("Alice")
bob = Student("Bob")
carol = Student("Carol")


def make_classroom_set() -> ClassroomSet:
    return ClassroomSet([Classroom([alice, bob]), Classroom([carol])])


def test_satisfied_when_sizes_within_bounds() -> None:
    assert ClassSizeConstraint(min_size=1, max_size=2).is_satisfied_by(make_classroom_set())


def test_not_satisfied_when_below_min_size() -> None:
    assert not ClassSizeConstraint(min_size=2).is_satisfied_by(make_classroom_set())


def test_not_satisfied_when_above_max_size() -> None:
    assert not ClassSizeConstraint(max_size=1).is_satisfied_by(make_classroom_set())


def test_satisfied_when_no_bounds_given() -> None:
    assert ClassSizeConstraint().is_satisfied_by(make_classroom_set())


def test_scope_is_global() -> None:
    assert ClassSizeConstraint(min_size=1).scope() is None


def test_still_satisfiable_when_within_max_size() -> None:
    assert ClassSizeConstraint(max_size=2).is_still_satisfiable(make_classroom_set())


def test_not_still_satisfiable_when_above_max_size() -> None:
    assert not ClassSizeConstraint(max_size=1).is_still_satisfiable(make_classroom_set())


def test_still_satisfiable_when_below_min_size_since_more_students_may_come() -> None:
    assert ClassSizeConstraint(min_size=5).is_still_satisfiable(make_classroom_set())


def test_still_satisfiable_when_no_max_size_given() -> None:
    assert ClassSizeConstraint(min_size=1).is_still_satisfiable(make_classroom_set())


def test_to_dict() -> None:
    assert ClassSizeConstraint(min_size=20, max_size=25).to_dict() == {
        "type": "class_size",
        "min_size": 20,
        "max_size": 25,
    }


def test_to_dict_with_no_bounds() -> None:
    assert ClassSizeConstraint().to_dict() == {"type": "class_size", "min_size": None, "max_size": None}


def test_from_dict() -> None:
    constraint = Constraint.from_dict({"type": "class_size", "min_size": 20, "max_size": None})
    assert isinstance(constraint, ClassSizeConstraint)
    assert constraint.min_size == 20
    assert constraint.max_size is None


def test_dict_round_trips() -> None:
    original = ClassSizeConstraint(min_size=10, max_size=30)
    assert Constraint.from_dict(original.to_dict()).to_dict() == original.to_dict()
