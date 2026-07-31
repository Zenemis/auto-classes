"""Fenêtre principale : assemble les deux onglets autour de l'état de session.

`App` est le seul point où les objets partagés (session, interaction, génération) sont
créés, et le seul endroit qui connaît les deux onglets à la fois.
"""

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from auto_classes.pronote import Roster
from auto_classes.serialization import CsvImport, CsvImportError, load_students_csv
from auto_classes.ui.components import NoticeDialog
from auto_classes.ui.generation import GenerationController, GenerationResult
from auto_classes.ui.interaction import InteractionState
from auto_classes.ui.models import StudentModel
from auto_classes.ui.session import SessionState
from auto_classes.ui.theme import Fonts, Metrics, Palette
from auto_classes.ui.views.pronote_dialog import PronoteDialog
from auto_classes.ui.views.results_tab import ResultsTab
from auto_classes.ui.views.setup_tab import SetupTab

TAB_SETUP = "Configuration"
TAB_RESULTS = "Propositions"


class App(ctk.CTk):
    """Fenêtre racine de l'application."""

    def __init__(self, session: SessionState | None = None) -> None:
        super().__init__()

        self.title("Auto Classes")
        self.geometry("1240x820")
        self.minsize(1000, 700)
        self.configure(fg_color=Palette.WINDOW)

        self.session = session if session is not None else SessionState()
        self.interaction = InteractionState()
        self.generation = GenerationController(self, self.session)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_tabs()

        self.generation.started.connect(self._on_generation_started)
        self.generation.finished.connect(self._on_generation_finished)

    # ------------------------------------------------------------------ montage

    def _build_tabs(self) -> None:
        self.tabs = ctk.CTkTabview(
            self,
            fg_color="transparent",
            corner_radius=Metrics.RADIUS_MD,
            border_width=0,
            # Onglet actif laissé en blanc : `CTkSegmentedButton` n'a qu'une couleur de
            # texte pour les deux états, un onglet coloré laisserait du texte blanc sur
            # les onglets inactifs. La couleur de marque vit dans les titres de bande.
            segmented_button_fg_color=Palette.SURFACE_ALT,
            segmented_button_selected_color=Palette.SURFACE,
            segmented_button_selected_hover_color=Palette.SURFACE,
            segmented_button_unselected_color=Palette.SURFACE_ALT,
            segmented_button_unselected_hover_color=Palette.HOVER,
            text_color=Palette.TEXT,
            anchor="w",
        )
        self.tabs._segmented_button.configure(font=Fonts.body_bold())
        self.tabs.grid(row=0, column=0, sticky="nsew", padx=Metrics.PAD_LG, pady=Metrics.PAD_LG)

        setup_frame = self.tabs.add(TAB_SETUP)
        results_frame = self.tabs.add(TAB_RESULTS)
        for frame in (setup_frame, results_frame):
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)

        self.setup_tab = SetupTab(
            setup_frame,
            self.session,
            self.interaction,
            on_import=self._on_import,
            on_pronote=self._on_pronote,
            on_generate=self.generate,
        )
        self.setup_tab.grid(row=0, column=0, sticky="nsew")

        self.results_tab = ResultsTab(results_frame, self.session, on_regenerate=self.generate)
        self.results_tab.grid(row=0, column=0, sticky="nsew")

        self.tabs.set(TAB_SETUP)

    # ---------------------------------------------------------------- réactions

    def generate(self) -> None:
        problems = self.generation.start()
        if problems:
            NoticeDialog.inform(self, "Génération impossible", "\n".join(problems))
            return
        self.tabs.set(TAB_RESULTS)

    def _on_generation_started(self) -> None:
        self.setup_tab.menu_bar.set_generating(True)
        self.results_tab.show_running()

    def _on_generation_finished(self, result: GenerationResult) -> None:
        self.setup_tab.menu_bar.set_generating(False)
        self.results_tab.show_result(result)

    def _on_import(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Importer une liste d'élèves",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return  # sélection annulée

        try:
            imported = load_students_csv(Path(path))
        except CsvImportError as error:
            NoticeDialog.inform(self, "Import impossible", str(error))
            return

        added, rejected = self.session.add_students(list(imported.names))
        NoticeDialog.inform(self, "Import CSV", _csv_summary(imported, added, rejected))

    def _on_pronote(self) -> None:
        roster = PronoteDialog(self).show()
        if roster is None:
            return  # connexion annulée

        added, rejected = self.session.add_students(roster.student_names)
        NoticeDialog.inform(self, "Import Pronote", _import_summary(roster, added, rejected))


def _plural(count: int) -> str:
    return "s" if count > 1 else ""


def _rejected_line(rejected: list[tuple[str, str]]) -> str:
    """Les refus viennent presque toujours de doublons : comptés, pas énumérés."""
    mark = _plural(len(rejected))
    return f"\n{len(rejected)} nom{mark} ignoré{mark} (déjà dans la liste)."


def _import_summary(
    roster: Roster, added: list[StudentModel], rejected: list[tuple[str, str]]
) -> str:
    """Compte rendu de l'import Pronote : ce qui est entré, et ce qui a été écarté."""
    class_names = ", ".join(student_class.name for student_class in roster.classes)
    mark = _plural(len(added))
    lines = [
        f"{len(added)} élève{mark} importé{mark} depuis "
        f"{len(roster.classes)} classe{_plural(len(roster.classes))} Pronote.",
        f"\nClasses lues : {class_names}.",
    ]
    if rejected:
        lines.append(_rejected_line(rejected))
    return "\n".join(lines)


def _csv_summary(
    imported: CsvImport, added: list[StudentModel], rejected: list[tuple[str, str]]
) -> str:
    """Compte rendu de l'import CSV, refus et lignes sans identité compris."""
    mark = _plural(len(added))
    lines = [f"{len(added)} élève{mark} importé{mark} depuis le fichier."]
    if rejected:
        lines.append(_rejected_line(rejected))
    if imported.skipped_rows:
        skipped_mark = _plural(imported.skipped_rows)
        lines.append(
            f"\n{imported.skipped_rows} ligne{skipped_mark} sans nom "
            f"ignorée{skipped_mark}."
        )
    return "\n".join(lines)


def run(session: SessionState | None = None) -> None:
    """Point d'entrée de l'UI : configure CustomTkinter puis lance la boucle Tk."""
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    App(session).mainloop()
