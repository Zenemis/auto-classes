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


def generate_all_classroom_sets(students: list[Student], classroom_tags: list[set[str]]) -> list[ClassroomSet]:
    """Force brute : toutes les façons de répartir `students` dans `len(classroom_tags)` classes,
    sans tenir compte d'aucune contrainte. C'est l'espace de recherche complet de l'algorithme."""
    num_classrooms = len(classroom_tags)
    all_classroom_sets: list[ClassroomSet] = []
    for assignment in product(range(num_classrooms), repeat=len(students)):
        classrooms = [Classroom(tags=set(tags)) for tags in classroom_tags]
        for student, classroom_index in zip(students, assignment):
            classrooms[classroom_index].students.append(student)
        all_classroom_sets.append(ClassroomSet(classrooms))
    return all_classroom_sets


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
