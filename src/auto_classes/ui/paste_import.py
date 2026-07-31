"""Import d'élèves par collage (Ctrl+V) d'un tableau copié depuis Pronote.

La page Pronote se copie dans le presse-papiers sous forme de colonnes séparées par des
tabulations, en-tête compris : c'est un CSV, et c'est le même lecteur qui s'en charge.

Deux règles gouvernent ce module :

- **Un collage raté ne dit rien.** Ctrl+V sert à mille choses ; l'immense majorité des
  collages ne sont pas des listes d'élèves. Ouvrir une fenêtre d'erreur à chaque
  presse-papiers qui n'est pas un tableau Pronote rendrait le raccourci insupportable.
  Seul un collage *réussi* se manifeste.
- **La saisie de texte garde la priorité.** Un Ctrl+V dans un champ (renommer un élève,
  le mot de passe Pronote) doit coller du texte, pas déclencher un import.
"""

import tkinter as tk

from auto_classes.serialization import CsvImport, CsvImportError, parse_students_csv


def students_from_clipboard(text: str | None) -> CsvImport | None:
    """Élèves lus dans un presse-papiers, ou None si ce n'était pas une liste.

    Toute la politique d'échec silencieux tient dans cette signature : il n'y a pas
    d'erreur à afficher, seulement une absence de résultat.
    """
    if not text:
        return None
    try:
        return parse_students_csv(text)
    except CsvImportError:
        return None


def is_text_input(widget: object) -> bool:
    """Vrai si le widget attend de la saisie et doit donc traiter Ctrl+V lui-même.

    Le test porte sur les widgets Tk sous-jacents : un `CTkEntry` n'a jamais le focus
    lui-même, il le donne au `tk.Entry` qu'il enveloppe.
    """
    return isinstance(widget, (tk.Entry, tk.Text, tk.Spinbox))
