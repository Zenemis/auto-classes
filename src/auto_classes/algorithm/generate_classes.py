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


def _snapshot(classrooms: list[Classroom]) -> ClassroomSet:
    return ClassroomSet([Classroom(list(classroom.students), set(classroom.tags)) for classroom in classrooms])


def generate_classes(
    students: list[Student],
    num_classrooms: int,
    constraint: Constraint,
    num_solutions: int,
) -> list[ClassroomSet]:
    """Backtracking incrémental : place les élèves un par un dans les classes, en vérifiant
    chaque sous-contrainte dès que sa portée (Constraint.scope()) est entièrement affectée.

    La règle "une classe vide ne peut être ouverte que si elle est la première encore vide"
    brise la symétrie entre classes interchangeables (vides, sans tags) : chaque répartition
    d'élèves n'est explorée qu'une seule fois, quel que soit l'ordre des indices de classe.
    """
    if num_solutions <= 0:
        raise ValueError("num_solutions doit être strictement positif")

    conjuncts = _flatten_and(constraint)
    global_conjuncts = [c for c in conjuncts if c.scope() is None]
    scoped_conjuncts = [c for c in conjuncts if c.scope() is not None]
    order = _order_by_most_constrained(students, scoped_conjuncts)

    solutions: list[ClassroomSet] = []
    classrooms = [Classroom() for _ in range(num_classrooms)]
    placed: set[Student] = set()

    def backtrack(pos: int) -> bool:
        if pos == len(order):
            candidate = _snapshot(classrooms)
            if all(c.is_satisfied_by(candidate) for c in global_conjuncts):
                solutions.append(candidate)
            return len(solutions) >= num_solutions

        student = order[pos]
        relevant = [c for c in scoped_conjuncts if student in (c.scope() or ())]
        opened = sum(1 for classroom in classrooms if classroom.students)
        candidate_classrooms = classrooms[: min(opened + 1, num_classrooms)]

        for classroom in candidate_classrooms:
            classroom.students.append(student)
            placed.add(student)

            candidate = ClassroomSet(classrooms)
            if all(c.is_satisfied_by(candidate) for c in relevant if (c.scope() or set()) <= placed):
                if backtrack(pos + 1):
                    classroom.students.remove(student)
                    placed.discard(student)
                    return True

            classroom.students.remove(student)
            placed.discard(student)

        return False

    backtrack(0)
    return solutions
