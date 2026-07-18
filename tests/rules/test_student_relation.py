from auto_classes.core import Classroom, ClassroomSet, Student
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
