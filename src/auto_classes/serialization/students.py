from auto_classes.core import Student


def dump_students(students: list[Student]) -> list[str]:
    return [student.name for student in students]


def load_students(data: list[str]) -> list[Student]:
    return [Student(name) for name in data]
