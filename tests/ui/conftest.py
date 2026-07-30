import tkinter

import pytest


@pytest.fixture
def tk_root():
    """Racine Tk éphémère, pour les rares objets qui en exigent une (`CTkImage`).

    Ignore le test plutôt que d'échouer là où aucun affichage n'est disponible.
    """
    try:
        root = tkinter.Tk()
    except tkinter.TclError as error:
        pytest.skip(f"pas d'affichage disponible : {error}")

    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()
