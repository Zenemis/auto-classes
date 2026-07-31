"""Un clic sur une carte composite ne doit déclencher son action qu'une fois.

Tk ne délivre pas d'évènement dans une fenêtre non affichée : impossible de simuler
un vrai clic ici. On vérifie donc l'invariant qui le garantit — un seul gestionnaire
attaché à chaque partie cliquable — ce qui est précisément ce qui avait dérivé.
"""

import tkinter as tk

import customtkinter as ctk
import pytest

from auto_classes.ui.components.bindings import bind_recursive

SEQUENCE = "<Button-1>"


@pytest.fixture
def container(root):
    """Conteneur vierge par test, sous la racine partagée (`conftest.py`)."""
    holder = ctk.CTkFrame(root)
    yield holder
    holder.destroy()


def handlers(widget: tk.Misc) -> int:
    """Nombre de gestionnaires attachés à ce widget Tk précis."""
    return (tk.Misc.bind(widget, SEQUENCE) or "").count("if {")


def noop(_event: tk.Event) -> None:
    pass


def test_frame_is_bound_once(container):
    frame = ctk.CTkFrame(container)
    bind_recursive(frame, SEQUENCE, noop)
    assert handlers(frame._canvas) == 1


def test_label_internals_are_bound_once_each(container):
    """Le piège : CTkLabel relaie déjà `bind`, tout en exposant ses parties."""
    frame = ctk.CTkFrame(container)
    label = ctk.CTkLabel(frame, text="Alice")
    label.pack()

    bind_recursive(frame, SEQUENCE, noop)

    assert handlers(label._canvas) == 1
    assert handlers(label._label) == 1


def test_nested_frames_are_all_reached(container):
    outer = ctk.CTkFrame(container)
    inner = ctk.CTkFrame(outer)
    label = ctk.CTkLabel(inner, text="Bob")
    label.pack()
    inner.pack()

    bind_recursive(outer, SEQUENCE, noop)

    assert handlers(outer._canvas) == 1
    assert handlers(inner._canvas) == 1
    assert handlers(label._label) == 1


def test_interactive_widgets_are_left_alone(container):
    """Un bouton gère ses propres clics : le rebinder déclencherait deux actions."""
    frame = ctk.CTkFrame(container)
    button = ctk.CTkButton(frame, text="Supprimer")
    entry = ctk.CTkEntry(frame)
    button.pack()
    entry.pack()

    bind_recursive(frame, SEQUENCE, noop)

    assert handlers(button._canvas) == 0
    assert handlers(entry._entry) == 0


def test_binding_new_children_does_not_pile_up_on_the_container(container):
    """Rebinder les enfants recréés ne doit pas ajouter un gestionnaire au conteneur."""
    container = ctk.CTkFrame(container)
    bind_recursive(container, SEQUENCE, noop)

    for _ in range(5):
        for child in container.winfo_children():
            child.destroy()
        badge = ctk.CTkLabel(container, text="●")
        badge.pack()
        bind_recursive(badge, SEQUENCE, noop)

        assert handlers(container._canvas) == 1
        assert handlers(badge._label) == 1


def test_rebinding_the_same_widget_does_pile_up(container):
    """Garde-fou : `add="+"` empile bel et bien, d'où la règle de ne binder qu'une fois."""
    frame = ctk.CTkFrame(container)
    bind_recursive(frame, SEQUENCE, noop)
    bind_recursive(frame, SEQUENCE, noop)
    assert handlers(frame._canvas) == 2
