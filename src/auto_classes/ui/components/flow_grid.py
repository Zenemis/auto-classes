"""Grille défilante qui re-répartit ses tuiles en colonnes selon la largeur disponible."""

import tkinter as tk

from auto_classes.ui.components.surfaces import ScrollArea
from auto_classes.ui.theme import Metrics


class FlowGrid(ScrollArea):
    """Conteneur défilant vertical dont les tuiles s'écoulent sur autant de colonnes
    que la largeur le permet.

    Le cycle de vie des tuiles appartient à l'appelant : les widgets sont créés avec
    cette grille comme parent, puis confiés à `set_tiles` qui ne fait que les placer.
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        min_tile_width: int = Metrics.STUDENT_TILE_WIDTH,
        gap: int = Metrics.PAD_SM,
        spread: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(master, **kwargs)

        self._min_tile_width = min_tile_width
        self._gap = gap
        self._spread = spread
        self._tiles: list[tk.Widget] = []
        self._columns = 0
        self._dirty = False

        # add="+" : CTkScrollableFrame binde déjà <Configure> pour sa zone de défilement.
        self.bind("<Configure>", self._on_configure, add="+")

    def set_tiles(self, tiles: list[tk.Widget]) -> None:
        """Place `tiles` dans cet ordre et retire de la grille celles qui n'y sont plus."""
        for tile in self._tiles:
            if tile not in tiles and tile.winfo_exists():
                tile.grid_remove()
        self._tiles = list(tiles)
        self._dirty = True
        self._relayout()

    def _on_configure(self, _event: tk.Event) -> None:
        self._relayout()

    def _column_count(self, width: int) -> int:
        """`width` vient de `winfo_width` : des pixels physiques.

        Les largeurs de `Metrics` sont logiques, et CustomTkinter met les deux à
        l'échelle de l'écran (125 % sous Windows, par exemple) : comparer les deux
        sans conversion donnerait une colonne de trop.
        """
        step = self._apply_widget_scaling(self._min_tile_width + self._gap)
        return max(1, int((width + self._apply_widget_scaling(self._gap)) // step))

    def _relayout(self) -> None:
        width = self.winfo_width()
        if width <= 1:
            # Géométrie pas encore calculée (grille non encore affichée) : ne rien faire,
            # `_dirty` garde la trace du travail en attente et <Configure> rappellera
            # dès que Tk aura donné une largeur à la grille.
            return

        columns = self._column_count(width)
        if self._spread and self._tiles:
            # Peu de tuiles : les étaler sur toute la largeur plutôt que de laisser un
            # grand vide à droite (deux classes doivent occuper deux demi-largeurs).
            columns = min(columns, len(self._tiles))
        if columns == self._columns and not self._dirty:
            return

        if columns != self._columns:
            # Les colonnes devenues inutiles doivent quitter le groupe `uniform` : y
            # laisser une colonne de poids 0 empêche Tk de répartir l'espace restant
            # entre les colonnes actives, qui restent alors collées à gauche.
            for index in range(max(columns, self._columns)):
                if index < columns:
                    self.grid_columnconfigure(index, weight=1, uniform="flow-tile")
                else:
                    self.grid_columnconfigure(index, weight=0, uniform="")
            self._columns = columns

        self._dirty = False
        for position, tile in enumerate(self._tiles):
            if not tile.winfo_exists():
                continue
            tile.grid(
                row=position // columns,
                column=position % columns,
                sticky="new",
                padx=(0, self._gap),
                pady=(0, self._gap),
            )
