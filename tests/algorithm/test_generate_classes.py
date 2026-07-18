import pytest

from auto_classes.algorithm import generate_classes
from auto_classes.core import ClassroomSet, Student
from auto_classes.rules import (
    AndConstraint,
    ClassSizeConstraint,
    PredicateConstraint,
    StudentsApart,
    StudentsTogether,
    StudentTagPresence,
)

alice = Student("Alice")
bob = Student("Bob")
carol = Student("Carol")
dan = Student("Dan")

NO_CONSTRAINT = PredicateConstraint(lambda cs: True)


def _untagged(count: int) -> list[set[str]]:
    return [set() for _ in range(count)]


def _partition(classroom_set: ClassroomSet) -> frozenset[frozenset[Student]]:
    return frozenset(frozenset(classroom.students) for classroom in classroom_set if classroom.students)


def _tagged_partition(classroom_set: ClassroomSet) -> frozenset[tuple[frozenset[Student], frozenset[str]]]:
    # contrairement à _partition, distingue deux groupes d'élèves identiques placés dans des
    # classes portant des tags différents : ce ne sont pas des doublons de symétrie.
    return frozenset(
        (frozenset(classroom.students), frozenset(classroom.tags))
        for classroom in classroom_set
        if classroom.students
    )


def test_raises_when_num_solutions_is_not_positive() -> None:
    with pytest.raises(ValueError):
        generate_classes([alice], _untagged(1), NO_CONSTRAINT, 0)


def test_respects_num_solutions_cap() -> None:
    students = [alice, bob, carol, dan]
    solutions = generate_classes(students, _untagged(2), NO_CONSTRAINT, num_solutions=2)
    assert len(solutions) == 2


def test_every_solution_places_all_students_exactly_once() -> None:
    students = [alice, bob, carol]
    solutions = generate_classes(students, _untagged(2), NO_CONSTRAINT, num_solutions=10)
    assert solutions
    for solution in solutions:
        placed = [student for classroom in solution for student in classroom]
        assert sorted(placed, key=str) == sorted(students, key=str)


def test_no_duplicate_solutions_from_classroom_symmetry() -> None:
    students = [alice, bob]
    solutions = generate_classes(students, _untagged(2), NO_CONSTRAINT, num_solutions=10)
    partitions = [_partition(solution) for solution in solutions]
    assert len(partitions) == len(set(partitions))
    # {alice, bob} ensemble, ou chacun seul : seules 2 partitions distinctes existent.
    assert len(solutions) == 2


def test_students_together_constraint_is_respected() -> None:
    students = [alice, bob, carol]
    solutions = generate_classes(students, _untagged(2), StudentsTogether(alice, bob), num_solutions=10)
    assert solutions
    for solution in solutions:
        assert solution.classroom_of(alice) is solution.classroom_of(bob)


def test_students_apart_constraint_is_respected() -> None:
    students = [alice, bob, carol]
    solutions = generate_classes(students, _untagged(2), StudentsApart(alice, bob), num_solutions=10)
    assert solutions
    for solution in solutions:
        assert solution.classroom_of(alice) is not solution.classroom_of(bob)


def test_global_class_size_constraint_is_respected() -> None:
    students = [alice, bob, carol, dan]
    constraint = ClassSizeConstraint(min_size=2, max_size=2)
    solutions = generate_classes(students, _untagged(2), constraint, num_solutions=10)
    assert solutions
    for solution in solutions:
        assert all(len(classroom) == 2 for classroom in solution)


def test_max_size_prunes_without_ever_producing_invalid_solutions() -> None:
    students = [alice, bob, carol, dan]
    constraint = ClassSizeConstraint(max_size=1)
    # 4 élèves, 2 classes de taille max 1 : insatisfaisable, ne doit jamais planter ni
    # renvoyer une solution qui dépasse max_size.
    assert generate_classes(students, _untagged(2), constraint, num_solutions=10) == []


def test_composed_and_constraint_is_respected() -> None:
    students = [alice, bob, carol, dan]
    constraint = AndConstraint(StudentsTogether(alice, bob), StudentsApart(alice, carol))
    solutions = generate_classes(students, _untagged(2), constraint, num_solutions=10)
    assert solutions
    for solution in solutions:
        assert solution.classroom_of(alice) is solution.classroom_of(bob)
        assert solution.classroom_of(alice) is not solution.classroom_of(carol)


def test_unsatisfiable_constraint_yields_no_solutions() -> None:
    students = [alice, bob]
    constraint = AndConstraint(StudentsTogether(alice, bob), StudentsApart(alice, bob))
    assert generate_classes(students, _untagged(2), constraint, num_solutions=10) == []


def test_tagged_classroom_is_available_for_student_tag_presence() -> None:
    students = [alice, bob]
    classroom_tags = [{"latin"}, set()]
    constraint = StudentTagPresence(alice, "latin", present=True)
    solutions = generate_classes(students, classroom_tags, constraint, num_solutions=10)
    assert solutions
    for solution in solutions:
        assert "latin" in solution.classroom_of(alice).tags


def test_distinctly_tagged_classrooms_are_not_merged_by_symmetry_breaking() -> None:
    students = [alice, bob]
    classroom_tags = [{"latin"}, {"grec"}]
    solutions = generate_classes(students, classroom_tags, NO_CONSTRAINT, num_solutions=10)
    # chaque classe est unique (tag différent), donc aucune restriction de symétrie ne doit
    # empêcher un élève d'être placé dans la classe "grec" (2e classe) en premier.
    tags_used = {frozenset(solution.classroom_of(student).tags) for solution in solutions for student in students}
    assert frozenset({"latin"}) in tags_used
    assert frozenset({"grec"}) in tags_used


def test_symmetry_breaking_applies_per_tag_group() -> None:
    students = [alice, bob, carol]
    # 2 classes non taguées (interchangeables entre elles) + 1 classe taguée (à part) :
    # la brise de symétrie doit s'appliquer entre les 2 classes non taguées, mais ne doit
    # pas empêcher un même regroupement d'élèves de finir dans la classe taguée séparément.
    classroom_tags = [set(), set(), {"latin"}]
    solutions = generate_classes(students, classroom_tags, NO_CONSTRAINT, num_solutions=100)
    partitions = [_tagged_partition(solution) for solution in solutions]
    assert len(partitions) == len(set(partitions))
