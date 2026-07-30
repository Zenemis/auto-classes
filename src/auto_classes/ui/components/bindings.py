"""Aides de binding Tk pour rendre un bloc composite cliquable d'un seul tenant."""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

INTERACTIVE_WIDGETS = (ctk.CTkButton, ctk.CTkEntry, ctk.CTkTextbox, ctk.CTkScrollbar)
"""Widgets qui gèrent déjà leurs propres clics : leur sous-arbre n'est jamais rebindé."""


def bind_recursive(widget: tk.Misc, sequence: str, callback: Callable[[tk.Event], None]) -> None:
    """Binde `sequence` sur `widget` et toute sa descendance.

    Une carte CustomTkinter est un empilement frame + canvas + labels : sans cette
    propagation, un clic sur le texte d'une carte ne déclenche rien.
    """
    widget.bind(sequence, callback, add="+")
    for child in widget.winfo_children():
        if isinstance(child, INTERACTIVE_WIDGETS):
            continue
        bind_recursive(child, sequence, callback)


def set_cursor_recursive(widget: tk.Misc, cursor: str) -> None:
    for target in (widget, *_descendants(widget)):
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


def _descendants(widget: tk.Misc) -> list[tk.Misc]:
    found: list[tk.Misc] = []
    for child in widget.winfo_children():
        if isinstance(child, INTERACTIVE_WIDGETS):
            continue
        found.append(child)
        found += _descendants(child)
    return found
