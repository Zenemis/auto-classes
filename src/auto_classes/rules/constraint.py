from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable

from auto_classes.core import ClassroomSet, Student


def _merge_scopes(scopes: Iterable["set[Student] | None"]) -> "set[Student] | None":
    merged: set[Student] = set()
    for scope in scopes:
        if scope is None:
            return None
        merged |= scope
    return merged


class Constraint(ABC):
    @abstractmethod
    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool: ...

    def scope(self) -> "set[Student] | None":
        """Élèves dont dépend cette contrainte ; None si la portée est globale/indéterminée.

        Sert de point d'extension pour un futur solveur CSP (vérification incrémentale
        dès que les élèves de la portée sont affectés), sans impacter is_satisfied_by.
        """
        return None

    def is_still_satisfiable(self, classroom_set: ClassroomSet) -> bool:
        """Condition nécessaire vérifiable sur un état partiel (élève encore non placés).

        False signifie que cette branche ne pourra plus jamais satisfaire la contrainte,
        peu importe la suite de la recherche : on peut l'élaguer immédiatement. True par
        défaut (aucune information exploitable) : ne coupe jamais une branche valide.
        """
        return True

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

    def scope(self) -> "set[Student] | None":
        return _merge_scopes(constraint.scope() for constraint in self.constraints)

    def is_still_satisfiable(self, classroom_set: ClassroomSet) -> bool:
        return all(constraint.is_still_satisfiable(classroom_set) for constraint in self.constraints)


class OrConstraint(Constraint):
    def __init__(self, *constraints: Constraint):
        self.constraints = constraints

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return any(constraint.is_satisfied_by(classroom_set) for constraint in self.constraints)

    def scope(self) -> "set[Student] | None":
        return _merge_scopes(constraint.scope() for constraint in self.constraints)


class NotConstraint(Constraint):
    def __init__(self, constraint: Constraint):
        self.constraint = constraint

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return not self.constraint.is_satisfied_by(classroom_set)

    def scope(self) -> "set[Student] | None":
        return self.constraint.scope()


class PredicateConstraint(Constraint):
    """Wrappe une fonction pour définir une contrainte custom sans sous-classer Constraint."""

    def __init__(self, predicate: Callable[[ClassroomSet], bool]):
        self.predicate = predicate

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return self.predicate(classroom_set)
