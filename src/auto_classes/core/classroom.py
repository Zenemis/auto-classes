from dataclasses import dataclass, field

from auto_classes.core.student import Student


@dataclass
class Classroom:
    students: list[Student] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)

    def __iter__(self):
        return iter(self.students)

    def __len__(self) -> int:
        return len(self.students)

    def __contains__(self, student: Student) -> bool:
        return student in self.students
