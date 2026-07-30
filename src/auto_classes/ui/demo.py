"""Jeu d'essai pour explorer l'UI sans ressaisir des données à chaque lancement.

Utilisé uniquement par `python -m auto_classes.ui --demo` ; l'application démarre
autrement sur une session vide.
"""

from auto_classes.ui.models import RelationKind, TagRuleKind
from auto_classes.ui.session import SessionState

DEMO_STUDENTS = (
    "Alice",
    "Bob",
    "Carole",
    "Damien",
    "Elsa",
    "Farid",
    "Gaëlle",
    "Hugo",
    "Inès",
    "Jonas",
    "Karim",
    "Léa",
    # Nom volontairement long : vérifie la troncature des tuiles à l'œil nu.
    "Marie-Charlotte Vandenbrouck",
)


def build_demo_session() -> SessionState:
    session = SessionState()

    latin = session.add_classroom("6e A")
    session.update_classroom(latin.id, min_size=5, max_size=7, tags={"latin"})

    general = session.add_classroom("6e B")
    session.update_classroom(general.id, min_size=5, max_size=7, tags={"bilangue"})

    session.add_students(list(DEMO_STUDENTS))
    by_name = {student.name: student for student in session.students}

    session.add_relation(RelationKind.TOGETHER, by_name["Alice"].id, by_name["Bob"].id)
    session.add_relation(RelationKind.APART, by_name["Carole"].id, by_name["Damien"].id)
    session.add_tag_rule(TagRuleKind.INCLUDE, by_name["Elsa"].id, "latin")
    session.add_tag_rule(TagRuleKind.EXCLUDE, by_name["Farid"].id, "latin")

    return session
