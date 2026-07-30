from collections.abc import Hashable
from typing import Any

from auto_classes.core import ClassroomSet
from auto_classes.rules.constraint import Constraint


class ClassSizeConstraint(Constraint):
    type_name = "class_size"

    def __init__(self, classroom_index: int, min_size: int | None = None, max_size: int | None = None):
        self.classroom_index = classroom_index
        self.min_size = min_size
        self.max_size = max_size

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        classroom = classroom_set.classrooms[self.classroom_index]
        return (self.min_size is None or len(classroom) >= self.min_size) and (
            self.max_size is None or len(classroom) <= self.max_size
        )

    def classroom_signature(self, index: int) -> Hashable:
        if index != self.classroom_index:
            return None
        return ("class_size", self.min_size, self.max_size)

    def is_still_satisfiable(self, classroom_set: ClassroomSet) -> bool:
        # max_size ne peut qu'être violé de façon définitive (les classes ne rétrécissent
        # jamais pendant la recherche) ; min_size ne peut être vérifié qu'en fin d'affectation.
        classroom = classroom_set.classrooms[self.classroom_index]
        return self.max_size is None or len(classroom) <= self.max_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type_name,
            "classroom_index": self.classroom_index,
            "min_size": self.min_size,
            "max_size": self.max_size,
        }

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "ClassSizeConstraint":
        return cls(classroom_index=data["classroom_index"], min_size=data.get("min_size"), max_size=data.get("max_size"))
