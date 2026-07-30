import json
from dataclasses import dataclass
from pathlib import Path

from auto_classes.core import Student
from auto_classes.rules.constraint import Constraint
from auto_classes.serialization.classroom_tags import load_classroom_tags
from auto_classes.serialization.students import load_students


@dataclass
class Config:
    students: list[Student]
    classroom_tags: list[set[str]]
    constraints: list[Constraint]
    num_solutions: int = 1


def load_config(path: Path) -> Config:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Config(
        students=load_students(data["students"]),
        classroom_tags=load_classroom_tags(data["classroom_tags"]),
        constraints=[Constraint.from_dict(constraint) for constraint in data["constraints"]],
        num_solutions=data.get("num_solutions", 1),
    )
