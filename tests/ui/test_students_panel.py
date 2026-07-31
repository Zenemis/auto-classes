"""Sélection et désélection d'un élève dans la bande « Élèves ».

Cliquer sa propre tuile, une zone vide de la liste, ou l'intérieur de l'inspecteur ont
trois effets différents et c'est précisément ce qui se confondait : ces tests figent le
routage plutôt que le rendu.
"""

import pytest

from auto_classes.ui.interaction import InteractionState, Tool
from auto_classes.ui.session import SessionState
from auto_classes.ui.views.students_panel import StudentsPanel


@pytest.fixture
def panel(root):
    """`root` (racine partagée, réellement mappée) vient de `conftest.py` :
    `on_background_click` a besoin d'évènements Tk livrés pour de vrai, ce qu'une
    fenêtre `withdraw()`ée ne fait jamais."""
    session = SessionState()
    interaction = InteractionState()
    widget = StudentsPanel(root, session, interaction)
    widget.pack(fill="both", expand=True)
    root.update()
    yield widget, session, interaction
    widget.destroy()
    root.update()


def _add(session, *names):
    students = []
    for name in names:
        students.append(session.add_student(name))
    return students


def _click_background(panel_widget, target):
    """Clic réel dans la zone vide, en bas de la grille (sous les tuiles).

    Un `update()` avant de mesurer la cible est indispensable : sans lui, la mise en
    page provoquée par l'ajout d'élève ou l'armement de l'outil n'a pas encore tourné,
    `winfo_height()` répond avec une taille par défaut non représentative, et le clic
    part vers une position qui ne correspond à rien de stable.
    """
    root = panel_widget.winfo_toplevel()
    root.update()
    canvas = getattr(target, "_canvas", target)
    canvas.event_generate("<Button-1>", x=5, y=max(canvas.winfo_height() - 3, 1))
    root.update()


def test_clicking_a_student_selects_it(panel):
    widget, session, interaction = panel
    (alice,) = _add(session, "Alice")

    widget._on_tile_clicked(alice.id)

    assert interaction.selected_student_id == alice.id


def test_clicking_the_selected_tile_again_deselects_it(panel):
    widget, session, interaction = panel
    (alice,) = _add(session, "Alice")
    widget._on_tile_clicked(alice.id)

    widget._on_tile_clicked(alice.id)

    assert interaction.selected_student_id is None


def test_reclicking_the_selected_tile_disarms_the_tool_too(panel):
    widget, session, interaction = panel
    (alice,) = _add(session, "Alice")
    widget._on_tile_clicked(alice.id)
    interaction.set_tool(Tool.TOGETHER)

    widget._on_tile_clicked(alice.id)

    assert interaction.selected_student_id is None
    assert interaction.active_tool is None


def test_clicking_another_tile_selects_it_when_no_tool_is_armed(panel):
    widget, session, interaction = panel
    alice, bob = _add(session, "Alice", "Bob")
    widget._on_tile_clicked(alice.id)

    widget._on_tile_clicked(bob.id)

    assert interaction.selected_student_id == bob.id


def test_clicking_another_tile_toggles_a_relation_when_a_tool_is_armed(panel):
    widget, session, interaction = panel
    alice, bob = _add(session, "Alice", "Bob")
    widget._on_tile_clicked(alice.id)
    interaction.set_tool(Tool.TOGETHER)

    widget._on_tile_clicked(bob.id)

    assert session.relation_between(alice.id, bob.id) is not None
    assert interaction.selected_student_id == alice.id
    assert interaction.active_tool is Tool.TOGETHER


def test_clicking_the_same_target_twice_removes_the_relation(panel):
    widget, session, interaction = panel
    alice, bob = _add(session, "Alice", "Bob")
    widget._on_tile_clicked(alice.id)
    interaction.set_tool(Tool.TOGETHER)
    widget._on_tile_clicked(bob.id)

    widget._on_tile_clicked(bob.id)

    assert session.relation_between(alice.id, bob.id) is None
    assert interaction.selected_student_id == alice.id
    assert interaction.active_tool is Tool.TOGETHER


def test_clicking_the_empty_area_of_the_list_deselects(panel):
    widget, session, interaction = panel
    (alice,) = _add(session, "Alice")
    widget._on_tile_clicked(alice.id)

    _click_background(widget, widget._list)

    assert interaction.selected_student_id is None


def test_clicking_the_canvas_beneath_the_tiles_deselects(panel):
    """Zone du canevas non couverte par le cadre de contenu (peu de tuiles)."""
    widget, session, interaction = panel
    (alice,) = _add(session, "Alice")
    widget._on_tile_clicked(alice.id)

    _click_background(widget, widget._list._parent_canvas)

    assert interaction.selected_student_id is None


def test_background_click_disarms_the_tool(panel):
    widget, session, interaction = panel
    (alice,) = _add(session, "Alice")
    widget._on_tile_clicked(alice.id)
    interaction.set_tool(Tool.EXCLUDE)

    _click_background(widget, widget._list)

    assert interaction.selected_student_id is None
    assert interaction.active_tool is None


def test_clicking_inside_the_inspector_never_deselects(panel):
    """Le point signalé : le fond du panneau de détail ne doit jamais désélectionner."""
    widget, session, interaction = panel
    (alice,) = _add(session, "Alice")
    widget._on_tile_clicked(alice.id)
    interaction.set_tool(Tool.TOGETHER)

    _click_background(widget, widget._inspector)

    assert interaction.selected_student_id == alice.id
    assert interaction.active_tool is Tool.TOGETHER


def test_clicking_the_inspectors_scrollable_body_never_deselects(panel):
    widget, session, interaction = panel
    (alice,) = _add(session, "Alice")
    widget._on_tile_clicked(alice.id)
    interaction.set_tool(Tool.TOGETHER)

    _click_background(widget, widget._inspector._body._parent_canvas)

    assert interaction.selected_student_id == alice.id
    assert interaction.active_tool is Tool.TOGETHER
