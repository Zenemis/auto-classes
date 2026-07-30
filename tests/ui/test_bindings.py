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


@pytest.fixture(scope="module")
def window():
    """Une seule racine Tk pour tout le module.

    CustomTkinter garde un état global (suivi de l'échelle, du thème) que la création
    répétée de racines dans un même processus met en défaut — d'où une racine unique,
    et des widgets neufs à chaque test.
    """
    try:
        root = ctk.CTk()
    except tk.TclError as error:
        pytest.skip(f"pas d'affichage disponible : {error}")
    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def root(window):
    """Conteneur vierge par test, sous la racine partagée."""
    holder = ctk.CTkFrame(window)
    yield holder
    holder.destroy()


def handlers(widget: tk.Misc) -> int:
    """Nombre de gestionnaires attachés à ce widget Tk précis."""
    return (tk.Misc.bind(widget, SEQUENCE) or "").count("if {")


def noop(_event: tk.Event) -> None:
    pass


def test_frame_is_bound_once(root):
    frame = ctk.CTkFrame(root)
    bind_recursive(frame, SEQUENCE, noop)
    assert handlers(frame._canvas) == 1


def test_label_internals_are_bound_once_each(root):
    """Le piège : CTkLabel relaie déjà `bind`, tout en exposant ses parties."""
    frame = ctk.CTkFrame(root)
    label = ctk.CTkLabel(frame, text="Alice")
    label.pack()

    bind_recursive(frame, SEQUENCE, noop)

    assert handlers(label._canvas) == 1
    assert handlers(label._label) == 1


def test_nested_frames_are_all_reached(root):
    outer = ctk.CTkFrame(root)
    inner = ctk.CTkFrame(outer)
    label = ctk.CTkLabel(inner, text="Bob")
    label.pack()
    inner.pack()

    bind_recursive(outer, SEQUENCE, noop)

    assert handlers(outer._canvas) == 1
    assert handlers(inner._canvas) == 1
    assert handlers(label._label) == 1


def test_interactive_widgets_are_left_alone(root):
    """Un bouton gère ses propres clics : le rebinder déclencherait deux actions."""
    frame = ctk.CTkFrame(root)
    button = ctk.CTkButton(frame, text="Supprimer")
    entry = ctk.CTkEntry(frame)
    button.pack()
    entry.pack()

    bind_recursive(frame, SEQUENCE, noop)

    assert handlers(button._canvas) == 0
    assert handlers(entry._entry) == 0


def test_binding_new_children_does_not_pile_up_on_the_container(root):
    """Rebinder les enfants recréés ne doit pas ajouter un gestionnaire au conteneur."""
    container = ctk.CTkFrame(root)
    bind_recursive(container, SEQUENCE, noop)

    for _ in range(5):
        for child in container.winfo_children():
            child.destroy()
        badge = ctk.CTkLabel(container, text="●")
        badge.pack()
        bind_recursive(badge, SEQUENCE, noop)

        assert handlers(container._canvas) == 1
        assert handlers(badge._label) == 1


def test_rebinding_the_same_widget_does_pile_up(root):
    """Garde-fou : `add="+"` empile bel et bien, d'où la règle de ne binder qu'une fois."""
    frame = ctk.CTkFrame(root)
    bind_recursive(frame, SEQUENCE, noop)
    bind_recursive(frame, SEQUENCE, noop)
    assert handlers(frame._canvas) == 2
