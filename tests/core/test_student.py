from auto_classes.core.student import Student


def test_students_with_same_name_are_equal() -> None:
    assert Student("Alice") == Student("Alice")


def test_students_with_different_name_are_not_equal() -> None:
    assert Student("Alice") != Student("Bob")
