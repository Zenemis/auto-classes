"""Notification observateur minimale, pour découpler le modèle de session des vues."""

from collections.abc import Callable
from typing import Any


class Signal:
    """Liste d'abonnés appelés à chaque `emit`.

    Volontairement minimal : pas de désabonnement automatique, les vues vivent aussi
    longtemps que la fenêtre. Les abonnés détruits doivent se désabonner via
    `disconnect` (cf. `views.student_inspector`).
    """

    def __init__(self, name: str = "") -> None:
        self.name = name
        self._subscribers: list[Callable[..., None]] = []

    def connect(self, subscriber: Callable[..., None]) -> None:
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)

    def disconnect(self, subscriber: Callable[..., None]) -> None:
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    def emit(self, *args: Any) -> None:
        for subscriber in list(self._subscribers):
            subscriber(*args)
