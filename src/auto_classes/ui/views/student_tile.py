"""Tuile d'un élève dans la liste : nom tronqué, pastilles de contraintes, états visuels."""

from collections.abc import Callable

import tkinter as tk

from auto_classes.ui.components import ClickableCard, CountBadge, EllipsizedLabel, Group
from auto_classes.ui.components.chips import RELATION_COLORS, TAG_RULE_COLORS
from auto_classes.ui.models import RelationKind, StudentModel, TagRuleKind
from auto_classes.ui.session import SessionState
from auto_classes.ui.theme import Color, Fonts, Metrics, Palette


class StudentTile(ClickableCard):
    """Une tuile par élève, réutilisée d'un rafraîchissement à l'autre.

    Étroite à dessein : une classe de plus de cent élèves doit rester lisible d'un
    coup d'œil. Le nom est donc tronqué, et les contraintes réduites à une pastille
    colorée par type — le détail chiffré vit dans l'inspecteur.

    Reconstruire toutes les tuiles à chaque ajout de contrainte serait perceptible sur
    une centaine d'élèves : `refresh` remet à jour le contenu sans recréer le widget.
    """

    def __init__(
        self,
        master: tk.Misc,
        student: StudentModel,
        session: SessionState,
        on_click: Callable[[str], None],
    ) -> None:
        super().__init__(
            master,
            on_click=lambda: on_click(student.id),
            width=Metrics.STUDENT_TILE_WIDTH,
            height=Metrics.STUDENT_TILE_HEIGHT,
        )

        self.student_id = student.id
        self._session = session

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        # La ligne des pastilles absorbe le vide : sans cela, une tuile sans contrainte
        # centrerait son nom verticalement alors que les autres l'alignent en haut.
        self.grid_rowconfigure(1, weight=1)

        self._name = EllipsizedLabel(
            self,
            text=student.name,
            font=Fonts.body_bold(),
            text_color=Palette.TEXT,
            anchor="w",
            # La largeur utile est celle de la tuile, moins ses marges gauche et droite.
            width_source=self,
            width_margin=2 * Metrics.PAD_SM + 4,
        )
        self._name.grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_SM, pady=(Metrics.PAD_SM, 0))

        self._badges = Group(self)
        self._badges.grid(row=1, column=0, sticky="ew", padx=Metrics.PAD_SM, pady=(0, Metrics.PAD_SM))

        # Bindings d'abord, contenu ensuite : `refresh` ne rebinde que la zone des pastilles.
        self.activate()
        self.refresh()

    def set_accent(self, accent: Color | None, *, filled: bool = False) -> None:
        super().set_accent(accent, filled=filled)
        # Le nom reprend la couleur de l'outil quand la contrainte est déjà posée :
        # la bordure seule se remarque mal sur une tuile de cette taille.
        self._name.configure(
            text_color=accent if accent is not None and filled else Palette.TEXT
        )

    def refresh(self) -> None:
        student = self._session.student(self.student_id)
        if student is None:
            return

        self._name.set_text(student.name)
        for child in self._badges.winfo_children():
            child.destroy()

        for count, accent in self._badge_counts():
            CountBadge(self._badges, count, accent).pack(side="left", padx=(0, Metrics.PAD_XS))

        # Ne binder que les pastilles fraîchement créées. Repasser sur `_badges`
        # lui-même empilerait un gestionnaire de plus à chaque rafraîchissement
        # (`add="+"`), et un clic sur cette zone basculerait la contrainte autant de
        # fois qu'il y a de gestionnaires : posée, retirée, posée…
        for badge in self._badges.winfo_children():
            self.activate(badge)

    def _badge_counts(self) -> list[tuple[int, Color]]:
        """Une pastille par type de contrainte présent, dans un ordre stable."""
        counts: list[tuple[int, Color]] = []

        relations = self._session.relations_of(self.student_id)
        for kind in RelationKind:
            total = sum(1 for relation in relations if relation.kind is kind)
            if total:
                counts.append((total, RELATION_COLORS[kind]))

        rules = self._session.tag_rules_of(self.student_id)
        for tag_kind in TagRuleKind:
            total = sum(1 for rule in rules if rule.kind is tag_kind)
            if total:
                counts.append((total, TAG_RULE_COLORS[tag_kind]))

        return counts
