from abc import ABC, abstractmethod
from collections.abc import Callable

from auto_classes.core import ClassroomSet


class Constraint(ABC):
    @abstractmethod
    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool: ...

    def __and__(self, other: "Constraint") -> "Constraint":
        return AndConstraint(self, other)

    def __or__(self, other: "Constraint") -> "Constraint":
        return OrConstraint(self, other)

    def __invert__(self) -> "Constraint":
        return NotConstraint(self)


class AndConstraint(Constraint):
    def __init__(self, *constraints: Constraint):
        self.constraints = constraints

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return all(constraint.is_satisfied_by(classroom_set) for constraint in self.constraints)


class OrConstraint(Constraint):
    def __init__(self, *constraints: Constraint):
        self.constraints = constraints

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return any(constraint.is_satisfied_by(classroom_set) for constraint in self.constraints)


class NotConstraint(Constraint):
    def __init__(self, constraint: Constraint):
        self.constraint = constraint

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return not self.constraint.is_satisfied_by(classroom_set)


class PredicateConstraint(Constraint):
    """Wrappe une fonction pour définir une contrainte custom sans sous-classer Constraint."""

    def __init__(self, predicate: Callable[[ClassroomSet], bool]):
        self.predicate = predicate

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return self.predicate(classroom_set)
