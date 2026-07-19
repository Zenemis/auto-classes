from auto_classes.core import Classroom, ClassroomSet, Student
from auto_classes.rules.classroom_tag import StudentTagPresence
from auto_classes.rules.constraint import Constraint

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


def test_scope_is_the_single_student() -> None:
    assert StudentTagPresence(alice, "latin").scope() == {alice}


def test_to_dict() -> None:
    assert StudentTagPresence(alice, "latin", present=False).to_dict() == {
        "type": "student_tag_presence",
        "student": "Alice",
        "tag": "latin",
        "present": False,
    }


def test_from_dict_defaults_present_to_true() -> None:
    constraint = Constraint.from_dict({"type": "student_tag_presence", "student": "Alice", "tag": "latin"})
    assert isinstance(constraint, StudentTagPresence)
    assert constraint.student == alice
    assert constraint.tag == "latin"
    assert constraint.present is True


def test_dict_round_trips() -> None:
    original = StudentTagPresence(alice, "latin", present=False)
    assert Constraint.from_dict(original.to_dict()).to_dict() == original.to_dict()
