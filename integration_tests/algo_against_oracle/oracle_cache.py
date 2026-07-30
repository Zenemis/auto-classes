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


def _classroom_shape_hash(students: list[Student], classrooms: list[Classroom]) -> str:
    # L'ordre des élèves et des classes compte (il fixe le sens des colonnes du CSV et
    # l'indice de chaque classe) : pas de tri sur ces deux listes avant hachage. En
    # revanche, l'ordre des tags à l'intérieur d'une classe est insignifiant (c'est un
    # set) : on le trie pour que le hash soit stable indépendamment de l'itération.
    payload = json.dumps(
        {
            "students": [student.name for student in students],
            "classrooms": [{"name": c.name, "tags": sorted(c.tags)} for c in classrooms],
        }
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _constraint_hash(constraint: Constraint) -> str:
    payload = json.dumps(constraint.to_dict(), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_classroom_sets(path: Path, students: list[Student], classroom_sets: list[ClassroomSet]) -> None:
    """Une ligne par ClassroomSet : l'indice de classe de chaque élève, dans l'ordre de
    `students`. Les tags/noms ne sont pas stockés : ils sont fixés par `classrooms`, connu du
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
    path: Path, students: list[Student], classrooms: list[Classroom]
) -> list[ClassroomSet] | None:
    """Renvoie None si le cache est absent ou ne correspond plus à `students`/`classrooms`
    (liste d'élèves différente, ou indice de classe hors bornes) : le cache est alors ignoré et
    régénéré plutôt que de risquer de renvoyer un résultat erroné."""
    if not path.exists():
        return None

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader, None)
        if header != [student.name for student in students]:
            return None

        num_classrooms = len(classrooms)
        classroom_sets: list[ClassroomSet] = []
        for row in reader:
            indices = [int(value) for value in row]
            if max(indices, default=-1) >= num_classrooms:
                return None
            working_classrooms = [Classroom(tags=set(c.tags), name=c.name) for c in classrooms]
            for student, classroom_index in zip(students, indices):
                working_classrooms[classroom_index].students.append(student)
            classroom_sets.append(ClassroomSet(working_classrooms))

    return classroom_sets


def cached_all_classroom_sets(students: list[Student], classrooms: list[Classroom]) -> list[ClassroomSet]:
    path = CACHE_DIR / f"{_classroom_shape_hash(students, classrooms)}.csv"

    cached = _read_classroom_sets(path, students, classrooms)
    if cached is not None:
        return cached

    all_classroom_sets = generate_all_classroom_sets(students, classrooms)
    _write_classroom_sets(path, students, all_classroom_sets)
    return all_classroom_sets


def cached_valid_classroom_sets(
    students: list[Student],
    classrooms: list[Classroom],
    constraint: Constraint,
    all_classroom_sets: list[ClassroomSet] | None = None,
) -> dict[CanonicalClassroomSet, ClassroomSet]:
    """`all_classroom_sets`, si fourni, est utilisé tel quel en cas d'échec du cache du
    sous-ensemble valide, au lieu de le recharger depuis le disque : utile pour un appelant
    (ex. un fixture pytest scope="module") qui garde déjà l'univers complet en mémoire pour
    toute la durée des tests plutôt que de le relire à chaque contrainte."""
    # Le sous-ensemble valide est vérifié en premier : s'il est déjà en cache, on évite de
    # charger (ou pire, régénérer) l'univers complet des ClassroomSet, potentiellement bien
    # plus gros, qui n'est nécessaire qu'en cas d'échec de ce premier cache.
    path = CACHE_DIR / _classroom_shape_hash(students, classrooms) / f"{_constraint_hash(constraint)}.csv"

    cached = _read_classroom_sets(path, students, classrooms)
    if cached is not None:
        return {canonical_form(classroom_set): classroom_set for classroom_set in cached}

    if all_classroom_sets is None:
        all_classroom_sets = cached_all_classroom_sets(students, classrooms)
    valid = generate_valid_classroom_sets(all_classroom_sets, constraint)
    _write_classroom_sets(path, students, list(valid.values()))
    return valid
