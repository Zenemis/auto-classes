from auto_classes.core import Student
from auto_classes.serialization.students import dump_students, load_students


def test_dump_students_returns_names_in_order() -> None:
    assert dump_students([Student("Alice"), Student("Bob")]) == ["Alice", "Bob"]


def test_load_students_returns_students_in_order() -> None:
    assert load_students(["Alice", "Bob"]) == [Student("Alice"), Student("Bob")]


def test_dump_then_load_round_trips() -> None:
    students = [Student("Alice"), Student("Bob"), Student("Carol")]
    assert load_students(dump_students(students)) == students
