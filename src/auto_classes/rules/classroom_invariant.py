from auto_classes.core import ClassroomSet
from auto_classes.rules.constraint import Constraint


class ClassSizeConstraint(Constraint):
    def __init__(self, min_size: int | None = None, max_size: int | None = None):
        self.min_size = min_size
        self.max_size = max_size

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return all(
            (self.min_size is None or len(classroom) >= self.min_size)
            and (self.max_size is None or len(classroom) <= self.max_size)
            for classroom in classroom_set
        )
