from dataclasses import dataclass


@dataclass(frozen=True)
class Student:
    name: str
