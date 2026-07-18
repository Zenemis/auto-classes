import pytest

from auto_classes.algorithm import generate_classes
from auto_classes.core import ClassroomSet, Student
from auto_classes.rules import (
    AndConstraint,
    ClassSizeConstraint,
    PredicateConstraint,
    StudentsApart,
    StudentsTogether,
)

alice = Student("Alice")
bob = Student("Bob")
carol = Student("Carol")
dan = Student("Dan")

NO_CONSTRAINT = PredicateConstraint(lambda cs: True)


def _partition(classroom_set: ClassroomSet) -> frozenset[frozenset[Student]]:
    return frozenset(frozenset(classroom.students) for classroom in classroom_set if classroom.students)


def test_raises_when_num_solutions_is_not_positive() -> None:
    with pytest.raises(ValueError):
        generate_classes([alice], 1, NO_CONSTRAINT, 0)


def test_respects_num_solutions_cap() -> None:
    students = [alice, bob, carol, dan]
    solutions = generate_classes(students, 2, NO_CONSTRAINT, num_solutions=2)
    assert len(solutions) == 2


def test_every_solution_places_all_students_exactly_once() -> None:
    students = [alice, bob, carol]
    solutions = generate_classes(students, 2, NO_CONSTRAINT, num_solutions=10)
    assert solutions
    for solution in solutions:
        placed = [student for classroom in solution for student in classroom]
        assert sorted(placed, key=str) == sorted(students, key=str)


def test_no_duplicate_solutions_from_classroom_symmetry() -> None:
    students = [alice, bob]
    solutions = generate_classes(students, 2, NO_CONSTRAINT, num_solutions=10)
    partitions = [_partition(solution) for solution in solutions]
    assert len(partitions) == len(set(partitions))
    # {alice, bob} ensemble, ou chacun seul : seules 2 partitions distinctes existent.
    assert len(solutions) == 2


def test_students_together_constraint_is_respected() -> None:
    students = [alice, bob, carol]
    solutions = generate_classes(students, 2, StudentsTogether(alice, bob), num_solutions=10)
    assert solutions
    for solution in solutions:
        assert solution.classroom_of(alice) is solution.classroom_of(bob)


def test_students_apart_constraint_is_respected() -> None:
    students = [alice, bob, carol]
    solutions = generate_classes(students, 2, StudentsApart(alice, bob), num_solutions=10)
    assert solutions
    for solution in solutions:
        assert solution.classroom_of(alice) is not solution.classroom_of(bob)


def test_global_class_size_constraint_is_respected() -> None:
    students = [alice, bob, carol, dan]
    solutions = generate_classes(students, 2, ClassSizeConstraint(min_size=2, max_size=2), num_solutions=10)
    assert solutions
    for solution in solutions:
        assert all(len(classroom) == 2 for classroom in solution)


def test_composed_and_constraint_is_respected() -> None:
    students = [alice, bob, carol, dan]
    constraint = AndConstraint(StudentsTogether(alice, bob), StudentsApart(alice, carol))
    solutions = generate_classes(students, 2, constraint, num_solutions=10)
    assert solutions
    for solution in solutions:
        assert solution.classroom_of(alice) is solution.classroom_of(bob)
        assert solution.classroom_of(alice) is not solution.classroom_of(carol)


def test_unsatisfiable_constraint_yields_no_solutions() -> None:
    students = [alice, bob]
    constraint = AndConstraint(StudentsTogether(alice, bob), StudentsApart(alice, bob))
    assert generate_classes(students, 2, constraint, num_solutions=10) == []
