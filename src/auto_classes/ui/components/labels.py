"""Libellés à comportement particulier."""

from collections.abc import Callable

import customtkinter as ctk
import tkinter as tk

ELLIPSIS = "…"


def ellipsize(text: str, available: int, measure: Callable[[str], int]) -> str:
    """Plus long préfixe de `text` qui tient dans `available`, suivi de « … ».

    `measure` rend la largeur d'une chaîne dans l'unité de `available`. Renvoie `text`
    inchangé s'il tient déjà, et « … » seul si même un caractère ne rentre pas.
    """
    if measure(text) <= available:
        return text

    for cut in range(len(text) - 1, 0, -1):
        candidate = text[:cut].rstrip() + ELLIPSIS
        if measure(candidate) <= available:
            return candidate

    return ELLIPSIS


class EllipsizedLabel(ctk.CTkLabel):
    """Libellé qui tronque son texte et ajoute « … » quand la largeur manque.

    Tk ne tronque pas : un texte trop long est simplement rogné par les bords de son
    parent. La largeur utile ne peut pas non plus être lue sur le libellé lui-même —
    `grid` ne réduit jamais un widget en dessous de la taille qu'il réclame, donc
    `winfo_width()` renverrait la largeur du texte, pas celle de la place disponible.
    La mesure se fait donc sur le conteneur (`width_source`), dont la largeur est
    imposée par la mise en page.
    """

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        *,
        width_source: tk.Misc | None = None,
        width_margin: int = 0,
        **kwargs: object,
    ) -> None:
        super().__init__(master, text=text, **kwargs)

        self._full_text = text
        self._ellipsizing = False
        self._width_source = master if width_source is None else width_source
        self._width_margin = width_margin

        # Le conteneur annonce sa largeur définitive une fois la fenêtre affichée.
        self._width_source.bind("<Configure>", self._on_configure, add="+")

    @property
    def full_text(self) -> str:
        """Texte complet, indépendamment de ce qui est affiché."""
        return self._full_text

    def set_text(self, text: str) -> None:
        self._full_text = text
        self.configure(text=text)
        self._ellipsize()

    def _on_configure(self, _event: tk.Event) -> None:
        self._ellipsize()

    def _available_width(self) -> int:
        """Largeur utile en points de mise en page, l'unité des mesures de police.

        `CTkFont` configure la police Tk à sa taille *non* mise à l'échelle et ne
        l'applique qu'au rendu : `measure()` répond donc en points logiques, alors que
        `winfo_width()` répond en pixels physiques. C'est la largeur du conteneur qu'il
        faut ramener à l'échelle logique, sinon la coupe est calculée trop généreusement
        et le « … » se retrouve hors cadre.
        """
        width = self._reverse_widget_scaling(self._width_source.winfo_width())
        return round(width - self._width_margin)

    def _ellipsize(self) -> None:
        # `configure(text=...)` peut provoquer un <Configure> : sans ce garde-fou, la
        # première coupe relancerait la mesure en boucle.
        if self._ellipsizing:
            return

        available = self._available_width()
        if available <= 1:
            return  # conteneur pas encore dimensionné : <Configure> rappellera

        target = ellipsize(self._full_text, available, self.cget("font").measure)
        if target != self.cget("text"):
            self._ellipsizing = True
            try:
                self.configure(text=target)
            finally:
                self._ellipsizing = False
