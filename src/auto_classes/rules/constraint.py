from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable, Iterable
from typing import Any, ClassVar

from auto_classes.core import ClassroomSet, Student


def _merge_scopes(scopes: Iterable["set[Student] | None"]) -> "set[Student] | None":
    merged: set[Student] = set()
    for scope in scopes:
        if scope is None:
            return None
        merged |= scope
    return merged


def _merge_classroom_signatures(signatures: Iterable[Hashable]) -> Hashable:
    collected = frozenset(signature for signature in signatures if signature is not None)
    return collected or None


class Constraint(ABC):
    type_name: ClassVar[str]
    _registry: ClassVar[dict[str, type["Constraint"]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "type_name" in cls.__dict__:
            Constraint._registry[cls.type_name] = cls

    @abstractmethod
    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool: ...

    def scope(self) -> "set[Student] | None":
        """Élèves dont dépend cette contrainte ; None si la portée est globale/indéterminée.

        Sert de point d'extension pour un futur solveur CSP (vérification incrémentale
        dès que les élèves de la portée sont affectés), sans impacter is_satisfied_by.
        """
        return None

    def classroom_signature(self, index: int) -> Hashable:
        """Résumé hashable de ce que cette contrainte impose spécifiquement à la classe `index` ;
        None par défaut (la contrainte ne distingue pas cette classe en particulier).

        Sert au bris de symétrie (generate_classes._symmetry_groups) : deux classes portant les
        mêmes tags ne restent interchangeables que si elles ont la même signature pour la
        contrainte globale — deux ClassSizeConstraint aux bornes identiques laissent les classes
        interchangeables, des bornes différentes les distinguent.
        """
        return None

    def is_still_satisfiable(self, classroom_set: ClassroomSet) -> bool:
        """Condition nécessaire vérifiable sur un état partiel (élève encore non placés).

        False signifie que cette branche ne pourra plus jamais satisfaire la contrainte,
        peu importe la suite de la recherche : on peut l'élaguer immédiatement. True par
        défaut (aucune information exploitable) : ne coupe jamais une branche valide.
        """
        return True

    def to_dict(self) -> dict[str, Any]:
        """Sérialise cette contrainte. Pas abstraite : les contraintes custom (ex.
        PredicateConstraint, qui enveloppe une fonction Python arbitraire) n'ont en général
        rien de sérialisable et peuvent laisser ce comportement par défaut."""
        raise TypeError(f"{type(self).__name__} n'est pas sérialisable")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Constraint":
        constraint_cls = Constraint._registry.get(data["type"])
        if constraint_cls is None:
            raise ValueError(f"Type de contrainte inconnu : {data['type']!r}")
        return constraint_cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Constraint":
        raise NotImplementedError

    def __and__(self, other: "Constraint") -> "Constraint":
        return AndConstraint(self, other)

    def __or__(self, other: "Constraint") -> "Constraint":
        return OrConstraint(self, other)

    def __invert__(self) -> "Constraint":
        return NotConstraint(self)


class AndConstraint(Constraint):
    type_name = "and"

    def __init__(self, *constraints: Constraint):
        self.constraints = constraints

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return all(constraint.is_satisfied_by(classroom_set) for constraint in self.constraints)

    def scope(self) -> "set[Student] | None":
        return _merge_scopes(constraint.scope() for constraint in self.constraints)

    def classroom_signature(self, index: int) -> Hashable:
        return _merge_classroom_signatures(constraint.classroom_signature(index) for constraint in self.constraints)

    def is_still_satisfiable(self, classroom_set: ClassroomSet) -> bool:
        return all(constraint.is_still_satisfiable(classroom_set) for constraint in self.constraints)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "constraints": [c.to_dict() for c in self.constraints]}

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "AndConstraint":
        return cls(*(Constraint.from_dict(sub) for sub in data["constraints"]))


class OrConstraint(Constraint):
    type_name = "or"

    def __init__(self, *constraints: Constraint):
        self.constraints = constraints

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return any(constraint.is_satisfied_by(classroom_set) for constraint in self.constraints)

    def scope(self) -> "set[Student] | None":
        return _merge_scopes(constraint.scope() for constraint in self.constraints)

    def classroom_signature(self, index: int) -> Hashable:
        return _merge_classroom_signatures(constraint.classroom_signature(index) for constraint in self.constraints)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "constraints": [c.to_dict() for c in self.constraints]}

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "OrConstraint":
        return cls(*(Constraint.from_dict(sub) for sub in data["constraints"]))


class NotConstraint(Constraint):
    type_name = "not"

    def __init__(self, constraint: Constraint):
        self.constraint = constraint

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return not self.constraint.is_satisfied_by(classroom_set)

    def scope(self) -> "set[Student] | None":
        return self.constraint.scope()

    def classroom_signature(self, index: int) -> Hashable:
        return self.constraint.classroom_signature(index)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "constraint": self.constraint.to_dict()}

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "NotConstraint":
        return cls(Constraint.from_dict(data["constraint"]))


class PredicateConstraint(Constraint):
    """Wrappe une fonction pour définir une contrainte custom sans sous-classer Constraint."""

    def __init__(self, predicate: Callable[[ClassroomSet], bool]):
        self.predicate = predicate

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return self.predicate(classroom_set)
