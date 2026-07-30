from itertools import product

from auto_classes.core import Classroom, ClassroomSet, Student
from auto_classes.rules.constraint import Constraint

CanonicalClassroomSet = tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]


def canonical_form(classroom_set: ClassroomSet) -> CanonicalClassroomSet:
    """Représentation indépendante de l'ordre des classes : deux ClassroomSet qui ne diffèrent
    que par une permutation de classes (à commencer par celles qui partagent les mêmes tags,
    interchangeables pour l'algorithme) sont considérés comme la même solution."""
    return tuple(
        sorted(
            (tuple(sorted(classroom.tags)), tuple(sorted(student.name for student in classroom.students)))
            for classroom in classroom_set
        )
    )


def generate_all_classroom_sets(students: list[Student], classrooms: list[Classroom]) -> list[ClassroomSet]:
    """Force brute : toutes les façons de répartir `students` dans `len(classrooms)` classes,
    sans tenir compte d'aucune contrainte. C'est l'espace de recherche complet de l'algorithme."""
    num_classrooms = len(classrooms)
    all_classroom_sets: list[ClassroomSet] = []
    for assignment in product(range(num_classrooms), repeat=len(students)):
        working_classrooms = [Classroom(tags=set(c.tags), name=c.name) for c in classrooms]
        for student, classroom_index in zip(students, assignment):
            working_classrooms[classroom_index].students.append(student)
        all_classroom_sets.append(ClassroomSet(working_classrooms))
    return all_classroom_sets


def format_classroom_set(classroom_set: ClassroomSet) -> str:
    """Représentation lisible d'un ClassroomSet, pour inspection humaine (ex. dump de faux
    positifs/négatifs à la suite d'un échec de test)."""
    lines = []
    for classroom in classroom_set:
        tags = ", ".join(sorted(classroom.tags)) or "-"
        names = ", ".join(sorted(student.name for student in classroom.students)) or "(vide)"
        lines.append(f"{classroom.name} [tags: {tags}] : {names}")
    return "\n".join(lines)


def generate_valid_classroom_sets(
    all_classroom_sets: list[ClassroomSet], constraint: Constraint
) -> dict[CanonicalClassroomSet, ClassroomSet]:
    """Sous-ensemble de `all_classroom_sets` satisfaisant `constraint`, dédupliqué à symétrie
    près (cf. canonical_form) pour être directement comparable à la sortie de l'algorithme."""
    valid: dict[CanonicalClassroomSet, ClassroomSet] = {}
    for classroom_set in all_classroom_sets:
        if constraint.is_satisfied_by(classroom_set):
            valid.setdefault(canonical_form(classroom_set), classroom_set)
    return valid
