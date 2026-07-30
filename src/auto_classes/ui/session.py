"""État de la session : la seule source de vérité que lisent et modifient les vues.

Rien n'est persisté entre deux lancements du logiciel : tout vit ici, en mémoire, et
disparaît à la fermeture. Les vues n'échangent jamais de données entre elles ; elles
écrivent dans cet objet et se rafraîchissent sur ses signaux.
"""

from typing import Any

from auto_classes.core import Classroom, Student
from auto_classes.rules import (
    AndConstraint,
    ClassSizeConstraint,
    Constraint,
    StudentsApart,
    StudentsTogether,
    StudentTagPresence,
)
from auto_classes.ui.models import (
    ClassroomModel,
    RelationKind,
    StudentModel,
    StudentRelation,
    TagRule,
    TagRuleKind,
)
from auto_classes.ui.signal import Signal

_UNSET: Any = object()


class SessionError(ValueError):
    """Refus d'une modification, avec un message affichable tel quel à l'utilisateur."""


class SessionState:
    """Élèves, classes et contraintes de la session, plus les signaux de rafraîchissement."""

    def __init__(self) -> None:
        self._students: list[StudentModel] = []
        self._classrooms: list[ClassroomModel] = []
        self._relations: list[StudentRelation] = []
        self._tag_rules: list[TagRule] = []
        self._num_solutions = 3

        self.students_changed = Signal("students_changed")
        self.classrooms_changed = Signal("classrooms_changed")
        self.constraints_changed = Signal("constraints_changed")

    # ------------------------------------------------------------------ lecture

    @property
    def students(self) -> list[StudentModel]:
        """Les élèves, triés par nom (ordre d'affichage attendu par les enseignants)."""
        return sorted(self._students, key=lambda student: student.name.casefold())

    @property
    def classrooms(self) -> list[ClassroomModel]:
        return list(self._classrooms)

    @property
    def relations(self) -> list[StudentRelation]:
        return list(self._relations)

    @property
    def tag_rules(self) -> list[TagRule]:
        return list(self._tag_rules)

    @property
    def num_solutions(self) -> int:
        return self._num_solutions

    @num_solutions.setter
    def num_solutions(self, value: int) -> None:
        self._num_solutions = max(1, int(value))

    def student(self, student_id: str) -> StudentModel | None:
        return next((student for student in self._students if student.id == student_id), None)

    def classroom(self, classroom_id: str) -> ClassroomModel | None:
        return next((classroom for classroom in self._classrooms if classroom.id == classroom_id), None)

    def available_tags(self) -> list[str]:
        """Union des tags portés par les classes : le vocabulaire proposé aux contraintes."""
        tags: set[str] = set()
        for classroom in self._classrooms:
            tags |= classroom.tags
        return sorted(tags, key=str.casefold)

    def relations_of(self, student_id: str) -> list[StudentRelation]:
        return [relation for relation in self._relations if relation.involves(student_id)]

    def tag_rules_of(self, student_id: str) -> list[TagRule]:
        return [rule for rule in self._tag_rules if rule.student_id == student_id]

    def relation_between(self, first_id: str, second_id: str) -> StudentRelation | None:
        """La contrainte liant ces deux élèves, quel que soit son sens. Une seule par paire."""
        pair = frozenset({first_id, second_id})
        return next((relation for relation in self._relations if relation.pair == pair), None)

    def tag_rule_for(self, student_id: str, tag: str) -> TagRule | None:
        """La contrainte liant cet élève à ce tag. Une seule par couple."""
        return next(
            (
                rule
                for rule in self._tag_rules
                if rule.student_id == student_id and rule.tag == tag.strip()
            ),
            None,
        )

    def constraint_count_of(self, student_id: str) -> int:
        return len(self.relations_of(student_id)) + len(self.tag_rules_of(student_id))

    # ------------------------------------------------------------------- élèves

    def add_student(self, name: str) -> StudentModel:
        clean = name.strip()
        if not clean:
            raise SessionError("Le nom de l'élève ne peut pas être vide.")
        if self._student_named(clean) is not None:
            raise SessionError(f"« {clean} » figure déjà dans la liste.")
        student = StudentModel(name=clean)
        self._students.append(student)
        self.students_changed.emit()
        return student

    def add_students(self, names: list[str]) -> tuple[list[StudentModel], list[tuple[str, str]]]:
        """Ajout en lot, sans tout annuler en cas de refus partiel.

        Renvoie les élèves ajoutés et les refus sous forme de couples (nom, raison) :
        la saisie en place s'en sert pour ne laisser dans le champ que les noms à
        corriger.
        """
        added: list[StudentModel] = []
        rejected: list[tuple[str, str]] = []
        for name in names:
            try:
                student = self.add_student(name)
            except SessionError as error:
                rejected.append((name, str(error)))
            else:
                added.append(student)
        return added, rejected

    def rename_student(self, student_id: str, name: str) -> None:
        student = self._require_student(student_id)
        clean = name.strip()
        if not clean:
            raise SessionError("Le nom de l'élève ne peut pas être vide.")
        existing = self._student_named(clean)
        if existing is not None and existing.id != student_id:
            raise SessionError(f"« {clean} » figure déjà dans la liste.")
        student.name = clean
        self.students_changed.emit()

    def remove_student(self, student_id: str) -> None:
        student = self._require_student(student_id)
        self._students.remove(student)
        self._relations = [relation for relation in self._relations if not relation.involves(student_id)]
        self._tag_rules = [rule for rule in self._tag_rules if rule.student_id != student_id]
        self.students_changed.emit()
        self.constraints_changed.emit()

    # ------------------------------------------------------------------ classes

    def add_classroom(self, name: str | None = None) -> ClassroomModel:
        chosen = (name or self._next_classroom_name()).strip()
        if not chosen:
            raise SessionError("Le nom de la classe ne peut pas être vide.")
        if self._classroom_named(chosen) is not None:
            raise SessionError(f"Une classe « {chosen} » existe déjà.")
        classroom = ClassroomModel(name=chosen)
        self._classrooms.append(classroom)
        self.classrooms_changed.emit()
        return classroom

    def update_classroom(
        self,
        classroom_id: str,
        *,
        name: str = _UNSET,
        min_size: int | None = _UNSET,
        max_size: int | None = _UNSET,
        tags: set[str] = _UNSET,
    ) -> None:
        """Applique en un seul lot les champs fournis (les autres restent inchangés)."""
        classroom = self._require_classroom(classroom_id)

        new_name = classroom.name if name is _UNSET else name.strip()
        new_min = classroom.min_size if min_size is _UNSET else min_size
        new_max = classroom.max_size if max_size is _UNSET else max_size
        new_tags = set(classroom.tags) if tags is _UNSET else {tag.strip() for tag in tags if tag.strip()}

        if not new_name:
            raise SessionError("Le nom de la classe ne peut pas être vide.")
        existing = self._classroom_named(new_name)
        if existing is not None and existing.id != classroom_id:
            raise SessionError(f"Une classe « {new_name} » existe déjà.")
        if new_min is not None and new_min < 0:
            raise SessionError("L'effectif minimum ne peut pas être négatif.")
        if new_max is not None and new_max < 1:
            raise SessionError("L'effectif maximum doit valoir au moins 1.")
        if new_min is not None and new_max is not None and new_min > new_max:
            raise SessionError("L'effectif minimum ne peut pas dépasser le maximum.")

        classroom.name = new_name
        classroom.min_size = new_min
        classroom.max_size = new_max
        classroom.tags = new_tags

        self.classrooms_changed.emit()
        if self._prune_orphan_tag_rules():
            self.constraints_changed.emit()

    def remove_classroom(self, classroom_id: str) -> None:
        classroom = self._require_classroom(classroom_id)
        self._classrooms.remove(classroom)
        self.classrooms_changed.emit()
        if self._prune_orphan_tag_rules():
            self.constraints_changed.emit()

    # -------------------------------------------------------------- contraintes

    def toggle_relation(
        self, kind: RelationKind, first_id: str, second_id: str
    ) -> StudentRelation | None:
        """Pose la contrainte, ou la retire si elle est déjà posée à l'identique.

        Un clic pose, un second clic défait : c'est la même geste qui sert dans les deux
        sens. Une contrainte de l'autre type sur la même paire est remplacée, pas
        retirée — deux élèves ne peuvent pas être à la fois ensemble et séparés.
        """
        existing = self.relation_between(first_id, second_id)
        if existing is not None and existing.kind is kind:
            self.remove_relation(existing.id)
            return None
        return self.add_relation(kind, first_id, second_id)

    def add_relation(self, kind: RelationKind, first_id: str, second_id: str) -> StudentRelation:
        """Crée (ou remplace) la contrainte liant deux élèves : une seule par paire."""
        first = self._require_student(first_id)
        second = self._require_student(second_id)
        if first.id == second.id:
            raise SessionError("Un élève ne peut pas être mis en relation avec lui-même.")

        existing = self.relation_between(first.id, second.id)
        if existing is not None:
            if existing.kind is kind:
                return existing
            self._relations.remove(existing)

        relation = StudentRelation(kind=kind, first_id=first.id, second_id=second.id)
        self._relations.append(relation)
        self.constraints_changed.emit()
        return relation

    def remove_relation(self, relation_id: str) -> None:
        self._relations = [relation for relation in self._relations if relation.id != relation_id]
        self.constraints_changed.emit()

    def toggle_tag_rule(self, kind: TagRuleKind, student_id: str, tag: str) -> TagRule | None:
        """Pose la contrainte élève–tag, ou la retire si elle est déjà posée à l'identique."""
        existing = self.tag_rule_for(student_id, tag)
        if existing is not None and existing.kind is kind:
            self.remove_tag_rule(existing.id)
            return None
        return self.add_tag_rule(kind, student_id, tag)

    def add_tag_rule(self, kind: TagRuleKind, student_id: str, tag: str) -> TagRule:
        """Crée (ou remplace) la contrainte liant un élève à un tag : une seule par couple."""
        student = self._require_student(student_id)
        clean_tag = tag.strip()
        if not clean_tag:
            raise SessionError("Le tag ne peut pas être vide.")

        existing = self.tag_rule_for(student.id, clean_tag)
        if existing is not None:
            if existing.kind is kind:
                return existing
            self._tag_rules.remove(existing)

        rule = TagRule(kind=kind, student_id=student.id, tag=clean_tag)
        self._tag_rules.append(rule)
        self.constraints_changed.emit()
        return rule

    def remove_tag_rule(self, rule_id: str) -> None:
        self._tag_rules = [rule for rule in self._tag_rules if rule.id != rule_id]
        self.constraints_changed.emit()

    # ------------------------------------------------------------ vers le backend

    def core_students(self) -> list[Student]:
        return [student.to_core() for student in self.students]

    def core_classrooms(self) -> list[Classroom]:
        return [classroom.to_core() for classroom in self._classrooms]

    def build_constraint(self) -> Constraint:
        """Agrège tout l'état en une contrainte unique consommable par `generate_classes`.

        Une `AndConstraint` vide est valide : `generate_classes` l'aplatit en zéro
        conjonction et se contente alors de répartir les élèves.
        """
        parts: list[Constraint] = []

        for classroom in self._classrooms:
            if classroom.has_size_rule:
                parts.append(ClassSizeConstraint(classroom.name, classroom.min_size, classroom.max_size))

        for relation in self._relations:
            first = self.student(relation.first_id)
            second = self.student(relation.second_id)
            if first is None or second is None:
                continue
            factory = StudentsTogether if relation.kind is RelationKind.TOGETHER else StudentsApart
            parts.append(factory(first.to_core(), second.to_core()))

        for rule in self._tag_rules:
            student = self.student(rule.student_id)
            if student is None:
                continue
            parts.append(
                StudentTagPresence(student.to_core(), rule.tag, present=rule.kind is TagRuleKind.INCLUDE)
            )

        return AndConstraint(*parts)

    def validate(self) -> list[str]:
        """Problèmes bloquants ou manifestement insolubles, en clair pour l'utilisateur."""
        problems: list[str] = []

        if not self._students:
            problems.append("Ajoutez au moins un élève avant de générer.")
        if not self._classrooms:
            problems.append("Ajoutez au moins une classe avant de générer.")
        if not problems:
            problems += self._capacity_problems()

        unknown_tags = sorted(
            {rule.tag for rule in self._tag_rules if rule.tag not in set(self.available_tags())}
        )
        if unknown_tags:
            problems.append(
                "Aucune classe ne porte le tag " + ", ".join(f"« {tag} »" for tag in unknown_tags) + "."
            )

        return problems

    def _capacity_problems(self) -> list[str]:
        problems: list[str] = []
        headcount = len(self._students)

        maxima = [classroom.max_size for classroom in self._classrooms]
        if all(maximum is not None for maximum in maxima):
            capacity = sum(maxima)  # type: ignore[arg-type]
            if capacity < headcount:
                problems.append(
                    f"Effectifs maximum trop bas : {capacity} places pour {headcount} élèves."
                )

        floor = sum(classroom.min_size or 0 for classroom in self._classrooms)
        if floor > headcount:
            problems.append(f"Effectifs minimum trop hauts : {floor} places exigées pour {headcount} élèves.")

        return problems

    # ------------------------------------------------------------------ interne

    def _student_named(self, name: str) -> StudentModel | None:
        target = name.casefold()
        return next((student for student in self._students if student.name.casefold() == target), None)

    def _classroom_named(self, name: str) -> ClassroomModel | None:
        target = name.casefold()
        return next(
            (classroom for classroom in self._classrooms if classroom.name.casefold() == target), None
        )

    def _require_student(self, student_id: str) -> StudentModel:
        student = self.student(student_id)
        if student is None:
            raise SessionError("Cet élève n'existe plus.")
        return student

    def _require_classroom(self, classroom_id: str) -> ClassroomModel:
        classroom = self.classroom(classroom_id)
        if classroom is None:
            raise SessionError("Cette classe n'existe plus.")
        return classroom

    def _prune_orphan_tag_rules(self) -> bool:
        """Supprime les contraintes visant un tag qu'aucune classe ne porte plus."""
        known = set(self.available_tags())
        kept = [rule for rule in self._tag_rules if rule.tag in known]
        if len(kept) == len(self._tag_rules):
            return False
        self._tag_rules = kept
        return True

    def _next_classroom_name(self) -> str:
        index = len(self._classrooms) + 1
        while self._classroom_named(f"Classe {index}") is not None:
            index += 1
        return f"Classe {index}"
