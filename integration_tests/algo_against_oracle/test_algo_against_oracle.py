from pathlib import Path

import pytest

from auto_classes.algorithm.generate_classes import generate_classes
from auto_classes.rules.constraint import Constraint
from integration_tests.algo_against_oracle.oracle import canonical_form
from integration_tests.algo_against_oracle.oracle_cache import cached_valid_classroom_sets
from integration_tests.algo_against_oracle.oracle_config import load_oracle_config

CONFIG = load_oracle_config(Path(__file__).parent / "oracle.config")


def _constraint_id(constraint: Constraint) -> str:
    return constraint.to_dict()["type"]


@pytest.mark.parametrize("constraint", CONFIG.constraint_sets, ids=_constraint_id)
def test_algorithm_matches_oracle(constraint: Constraint) -> None:
    valid = cached_valid_classroom_sets(CONFIG.students, CONFIG.classroom_tags, constraint)
    num_solutions = max(len(valid), 1)

    results = generate_classes(CONFIG.students, CONFIG.classroom_tags, constraint, num_solutions)
    result_keys = [canonical_form(result) for result in results]

    assert len(result_keys) == len(set(result_keys)), "l'algorithme a renvoyé des doublons (à symétrie près)"
    assert set(result_keys) <= valid.keys(), "l'algorithme a renvoyé une solution qui ne satisfait pas la contrainte"
    assert len(results) == len(valid), "l'algorithme n'a pas trouvé toutes les solutions valides"
