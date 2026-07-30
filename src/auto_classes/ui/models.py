"""Modèle d'édition de l'UI.

Le backend (`auto_classes.core`, `auto_classes.rules`) manipule des objets immuables
identifiés par leur nom : `Student` est un dataclass frozen, une contrainte cible une
classe par son `name`. L'UI a besoin d'identités stables *à travers les renommages* :
d'où ces modèles porteurs d'un `id`, convertis en objets backend seulement au moment
de la génération (`SessionState.build_constraint`).
"""

from dataclasses import dataclass, field
from enum import Enum
from itertools import count

from auto_classes.core import Classroom, Student

_ID_SEQUENCE = count(1)

_VOWELS = "aàâäeéèêëiîïoôöuùûüh"


def _new_id(prefix: str) -> str:
    return f"{prefix}-{next(_ID_SEQUENCE)}"


def elide_de(word: str) -> str:
    """« de Bob », mais « d'Alice » : la préposition s'élide devant une voyelle.

    Le h compte comme une voyelle : sur des prénoms, « d'Hugo » est la forme attendue,
    et distinguer h muet et h aspiré demanderait un dictionnaire. Le y, lui, n'élide
    pas : dans une liste de classe il se prononce presque toujours comme une consonne
    (Yasmine, Yanis), et « d'Yves » reste l'exception.
    """
    if word and word[0].lower() in _VOWELS:
        return f"d'{word}"
    return f"de {word}"


@dataclass
class StudentModel:
    """Un élève de la session en cours."""

    name: str
    id: str = field(default_factory=lambda: _new_id("student"))

    def to_core(self) -> Student:
        return Student(self.name)


@dataclass
class ClassroomModel:
    """Une classe à créer : son nom, ses tags (options : latin, bilangue…) et son effectif."""

    name: str
    tags: set[str] = field(default_factory=set)
    min_size: int | None = None
    max_size: int | None = None
    id: str = field(default_factory=lambda: _new_id("classroom"))

    def to_core(self) -> Classroom:
        """Gabarit vide : `generate_classes` n'utilise que `name` et `tags`."""
        return Classroom(tags=set(self.tags), name=self.name)

    @property
    def has_size_rule(self) -> bool:
        return self.min_size is not None or self.max_size is not None

    def size_label(self) -> str:
        if self.min_size is not None and self.max_size is not None:
            if self.min_size == self.max_size:
                return f"{self.min_size} élèves"
            return f"{self.min_size} à {self.max_size} élèves"
        if self.min_size is not None:
            return f"{self.min_size} élèves minimum"
        if self.max_size is not None:
            return f"{self.max_size} élèves maximum"
        return "Effectif libre"


class RelationKind(Enum):
    """Contrainte entre deux élèves."""

    TOGETHER = "together"
    APART = "apart"

    @property
    def label(self) -> str:
        return "Mettre avec" if self is RelationKind.TOGETHER else "Séparer de"

    def describe(self, other_name: str) -> str:
        if self is RelationKind.TOGETHER:
            return f"Avec {other_name}"
        return f"Séparé {elide_de(other_name)}"


class TagRuleKind(Enum):
    """Contrainte entre un élève et une option de classe (tag)."""

    INCLUDE = "include"
    EXCLUDE = "exclude"

    @property
    def label(self) -> str:
        return "Inclure dans" if self is TagRuleKind.INCLUDE else "Exclure de"

    def describe(self, tag: str) -> str:
        if self is TagRuleKind.INCLUDE:
            return f"Doit avoir l'option « {tag} »"
        return f"Jamais l'option « {tag} »"


@dataclass
class StudentRelation:
    """« Alice avec Bob » / « Alice séparée de Bob ». Non orientée."""

    kind: RelationKind
    first_id: str
    second_id: str
    id: str = field(default_factory=lambda: _new_id("relation"))

    @property
    def pair(self) -> frozenset[str]:
        return frozenset({self.first_id, self.second_id})

    def involves(self, student_id: str) -> bool:
        return student_id in (self.first_id, self.second_id)

    def other_than(self, student_id: str) -> str:
        return self.second_id if student_id == self.first_id else self.first_id


@dataclass
class TagRule:
    """« Alice doit être dans une classe latin » / « jamais en classe bilangue »."""

    kind: TagRuleKind
    student_id: str
    tag: str
    id: str = field(default_factory=lambda: _new_id("tagrule"))
