from auto_classes.core.classroom import Classroom
from auto_classes.core.classroom_set import ClassroomSet
from auto_classes.core.student import Student

alice = Student("Alice")
bob = Student("Bob")
carol = Student("Carol")


def test_len_returns_number_of_classrooms() -> None:
    classroom_set = ClassroomSet([Classroom([alice]), Classroom([bob])])
    assert len(classroom_set) == 2


def test_iter_yields_classrooms() -> None:
    classroom_a = Classroom([alice])
    classroom_b = Classroom([bob])
    classroom_set = ClassroomSet([classroom_a, classroom_b])
    assert list(classroom_set) == [classroom_a, classroom_b]


def test_classroom_of_returns_containing_classroom() -> None:
    classroom_a = Classroom([alice])
    classroom_b = Classroom([bob])
    classroom_set = ClassroomSet([classroom_a, classroom_b])
    assert classroom_set.classroom_of(alice) is classroom_a
    assert classroom_set.classroom_of(bob) is classroom_b


def test_classroom_of_returns_none_when_student_not_placed() -> None:
    classroom_set = ClassroomSet([Classroom([alice])])
    assert classroom_set.classroom_of(carol) is None
