from auto_classes.core import Classroom, ClassroomSet, Student
from auto_classes.rules.constraint import Constraint
from auto_classes.rules.student_relation import StudentsApart, StudentsTogether

alice = Student("Alice")
bob = Student("Bob")
carol = Student("Carol")


def make_classroom_set() -> ClassroomSet:
    return ClassroomSet([Classroom([alice, bob]), Classroom([carol])])


def test_students_together_satisfied_when_same_classroom() -> None:
    assert StudentsTogether(alice, bob).is_satisfied_by(make_classroom_set())


def test_students_together_not_satisfied_when_different_classroom() -> None:
    assert not StudentsTogether(alice, carol).is_satisfied_by(make_classroom_set())


def test_students_apart_satisfied_when_different_classroom() -> None:
    assert StudentsApart(alice, carol).is_satisfied_by(make_classroom_set())


def test_students_apart_not_satisfied_when_same_classroom() -> None:
    assert not StudentsApart(alice, bob).is_satisfied_by(make_classroom_set())


def test_students_together_scope_is_both_students() -> None:
    assert StudentsTogether(alice, bob).scope() == {alice, bob}


def test_students_apart_scope_is_both_students() -> None:
    assert StudentsApart(alice, bob).scope() == {alice, bob}


def test_students_together_to_dict() -> None:
    assert StudentsTogether(alice, bob).to_dict() == {
        "type": "students_together",
        "student_a": "Alice",
        "student_b": "Bob",
    }


def test_students_together_from_dict() -> None:
    constraint = Constraint.from_dict({"type": "students_together", "student_a": "Alice", "student_b": "Bob"})
    assert isinstance(constraint, StudentsTogether)
    assert constraint.student_a == alice
    assert constraint.student_b == bob


def test_students_together_dict_round_trips() -> None:
    original = StudentsTogether(alice, bob)
    assert Constraint.from_dict(original.to_dict()).to_dict() == original.to_dict()


def test_students_apart_to_dict() -> None:
    assert StudentsApart(alice, bob).to_dict() == {
        "type": "students_apart",
        "student_a": "Alice",
        "student_b": "Bob",
    }


def test_students_apart_from_dict() -> None:
    constraint = Constraint.from_dict({"type": "students_apart", "student_a": "Alice", "student_b": "Bob"})
    assert isinstance(constraint, StudentsApart)
    assert constraint.student_a == alice
    assert constraint.student_b == bob


def test_students_apart_dict_round_trips() -> None:
    original = StudentsApart(alice, bob)
    assert Constraint.from_dict(original.to_dict()).to_dict() == original.to_dict()
