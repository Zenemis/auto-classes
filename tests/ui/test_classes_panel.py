"""Ouverture et fermeture du formulaire de classe par clic.

Cliquer une carte l'ouvre en édition ; cliquer n'importe où ailleurs dans la bande la
referme. La carte cliquée se détruit *pendant* son propre clic (elle devient le
formulaire) — un piège pour tout gestionnaire qui traiterait ce même clic ensuite,
couvert ici par les tests de régression en bas de fichier.
"""

import pytest

from auto_classes.ui.interaction import InteractionState
from auto_classes.ui.session import SessionState
from auto_classes.ui.views.classes_panel import ClassesPanel
from auto_classes.ui.views.classroom_editor import ClassroomEditor
from auto_classes.ui.views.students_panel import StudentsPanel


@pytest.fixture
def panel(root):
    session = SessionState()
    widget = ClassesPanel(root, session)
    widget.pack(fill="both", expand=True)
    root.update()
    yield widget, session
    widget.destroy()
    root.update()


def _click(panel_widget, target, x=5, y=5):
    """Clic réel ; `update()` avant et après pour que la mise en page ait tourné."""
    root = panel_widget.winfo_toplevel()
    root.update()
    canvas = getattr(target, "_canvas", target)
    canvas.event_generate("<Button-1>", x=x, y=y)
    root.update()


def _editors(panel_widget):
    return [w for w in panel_widget._strip.winfo_children() if isinstance(w, ClassroomEditor)]


def _cards(panel_widget):
    from auto_classes.ui.views.classes_panel import ClassroomCard

    return [w for w in panel_widget._strip.winfo_children() if isinstance(w, ClassroomCard)]


def test_clicking_a_card_opens_its_editor(panel):
    widget, session = panel
    room = session.add_classroom("6e A")

    widget._edit_classroom(room.id)

    assert widget._editing_id == room.id
    assert len(_editors(widget)) == 1


def test_clicking_the_bands_own_background_closes_the_editor(panel):
    widget, session = panel
    room = session.add_classroom("6e A")
    widget._edit_classroom(room.id)

    _click(widget, widget, y=widget.winfo_height() - 3)

    assert widget._editing_id is None
    assert _editors(widget) == []


def test_clicking_the_strips_blank_area_closes_the_editor(panel):
    """À droite des cartes, dans la partie du bandeau qui défile horizontalement."""
    widget, session = panel
    room = session.add_classroom("6e A")
    widget._edit_classroom(room.id)

    _click(widget, widget._strip, x=widget._strip.winfo_width() - 5, y=20)

    assert widget._editing_id is None


def test_clicking_the_canvas_beneath_the_strip_closes_the_editor(panel):
    widget, session = panel
    room = session.add_classroom("6e A")
    widget._edit_classroom(room.id)

    _click(widget, widget._strip._parent_canvas, x=widget._strip.winfo_width() - 5, y=20)

    assert widget._editing_id is None


def test_background_click_does_nothing_when_no_editor_is_open(panel):
    """Ne doit pas planter, ni reconstruire la bande inutilement, quand rien n'édite."""
    widget, session = panel
    session.add_classroom("6e A")

    _click(widget, widget, y=widget.winfo_height() - 3)

    assert widget._editing_id is None


def test_clicking_another_card_switches_the_editor_without_closing_it(panel):
    widget, session = panel
    first = session.add_classroom("6e A")
    second = session.add_classroom("6e B")
    widget._edit_classroom(first.id)

    other_card = next(c for c in _cards(widget) if c.classroom_id == second.id)
    _click(widget, other_card)

    assert widget._editing_id == second.id
    assert len(_editors(widget)) == 1


class TestRegressionAgainstTheStudentGlobalHandler:
    """`StudentsPanel` écoute *tous* les clics de la fenêtre pour désélectionner un
    élève. Cliquer une carte de classe détruit cette carte au même clic (elle devient
    un formulaire) : si `StudentsPanel` traite ensuite ce même évènement, il reçoit un
    `event.widget` que Tk ne peut plus résoudre — une chaîne, pas un widget — et
    plantait avant l'ajout du filtre `event_widget`. Les deux bandes doivent coexister
    ici, comme dans la vraie fenêtre, pour que ce risque soit réellement couvert.

    Limite connue, pas un bug : quand un widget se détruit lui-même en réponse à son
    propre clic, Tk abandonne la suite du parcours des étiquettes de liaison pour cet
    évènement — les gestionnaires attachés à « all » (dont celui de `StudentsPanel`)
    ne s'exécutent alors tout simplement pas. Cliquer une carte de classe n'annule donc
    pas la sélection d'élève en cours ; ça ne plante pas non plus, ce qui est ce qui
    compte ici.
    """

    @pytest.fixture
    def both_panels(self, root):
        session = SessionState()
        interaction = InteractionState()
        students = StudentsPanel(root, session, interaction)
        classes = ClassesPanel(root, session)
        students.pack(fill="both", expand=True)
        classes.pack(fill="both", expand=True)
        root.update()
        yield classes, students, session, interaction
        students.destroy()
        classes.destroy()
        root.update()

    def test_clicking_a_classroom_card_does_not_crash_the_student_handler(self, both_panels):
        classes, _students, session, _interaction = both_panels
        room = session.add_classroom("6e A")

        card = next(c for c in _cards(classes) if c.classroom_id == room.id)
        _click(classes, card)  # ne doit lever aucune exception

        assert classes._editing_id == room.id

    def test_clicking_a_plain_sibling_still_deselects_the_student(self, both_panels):
        """Le cas courant (un widget qui ne se détruit pas lui-même) continue de
        fonctionner : seule la combinaison « widget qui se détruit à son propre clic »
        échappe au gestionnaire global, pas le mécanisme dans son ensemble."""
        classes, students, session, interaction = both_panels
        alice = session.add_student("Alice")
        students._on_tile_clicked(alice.id)

        _click(classes, classes._header)  # zone de classes, mais qui ne se détruit pas

        assert interaction.selected_student_id is None
