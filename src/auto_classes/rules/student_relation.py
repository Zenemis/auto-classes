from typing import Any

from auto_classes.core import ClassroomSet, Student
from auto_classes.rules.constraint import Constraint


class StudentsTogether(Constraint):
    type_name = "students_together"

    def __init__(self, student_a: Student, student_b: Student):
        self.student_a = student_a
        self.student_b = student_b

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return classroom_set.classroom_of(self.student_a) is classroom_set.classroom_of(self.student_b)

    def scope(self) -> set[Student] | None:
        return {self.student_a, self.student_b}

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "student_a": self.student_a.name, "student_b": self.student_b.name}

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "StudentsTogether":
        return cls(Student(data["student_a"]), Student(data["student_b"]))


class StudentsApart(Constraint):
    type_name = "students_apart"

    def __init__(self, student_a: Student, student_b: Student):
        self.student_a = student_a
        self.student_b = student_b

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return classroom_set.classroom_of(self.student_a) is not classroom_set.classroom_of(self.student_b)

    def scope(self) -> set[Student] | None:
        return {self.student_a, self.student_b}

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "student_a": self.student_a.name, "student_b": self.student_b.name}

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "StudentsApart":
        return cls(Student(data["student_a"]), Student(data["student_b"]))
