"""Aides de binding Tk pour rendre un bloc composite cliquable d'un seul tenant."""

from collections.abc import Callable, Iterator

import customtkinter as ctk
import tkinter as tk

INTERACTIVE_WIDGETS = (ctk.CTkButton, ctk.CTkEntry, ctk.CTkTextbox, ctk.CTkScrollbar)
"""Widgets qui gèrent déjà leurs propres clics : leur sous-arbre n'est jamais rebindé."""

CONTAINERS = (ctk.CTkFrame, ctk.CTkScrollableFrame)
"""Widgets CTk dans lesquels il faut descendre pour atteindre les enfants réels."""


def _forwards_to_internals(widget: tk.Misc) -> bool:
    """Vrai si `bind` sur ce widget atteint déjà toutes ses parties internes.

    Un `CTkLabel` est un empilement canvas + label Tk, et son `bind` relaie sur les
    deux. Mais contrairement à `CTkFrame`, il expose aussi ces parties dans
    `winfo_children()` : y redescendre poserait un second gestionnaire sur chacune, et
    le moindre clic déclencherait deux fois. Invisible tant qu'une action est
    idempotente, fatal dès qu'elle bascule — poser puis retirer aussitôt.
    """
    return isinstance(widget, ctk.CTkBaseClass) and not isinstance(widget, CONTAINERS)


def _subtree(widget: tk.Misc) -> Iterator[tk.Misc]:
    """Widget et descendance à traiter, en s'arrêtant aux widgets auto-suffisants."""
    yield widget
    if _forwards_to_internals(widget):
        return
    for child in widget.winfo_children():
        if isinstance(child, INTERACTIVE_WIDGETS):
            continue
        yield from _subtree(child)


def bind_recursive(widget: tk.Misc, sequence: str, callback: Callable[[tk.Event], None]) -> None:
    """Binde `sequence` sur `widget` et sur ce qu'il faut de sa descendance.

    Une carte CustomTkinter est un empilement frame + canvas + libellés : sans cette
    propagation, un clic sur le texte d'une carte ne déclencherait rien.
    """
    for target in _subtree(widget):
        target.bind(sequence, callback, add="+")


def set_cursor_recursive(widget: tk.Misc, cursor: str) -> None:
    for target in _subtree(widget):
        try:
            target.configure(cursor=cursor)
        except tk.TclError:
            pass  # certains widgets CTk internes n'exposent pas l'option cursor


def contains_widget(container: tk.Misc, widget: tk.Misc | None) -> bool:
    """Vrai si `widget` appartient au sous-arbre de `container`.

    Les chemins Tk étant hiérarchiques, la comparaison de préfixe suffit et évite de
    remonter la chaîne des masters (que les widgets CTk internes cassent parfois).
    """
    if widget is None:
        return False
    return str(widget) == str(container) or str(widget).startswith(f"{container}.")


def event_widget(event: tk.Event) -> tk.Misc | None:
    """Le widget réellement ciblé par `event`, ou None si Tk n'a pas pu le résoudre.

    Un gestionnaire spécifique au widget cliqué (celui d'une carte, par exemple) peut
    détruire et reconstruire ce widget — c'est le cas quand cliquer une carte l'ouvre
    en édition. Si un second gestionnaire pour le même clic tourne ensuite (un clic
    global lié par `bind_all`), Tk ne peut plus retrouver l'objet Python correspondant
    et laisse `event.widget` sous forme de chemin brut (une chaîne) plutôt qu'un
    widget — d'où ce filtre, à appeler avant toute méthode `winfo_*`.
    """
    widget = event.widget
    return None if isinstance(widget, str) else widget
