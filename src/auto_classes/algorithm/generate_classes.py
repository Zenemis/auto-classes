from collections import defaultdict

from auto_classes.core import Classroom, ClassroomSet, Student
from auto_classes.rules.constraint import AndConstraint, Constraint


def _flatten_and(constraint: Constraint) -> tuple[Constraint, ...]:
    if isinstance(constraint, AndConstraint):
        return tuple(leaf for sub in constraint.constraints for leaf in _flatten_and(sub))
    return (constraint,)


def _order_by_most_constrained(students: list[Student], scoped: list[Constraint]) -> list[Student]:
    def degree(student: Student) -> int:
        return sum(1 for constraint in scoped if student in (constraint.scope() or ()))

    return sorted(students, key=degree, reverse=True)


def _symmetry_groups(classrooms: list[Classroom], constraint: Constraint) -> list[list[int]]:
    """Regroupe les indices de classes interchangeables : même tag-set, et même signature vis-à-vis
    de la contrainte globale (cf. Constraint.classroom_signature). Deux classes de mêmes tags avec
    des ClassSizeConstraint aux bornes identiques restent groupées ; des bornes différentes (ou une
    seule des deux classes contrainte) les séparent en groupes distincts."""
    groups: dict[tuple[frozenset[str], object], list[int]] = defaultdict(list)
    for index, classroom in enumerate(classrooms):
        key = (frozenset(classroom.tags), constraint.classroom_signature(classroom.name))
        groups[key].append(index)
    return list(groups.values())


def _snapshot(classrooms: list[Classroom]) -> ClassroomSet:
    return ClassroomSet(
        [Classroom(list(classroom.students), set(classroom.tags), classroom.name) for classroom in classrooms]
    )


def generate_classes(
    students: list[Student],
    classrooms: list[Classroom],
    constraint: Constraint,
    num_solutions: int,
) -> list[ClassroomSet]:
    """Backtracking incrémental : place les élèves un par un dans les classes, en vérifiant
    chaque sous-contrainte dès que sa portée (Constraint.scope()) est entièrement affectée,
    et en élaguant dès qu'une contrainte globale devient insatisfaisable (is_still_satisfiable).

    `classrooms` fixe le nombre de classes (sa longueur), leur `name` (identité stable utilisée
    par les contraintes pour cibler une classe précise, ex. ClassSizeConstraint) et leurs `tags` ;
    ce sont des gabarits vides, leurs éventuels `students` sont ignorés. La règle "une classe
    vide ne peut être ouverte que si elle est la première encore vide de son groupe" brise la
    symétrie entre classes interchangeables (mêmes tags, même signature) : chaque répartition
    d'élèves n'est explorée qu'une fois.
    """
    if num_solutions <= 0:
        raise ValueError("num_solutions doit être strictement positif")

    conjuncts = _flatten_and(constraint)
    global_conjuncts = [c for c in conjuncts if c.scope() is None]
    scoped_conjuncts = [c for c in conjuncts if c.scope() is not None]
    order = _order_by_most_constrained(students, scoped_conjuncts)
    symmetry_groups = _symmetry_groups(classrooms, constraint)

    solutions: list[ClassroomSet] = []
    working_classrooms = [Classroom(tags=set(c.tags), name=c.name) for c in classrooms]
    placed: set[Student] = set()

    def allowed_indices() -> list[int]:
        allowed: list[int] = []
        for indices in symmetry_groups:
            opened = sum(1 for i in indices if working_classrooms[i].students)
            allowed += indices[: min(opened + 1, len(indices))]
        return allowed

    def backtrack(pos: int) -> bool:
        if pos == len(order):
            candidate = _snapshot(working_classrooms)
            if all(c.is_satisfied_by(candidate) for c in global_conjuncts):
                solutions.append(candidate)
            return len(solutions) >= num_solutions

        student = order[pos]
        relevant = [c for c in scoped_conjuncts if student in (c.scope() or ())]

        for index in allowed_indices():
            classroom = working_classrooms[index]
            classroom.students.append(student)
            placed.add(student)

            candidate = ClassroomSet(working_classrooms)
            still_ok = all(c.is_still_satisfiable(candidate) for c in global_conjuncts)
            locally_ok = all(c.is_satisfied_by(candidate) for c in relevant if (c.scope() or set()) <= placed)
            if still_ok and locally_ok:
                if backtrack(pos + 1):
                    classroom.students.remove(student)
                    placed.discard(student)
                    return True

            classroom.students.remove(student)
            placed.discard(student)

        return False

    backtrack(0)
    return solutions
