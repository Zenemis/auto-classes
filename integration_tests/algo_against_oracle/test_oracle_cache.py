import csv
from pathlib import Path

import pytest

from auto_classes.core import Classroom, Student
from auto_classes.rules.classroom_invariant import ClassSizeConstraint
from auto_classes.rules.student_relation import StudentsTogether
from integration_tests.algo_against_oracle import oracle_cache
from integration_tests.algo_against_oracle.oracle import (
    canonical_form,
    generate_all_classroom_sets,
    generate_valid_classroom_sets,
)

alice = Student("Alice")
bob = Student("Bob")
carol = Student("Carol")
STUDENTS = [alice, bob, carol]
CLASSROOMS = [Classroom(name="latin", tags={"latin"}), Classroom(name="B", tags=set())]


@pytest.fixture(autouse=True)
def isolated_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cache_dir = tmp_path / "oracle_cache"
    monkeypatch.setattr(oracle_cache, "CACHE_DIR", cache_dir)
    return cache_dir


def test_classroom_shape_hash_is_deterministic() -> None:
    assert oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS) == oracle_cache._classroom_shape_hash(
        list(STUDENTS), CLASSROOMS
    )


def test_classroom_shape_hash_depends_on_student_order() -> None:
    assert oracle_cache._classroom_shape_hash([alice, bob], CLASSROOMS) != oracle_cache._classroom_shape_hash(
        [bob, alice], CLASSROOMS
    )


def test_classroom_shape_hash_depends_on_classroom_tags() -> None:
    assert oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS) != oracle_cache._classroom_shape_hash(
        STUDENTS, [Classroom(name="latin", tags={"latin"}), Classroom(name="B", tags={"sport"})]
    )


def test_classroom_shape_hash_depends_on_classroom_name() -> None:
    assert oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS) != oracle_cache._classroom_shape_hash(
        STUDENTS, [Classroom(name="autre", tags={"latin"}), Classroom(name="B", tags=set())]
    )


def test_classroom_shape_hash_depends_on_classroom_order() -> None:
    assert oracle_cache._classroom_shape_hash(
        STUDENTS, [Classroom(name="latin", tags={"latin"}), Classroom(name="B", tags=set())]
    ) != oracle_cache._classroom_shape_hash(
        STUDENTS, [Classroom(name="B", tags=set()), Classroom(name="latin", tags={"latin"})]
    )


def test_classroom_shape_hash_ignores_tag_iteration_order_within_a_classroom() -> None:
    assert oracle_cache._classroom_shape_hash(
        STUDENTS, [Classroom(name="latin", tags={"latin", "avancé"}), Classroom(name="B", tags=set())]
    ) == oracle_cache._classroom_shape_hash(
        STUDENTS, [Classroom(name="latin", tags={"avancé", "latin"}), Classroom(name="B", tags=set())]
    )


def test_constraint_hash_is_deterministic() -> None:
    assert oracle_cache._constraint_hash(StudentsTogether(alice, bob)) == oracle_cache._constraint_hash(
        StudentsTogether(alice, bob)
    )


def test_constraint_hash_differs_for_different_constraints() -> None:
    assert oracle_cache._constraint_hash(StudentsTogether(alice, bob)) != oracle_cache._constraint_hash(
        ClassSizeConstraint(classroom_name="latin", max_size=2)
    )


def test_cached_all_classroom_sets_writes_a_csv_file(isolated_cache_dir: Path) -> None:
    oracle_cache.cached_all_classroom_sets(STUDENTS, CLASSROOMS)

    cache_file = isolated_cache_dir / f"{oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS)}.csv"
    assert cache_file.exists()
    with cache_file.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))
    assert rows[0] == ["Alice", "Bob", "Carol"]
    assert len(rows) == 1 + len(CLASSROOMS) ** len(STUDENTS)


def test_cached_all_classroom_sets_matches_uncached_generation() -> None:
    expected = {canonical_form(cs) for cs in generate_all_classroom_sets(STUDENTS, CLASSROOMS)}
    cached = {canonical_form(cs) for cs in oracle_cache.cached_all_classroom_sets(STUDENTS, CLASSROOMS)}
    assert cached == expected


