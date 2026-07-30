import pytest

from auto_classes.core import Classroom
from auto_classes.serialization.classrooms import dump_classrooms, load_classrooms


def test_dump_classrooms_sorts_tags_and_keeps_classroom_order() -> None:
    classrooms = [Classroom(name="A", tags={"latin", "avancé"}), Classroom(name="B", tags=set())]
    assert dump_classrooms(classrooms) == [
        {"name": "A", "tags": ["avancé", "latin"]},
        {"name": "B", "tags": []},
    ]


def test_load_classrooms_returns_classrooms_in_order() -> None:
    data = [{"name": "A", "tags": ["latin"]}, {"name": "B", "tags": []}]
    assert load_classrooms(data) == [Classroom(name="A", tags={"latin"}), Classroom(name="B", tags=set())]


def test_dump_then_load_round_trips() -> None:
    classrooms = [Classroom(name="A", tags={"latin", "avancé"}), Classroom(name="B", tags=set())]
    assert load_classrooms(dump_classrooms(classrooms)) == classrooms


def test_load_classrooms_raises_on_duplicate_names() -> None:
    data = [{"name": "A", "tags": ["latin"]}, {"name": "A", "tags": []}]
    with pytest.raises(ValueError):
        load_classrooms(data)
