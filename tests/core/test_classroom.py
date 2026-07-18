from auto_classes.core.classroom import Classroom
from auto_classes.core.student import Student

alice = Student("Alice")
bob = Student("Bob")


def test_len_returns_number_of_students() -> None:
    assert len(Classroom([alice, bob])) == 2


def test_contains_checks_student_membership() -> None:
    classroom = Classroom([alice])
    assert alice in classroom
    assert bob not in classroom


def test_iter_yields_students() -> None:
    classroom = Classroom([alice, bob])
    assert list(classroom) == [alice, bob]


def test_default_tags_is_empty() -> None:
    assert Classroom([alice]).tags == set()
