from auto_classes.core import ClassroomSet, Student
from auto_classes.rules.constraint import Constraint


class StudentsTogether(Constraint):
    def __init__(self, student_a: Student, student_b: Student):
        self.student_a = student_a
        self.student_b = student_b

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return classroom_set.classroom_of(self.student_a) is classroom_set.classroom_of(self.student_b)


class StudentsApart(Constraint):
    def __init__(self, student_a: Student, student_b: Student):
        self.student_a = student_a
        self.student_b = student_b

    def is_satisfied_by(self, classroom_set: ClassroomSet) -> bool:
        return classroom_set.classroom_of(self.student_a) is not classroom_set.classroom_of(self.student_b)
