import json
from pathlib import Path

from auto_classes.core import Classroom, Student
from auto_classes.rules.constraint import AndConstraint
from auto_classes.rules.student_relation import StudentsApart, StudentsTogether
from auto_classes.serialization.config import load_config


def _write_config(path: Path, **overrides: object) -> Path:
    data = {
        "students": ["Alice", "Bob"],
        "classrooms": [{"name": "A", "tags": ["latin"]}, {"name": "B", "tags": []}],
        "constraints": [{"type": "students_together", "student_a": "Alice", "student_b": "Bob"}],
        **overrides,
    }
    config_path = path / "config.json"
    config_path.write_text(json.dumps(data), encoding="utf-8")
    return config_path


def test_load_config_parses_students_and_classrooms(tmp_path: Path) -> None:
    config = load_config(_write_config(tmp_path))
    assert config.students == [Student("Alice"), Student("Bob")]
    assert config.classrooms == [Classroom(name="A", tags={"latin"}), Classroom(name="B", tags=set())]


def test_load_config_parses_constraints(tmp_path: Path) -> None:
    config = load_config(_write_config(tmp_path))
    assert len(config.constraints) == 1
    assert isinstance(config.constraints[0], StudentsTogether)
    assert config.constraints[0].student_a == Student("Alice")
    assert config.constraints[0].student_b == Student("Bob")


def test_load_config_parses_multiple_constraints(tmp_path: Path) -> None:
    config = load_config(
        _write_config(
            tmp_path,
            constraints=[
                {"type": "students_together", "student_a": "Alice", "student_b": "Bob"},
                {
                    "type": "and",
                    "constraints": [
                        {"type": "students_apart", "student_a": "Alice", "student_b": "Bob"},
                    ],
                },
            ],
        )
    )
    assert isinstance(config.constraints[0], StudentsTogether)
    assert isinstance(config.constraints[1], AndConstraint)
    assert isinstance(config.constraints[1].constraints[0], StudentsApart)


def test_load_config_defaults_num_solutions_to_one(tmp_path: Path) -> None:
    config = load_config(_write_config(tmp_path))
    assert config.num_solutions == 1


def test_load_config_reads_explicit_num_solutions(tmp_path: Path) -> None:
    config = load_config(_write_config(tmp_path, num_solutions=5))
    assert config.num_solutions == 5
