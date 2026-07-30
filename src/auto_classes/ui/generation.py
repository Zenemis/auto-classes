"""Pont entre l'UI et `algorithm.generate_classes`.

Le backtracking peut durer plusieurs secondes : il tourne dans un thread pour ne pas
geler la boucle Tk. Le résultat traverse une `Queue` que le thread UI relève avec
`after` — appeler `after` depuis le thread de calcul reviendrait à toucher à
l'interpréteur Tk depuis l'extérieur de sa boucle (et lève « main thread is not in
main loop »).
"""

import queue
import threading
import time
from dataclasses import dataclass, field

import customtkinter as ctk

from auto_classes.algorithm import generate_classes
from auto_classes.core import ClassroomSet
from auto_classes.ui.session import SessionState
from auto_classes.ui.signal import Signal


@dataclass(frozen=True)
class GenerationResult:
    """Issue d'une génération : propositions trouvées, durée, éventuelle erreur backend."""

    proposals: list[ClassroomSet] = field(default_factory=list)
    duration: float = 0.0
    requested: int = 0
    error: str | None = None

    @property
    def is_empty(self) -> bool:
        return not self.proposals


POLL_INTERVAL_MS = 60


class GenerationController:
    """Séquence une génération à la fois et diffuse son avancement."""

    def __init__(self, widget: ctk.CTkBaseClass, session: SessionState) -> None:
        self._widget = widget
        self._session = session
        self._thread: threading.Thread | None = None
        self._results: queue.Queue[GenerationResult] = queue.Queue()

        self.started = Signal("generation_started")
        self.finished = Signal("generation_finished")

    @property
    def is_running(self) -> bool:
        """Vraie tant que le résultat n'a pas été relevé, thread terminé ou non."""
        return self._thread is not None

    def start(self) -> list[str]:
        """Lance la génération. Renvoie les problèmes bloquants ; liste vide = démarré.

        Les données du backend sont converties ici, sur le thread UI, pour que le thread
        de calcul ne voie qu'un instantané immuable de la session.
        """
        if self.is_running:
            return ["Une génération est déjà en cours."]

        problems = self._session.validate()
        if problems:
            return problems

        students = self._session.core_students()
        classrooms = self._session.core_classrooms()
        constraint = self._session.build_constraint()
        requested = self._session.num_solutions

        self.started.emit()
        self._thread = threading.Thread(
            target=self._work,
            args=(students, classrooms, constraint, requested),
            name="auto-classes-generate",
            daemon=True,
        )
        self._thread.start()
        self._widget.after(POLL_INTERVAL_MS, self._poll)
        return []

    def _work(self, students, classrooms, constraint, requested: int) -> None:
        """Exécuté dans le thread de calcul : ne touche ni widget ni signal."""
        started_at = time.perf_counter()
        try:
            proposals = generate_classes(students, classrooms, constraint, requested)
            error = None
        except Exception as exception:  # remonté tel quel dans l'UI, jamais avalé
            proposals, error = [], f"{type(exception).__name__} : {exception}"

        self._results.put(
            GenerationResult(
                proposals=proposals,
                duration=time.perf_counter() - started_at,
                requested=requested,
                error=error,
            )
        )

    def _poll(self) -> None:
        """Relève le résultat sur le thread UI, seul autorisé à émettre les signaux."""
        thread = self._thread
        if thread is None:
            return

        try:
            result = self._results.get_nowait()
        except queue.Empty:
            if thread.is_alive():
                self._widget.after(POLL_INTERVAL_MS, self._poll)
                return
            # Thread mort sans résultat : impossible via `_work`, mais mieux vaut
            # relâcher le contrôleur que rester bloqué en « génération en cours ».
            result = GenerationResult(error="La génération s'est interrompue sans résultat.")

        self._thread = None
        self.finished.emit(result)