def test_cached_all_classroom_sets_second_call_reads_from_cache(isolated_cache_dir: Path) -> None:
    first = oracle_cache.cached_all_classroom_sets(STUDENTS, CLASSROOMS)
    cache_file = isolated_cache_dir / f"{oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS)}.csv"
    written_at = cache_file.stat().st_mtime_ns

    second = oracle_cache.cached_all_classroom_sets(STUDENTS, CLASSROOMS)

    assert cache_file.stat().st_mtime_ns == written_at
    assert {canonical_form(cs) for cs in first} == {canonical_form(cs) for cs in second}


def test_cache_ignored_when_student_list_differs(isolated_cache_dir: Path) -> None:
    cache_file = isolated_cache_dir / f"{oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS)}.csv"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("SomeoneElse\n0\n", encoding="utf-8")

    result = oracle_cache._read_classroom_sets(cache_file, STUDENTS, CLASSROOMS)

    assert result is None


def test_cache_ignored_when_classroom_index_out_of_range(isolated_cache_dir: Path) -> None:
    cache_file = isolated_cache_dir / f"{oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS)}.csv"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("Alice,Bob,Carol\n5,0,1\n", encoding="utf-8")

    result = oracle_cache._read_classroom_sets(cache_file, STUDENTS, CLASSROOMS)

    assert result is None


def test_cached_valid_classroom_sets_writes_nested_file(isolated_cache_dir: Path) -> None:
    constraint = StudentsTogether(alice, bob)
    oracle_cache.cached_valid_classroom_sets(STUDENTS, CLASSROOMS, constraint)

    shape_hash = oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS)
    nested_file = isolated_cache_dir / shape_hash / f"{oracle_cache._constraint_hash(constraint)}.csv"
    assert nested_file.exists()


def test_cached_valid_classroom_sets_matches_uncached_generation() -> None:
    constraint = StudentsTogether(alice, bob)
    all_classroom_sets = generate_all_classroom_sets(STUDENTS, CLASSROOMS)
    expected = generate_valid_classroom_sets(all_classroom_sets, constraint)

    cached = oracle_cache.cached_valid_classroom_sets(STUDENTS, CLASSROOMS, constraint)

    assert cached.keys() == expected.keys()


def test_cached_valid_classroom_sets_second_call_reads_from_cache(isolated_cache_dir: Path) -> None:
    constraint = StudentsTogether(alice, bob)
    first = oracle_cache.cached_valid_classroom_sets(STUDENTS, CLASSROOMS, constraint)
    shape_hash = oracle_cache._classroom_shape_hash(STUDENTS, CLASSROOMS)
    nested_file = isolated_cache_dir / shape_hash / f"{oracle_cache._constraint_hash(constraint)}.csv"
    written_at = nested_file.stat().st_mtime_ns

    second = oracle_cache.cached_valid_classroom_sets(STUDENTS, CLASSROOMS, constraint)

    assert nested_file.stat().st_mtime_ns == written_at
    assert first.keys() == second.keys()


def test_cached_valid_classroom_sets_does_not_touch_the_all_classroom_sets_cache_on_hit(
    isolated_cache_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le sous-ensemble valide doit se suffire à lui-même une fois en cache : le retrouver ne
    doit pas nécessiter de charger (ni a fortiori régénérer) l'univers complet des
    ClassroomSet, potentiellement bien plus coûteux."""
    constraint = StudentsTogether(alice, bob)
    oracle_cache.cached_valid_classroom_sets(STUDENTS, CLASSROOMS, constraint)

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("cached_all_classroom_sets ne doit pas être appelé quand le cache valide est déjà présent")

    monkeypatch.setattr(oracle_cache, "cached_all_classroom_sets", fail_if_called)

    oracle_cache.cached_valid_classroom_sets(STUDENTS, CLASSROOMS, constraint)
