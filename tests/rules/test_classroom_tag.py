from auto_classes.core import Classroom, ClassroomSet, Student
from auto_classes.rules.classroom_tag import StudentTagPresence

alice = Student("Alice")
carol = Student("Carol")
dan = Student("Dan")


def make_classroom_set() -> ClassroomSet:
    return ClassroomSet([Classroom([alice], tags={"latin"}), Classroom([carol], tags=set())])


def test_satisfied_when_tag_present_as_expected() -> None:
    assert StudentTagPresence(alice, "latin", present=True).is_satisfied_by(make_classroom_set())


def test_satisfied_when_tag_absent_as_expected() -> None:
    assert StudentTagPresence(carol, "latin", present=False).is_satisfied_by(make_classroom_set())


def test_not_satisfied_when_tag_missing_but_expected() -> None:
    assert not StudentTagPresence(carol, "latin", present=True).is_satisfied_by(make_classroom_set())


def test_not_satisfied_when_student_not_placed() -> None:
    assert not StudentTagPresence(dan, "latin", present=True).is_satisfied_by(make_classroom_set())
