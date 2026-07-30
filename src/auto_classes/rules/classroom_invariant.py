from collections.abc import Hashable
from typing import Any

from auto_classes.core import Classroom, ClassroomSet
from auto_classes.rules.constraint import Constraint


class ClassSizeConstraint(Constraint):
    type_name = "class_size"

    def __init__(self, classroom_name: str, min_size: int | None = None, max_size: int | None = None):
        self.classroom_name = classroom_name
        self.min_size = min_size
        self.max_size = max_size

    def _target(self, classroom_set: ClassroomSet) -> Classroom:
        classroom = classroom_set.classroom_named(self.classroom_name)
        if classroom is None:
            raise ValueError(f"Classe inconnue : {self.classroom_name!r}")
        return classroom

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        classroom = self._target(classroom_set)
        return (self.min_size is None or len(classroom) >= self.min_size) and (
            self.max_size is None or len(classroom) <= self.max_size
        )

    def classroom_signature(self, name: str) -> Hashable:
        if name != self.classroom_name:
            return None
        return ("class_size", self.min_size, self.max_size)

    def is_still_satisfiable(self, classroom_set: ClassroomSet) -> bool:
        # max_size ne peut qu'être violé de façon définitive (les classes ne rétrécissent
        # jamais pendant la recherche) ; min_size ne peut être vérifié qu'en fin d'affectation.
        classroom = self._target(classroom_set)
        return self.max_size is None or len(classroom) <= self.max_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type_name,
            "classroom_name": self.classroom_name,
            "min_size": self.min_size,
            "max_size": self.max_size,
        }

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "ClassSizeConstraint":
        return cls(
            classroom_name=data["classroom_name"], min_size=data.get("min_size"), max_size=data.get("max_size")
        )
