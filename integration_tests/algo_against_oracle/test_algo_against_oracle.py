import shutil
from pathlib import Path

import pytest

from auto_classes.algorithm.generate_classes import generate_classes
from auto_classes.core import ClassroomSet
from auto_classes.rules.constraint import Constraint
from integration_tests.algo_against_oracle.oracle import canonical_form, format_classroom_set
from integration_tests.algo_against_oracle.oracle_cache import (
    _constraint_hash,
    cached_all_classroom_sets,
    cached_valid_classroom_sets,
)
from integration_tests.algo_against_oracle.oracle_config import load_oracle_config

CONFIG = load_oracle_config(Path(__file__).parent / "oracle.config")
RESULTS_DIR = Path(__file__).parent / "oracle_results"


def _constraint_id(constraint: Constraint) -> str:
    return constraint.to_dict()["type"]


def _dump_classroom_sets(path: Path, classroom_sets: list[ClassroomSet]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = [format_classroom_set(classroom_set) for classroom_set in classroom_sets]
    path.write_text(("\n\n".join(blocks) + "\n") if blocks else "(aucune)\n", encoding="utf-8")


@pytest.fixture(scope="session", autouse=True)
def clear_previous_results() -> None:
    """Purge les dumps de faux positifs/négatifs d'une exécution précédente, pour ne pas
    laisser traîner des artefacts qui ne correspondent plus à l'état actuel de l'algorithme."""
    shutil.rmtree(RESULTS_DIR, ignore_errors=True)


@pytest.fixture(scope="module")
def all_classroom_sets() -> list[ClassroomSet]:
    """Chargé une seule fois pour tout le module et gardé en mémoire, plutôt que rechargé
    depuis le disque à chaque contrainte testée (cf. cached_valid_classroom_sets)."""
    all_sets = cached_all_classroom_sets(CONFIG.students, CONFIG.classroom_tags)
    print(f"\n[oracle] {len(all_sets)} ClassroomSet générés au total (univers complet)")
    return all_sets


@pytest.mark.parametrize("constraint", CONFIG.constraint_sets, ids=_constraint_id)
def test_algorithm_matches_oracle(constraint: Constraint, all_classroom_sets: list[ClassroomSet]) -> None:
    valid = cached_valid_classroom_sets(CONFIG.students, CONFIG.classroom_tags, constraint, all_classroom_sets)
    print(f"[oracle] {_constraint_id(constraint)} : {len(valid)} ClassroomSet valides")
    num_solutions = max(len(valid), 1)

    results = generate_classes(CONFIG.students, CONFIG.classroom_tags, constraint, num_solutions)
    result_by_key = {canonical_form(result): result for result in results}

    duplicate_count = len(results) - len(result_by_key)
    assert duplicate_count == 0, f"l'algorithme a renvoyé {duplicate_count} doublon(s) (à symétrie près)"

    false_positives = [result_by_key[key] for key in result_by_key if key not in valid]
    false_negatives = [valid[key] for key in valid if key not in result_by_key]

    if false_positives or false_negatives:
        base = RESULTS_DIR / f"{_constraint_id(constraint)}_{_constraint_hash(constraint)[:12]}"
        positives_path = base.with_name(base.name + "_faux_positifs.txt")
        negatives_path = base.with_name(base.name + "_faux_negatifs.txt")
        _dump_classroom_sets(positives_path, false_positives)
        _dump_classroom_sets(negatives_path, false_negatives)

        assert not false_positives, (
            f"{len(false_positives)} solution(s) renvoyée(s) par l'algorithme ne satisfont pas la "
            f"contrainte, cf. {positives_path}"
        )
        assert not false_negatives, (
            f"{len(false_negatives)} solution(s) valide(s) n'ont pas été trouvées par l'algorithme, "
            f"cf. {negatives_path}"
        )
