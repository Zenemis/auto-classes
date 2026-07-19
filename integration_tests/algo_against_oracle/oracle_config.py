import json
from dataclasses import dataclass
from pathlib import Path

from auto_classes.core import Student
from auto_classes.rules.constraint import Constraint
from auto_classes.serialization import load_classroom_tags, load_students


@dataclass
class OracleConfig:
    students: list[Student]
    classroom_tags: list[set[str]]
    constraint_sets: list[Constraint]


def load_oracle_config(path: Path) -> OracleConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return OracleConfig(
        students=load_students(data["students"]),
        classroom_tags=load_classroom_tags(data["classroom_tags"]),
        constraint_sets=[Constraint.from_dict(constraint) for constraint in data["constraint_sets"]],
    )
