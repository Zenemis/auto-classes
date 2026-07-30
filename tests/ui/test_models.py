import pytest

from auto_classes.core import Classroom, Student
from auto_classes.ui.models import (
    ClassroomModel,
    RelationKind,
    StudentModel,
    StudentRelation,
    TagRuleKind,
)


def test_student_converts_to_backend_student():
    assert StudentModel("Alice").to_core() == Student("Alice")


def test_ids_are_unique():
    assert StudentModel("Alice").id != StudentModel("Alice").id


def test_classroom_converts_to_an_empty_backend_template():
    model = ClassroomModel("6e A", tags={"latin"}, min_size=2, max_size=4)
    core = model.to_core()

    assert core == Classroom(students=[], tags={"latin"}, name="6e A")
    assert core.tags is not model.tags  # copie : le gabarit ne partage rien avec le modèle


@pytest.mark.parametrize(
    ("min_size", "max_size", "expected"),
    [
        (None, None, "Effectif libre"),
        (3, None, "3 élèves minimum"),
        (None, 5, "5 élèves maximum"),
        (2, 4, "2 à 4 élèves"),
        (4, 4, "4 élèves"),
    ],
)
def test_size_label(min_size, max_size, expected):
    assert ClassroomModel("6e A", min_size=min_size, max_size=max_size).size_label() == expected


@pytest.mark.parametrize(
    ("min_size", "max_size", "expected"),
    [(None, None, False), (1, None, True), (None, 1, True)],
)
def test_has_size_rule(min_size, max_size, expected):
    assert ClassroomModel("6e A", min_size=min_size, max_size=max_size).has_size_rule is expected


def test_relation_is_undirected():
    relation = StudentRelation(RelationKind.APART, "a", "b")
    assert relation.pair == frozenset({"a", "b"})
    assert relation.involves("a") and relation.involves("b")
    assert not relation.involves("c")
    assert relation.other_than("a") == "b"
    assert relation.other_than("b") == "a"


def test_relation_kind_describes_in_french():
    assert RelationKind.TOGETHER.describe("Bob") == "Avec Bob"
    assert RelationKind.APART.describe("Bob") == "Séparé de Bob"


def test_tag_rule_kind_describes_in_french():
    assert TagRuleKind.INCLUDE.describe("latin") == "Doit avoir « latin »"
    assert TagRuleKind.EXCLUDE.describe("latin") == "Jamais « latin »"
