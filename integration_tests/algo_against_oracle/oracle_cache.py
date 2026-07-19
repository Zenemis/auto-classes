import csv
import hashlib
import json
from pathlib import Path

from auto_classes.core import Classroom, ClassroomSet, Student
from auto_classes.rules.constraint import Constraint
from integration_tests.algo_against_oracle.oracle import (
    CanonicalClassroomSet,
    canonical_form,
    generate_all_classroom_sets,
    generate_valid_classroom_sets,
)

CACHE_DIR = Path(__file__).parent / "oracle_cache"


def _classroom_shape_hash(students: list[Student], classroom_tags: list[set[str]]) -> str:
    # L'ordre des élèves et des classes compte (il fixe le sens des colonnes du CSV et
    # l'indice de chaque classe) : pas de tri sur ces deux listes avant hachage. En
    # revanche, l'ordre des tags à l'intérieur d'une classe est insignifiant (c'est un
    # set) : on le trie pour que le hash soit stable indépendamment de l'itération.
    payload = json.dumps(
        {
            "students": [student.name for student in students],
            "classroom_tags": [sorted(tags) for tags in classroom_tags],
        }
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _constraint_hash(constraint: Constraint) -> str:
    payload = json.dumps(constraint.to_dict(), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_classroom_sets(path: Path, students: list[Student], classroom_sets: list[ClassroomSet]) -> None:
    """Une ligne par ClassroomSet : l'indice de classe de chaque élève, dans l'ordre de
    `students`. Les tags ne sont pas stockés : ils sont fixés par `classroom_tags`, connu du
    lecteur, donc les répéter à chaque ligne serait pur gaspillage."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([student.name for student in students])
        for classroom_set in classroom_sets:
            index_of_student = {
                student: index for index, classroom in enumerate(classroom_set) for student in classroom
            }
            writer.writerow([index_of_student[student] for student in students])


def _read_classroom_sets(
    path: Path, students: list[Student], classroom_tags: list[set[str]]
) -> list[ClassroomSet] | None:
    """Renvoie None si le cache est absent ou ne correspond plus à `students`/`classroom_tags`
    (liste d'élèves différente, ou indice de classe hors bornes) : le cache est alors ignoré et
    régénéré plutôt que de risquer de renvoyer un résultat erroné."""
    if not path.exists():
        return None

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader, None)
        if header != [student.name for student in students]:
            return None

        num_classrooms = len(classroom_tags)
        classroom_sets: list[ClassroomSet] = []
        for row in reader:
            indices = [int(value) for value in row]
            if any(index >= num_classrooms for index in indices):
                return None
            classrooms = [Classroom(tags=set(tags)) for tags in classroom_tags]
            for student, classroom_index in zip(students, indices):
                classrooms[classroom_index].students.append(student)
            classroom_sets.append(ClassroomSet(classrooms))

    return classroom_sets


def cached_all_classroom_sets(students: list[Student], classroom_tags: list[set[str]]) -> list[ClassroomSet]:
    path = CACHE_DIR / f"{_classroom_shape_hash(students, classroom_tags)}.csv"

    cached = _read_classroom_sets(path, students, classroom_tags)
    if cached is not None:
        return cached

    all_classroom_sets = generate_all_classroom_sets(students, classroom_tags)
    _write_classroom_sets(path, students, all_classroom_sets)
    return all_classroom_sets


def cached_valid_classroom_sets(
    students: list[Student], classroom_tags: list[set[str]], constraint: Constraint
) -> dict[CanonicalClassroomSet, ClassroomSet]:
    all_classroom_sets = cached_all_classroom_sets(students, classroom_tags)
    path = CACHE_DIR / _classroom_shape_hash(students, classroom_tags) / f"{_constraint_hash(constraint)}.csv"

    cached = _read_classroom_sets(path, students, classroom_tags)
    if cached is not None:
        return {canonical_form(classroom_set): classroom_set for classroom_set in cached}

    valid = generate_valid_classroom_sets(all_classroom_sets, constraint)
    _write_classroom_sets(path, students, list(valid.values()))
    return valid
