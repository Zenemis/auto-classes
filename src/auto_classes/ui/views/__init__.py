"""Vues de l'application, une par zone d'écran."""

from auto_classes.ui.views.classes_panel import ClassesPanel
from auto_classes.ui.views.classroom_editor import ClassroomEditor
from auto_classes.ui.views.menu_bar import MenuBar
from auto_classes.ui.views.pronote_dialog import PronoteDialog
from auto_classes.ui.views.results_tab import ResultsTab
from auto_classes.ui.views.setup_tab import SetupTab
from auto_classes.ui.views.student_inspector import StudentInspector
from auto_classes.ui.views.students_panel import StudentsPanel
from auto_classes.ui.views.student_tile import StudentTile

__all__ = [
    "MenuBar",
    "PronoteDialog",
    "ClassesPanel",
    "ClassroomEditor",
    "StudentsPanel",
    "StudentTile",
    "StudentInspector",
    "SetupTab",
    "ResultsTab",
]
