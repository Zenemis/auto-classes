import json
from dataclasses import dataclass
from pathlib import Path

from auto_classes.core import Classroom, Student
from auto_classes.rules.constraint import Constraint
from auto_classes.serialization.classrooms import load_classrooms
from auto_classes.serialization.students import load_students


@dataclass
class Config:
    students: list[Student]
    classrooms: list[Classroom]
    constraints: list[Constraint]
    num_solutions: int = 1


def load_config(path: Path) -> Config:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Config(
        students=load_students(data["students"]),
        classrooms=load_classrooms(data["classrooms"]),
        constraints=[Constraint.from_dict(constraint) for constraint in data["constraints"]],
        num_solutions=data.get("num_solutions", 1),
    )
