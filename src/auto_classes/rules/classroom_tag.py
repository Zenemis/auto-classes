from typing import Any

from auto_classes.core import ClassroomSet, Student
from auto_classes.rules.constraint import Constraint


class StudentTagPresence(Constraint):
    """Ex : tel élève doit (present=True) / ne doit pas (present=False) être dans une classe portant tel tag."""

    type_name = "student_tag_presence"

    def __init__(self, student: Student, tag: str, present: bool = True):
        self.student = student
        self.tag = tag
        self.present = present

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        classroom = classroom_set.classroom_of(self.student)
        if classroom is None:
            return False
        return (self.tag in classroom.tags) == self.present

    def scope(self) -> set[Student] | None:
        return {self.student}

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "student": self.student.name, "tag": self.tag, "present": self.present}

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "StudentTagPresence":
        return cls(Student(data["student"]), data["tag"], data.get("present", True))
