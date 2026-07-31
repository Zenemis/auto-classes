"""Racine Tk partagée par tous les tests de `tests/ui`.

CustomTkinter garde un état global (suivi de l'échelle, du thème) que la création
répétée de racines `ctk.CTk()` dans le même processus met en défaut — un `ctk.CTk()`
sur deux ou trois lève parfois `TclError: invalid command name "tcl_findLibrary"`,
selon l'ordre de collecte des modules. Une seule racine pour toute la session élimine
la source du problème plutôt que de la contourner module par module.

Mappée hors champ (pas masquée) : `event_generate` ne délivre jamais d'évènement à une
fenêtre `withdraw()`ée, et certains tests ont besoin de vrais clics.
"""

import tkinter as tk

import customtkinter as ctk
import pytest


@pytest.fixture(scope="session")
def root():
    try:
        window = ctk.CTk()
    except tk.TclError as error:
        pytest.skip(f"pas d'affichage disponible : {error}")
    window.geometry("900x700+2000+2000")
    window.update()
    try:
        yield window
    finally:
        window.destroy()
