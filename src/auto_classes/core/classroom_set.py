from dataclasses import dataclass, field

from auto_classes.core.classroom import Classroom
from auto_classes.core.student import Student


@dataclass
class ClassroomSet:
    classrooms: list[Classroom] = field(default_factory=list)

    def __iter__(self):
        return iter(self.classrooms)

    def __len__(self) -> int:
        return len(self.classrooms)

    def classroom_of(self, student: Student) -> Classroom | None:
        for classroom in self.classrooms:
            if student in classroom:
                return classroom
        return None
