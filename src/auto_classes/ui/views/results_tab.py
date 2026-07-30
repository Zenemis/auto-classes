"""Onglet 2 — Propositions : liste des propositions à gauche, détail agrandi à droite.

Maître/détail plutôt qu'une grille de petites cartes : le professeur balaie les
propositions d'un clic dans la colonne de gauche et étudie celle qui l'intéresse en
grand à droite, sans jamais perdre le contexte.
"""

import customtkinter as ctk
import tkinter as tk

from auto_classes.core import Classroom, ClassroomSet
from auto_classes.ui.components import (
    ClickableCard,
    EmptyState,
    FlowGrid,
    GhostButton,
    Group,
    Panel,
    ScrollArea,
    SectionHeader,
    TagPill,
)
from auto_classes.ui.generation import GenerationResult
from auto_classes.ui.session import SessionState
from auto_classes.ui.theme import Fonts, Icons, Metrics, Palette


class ProposalListItem(ClickableCard):
    """Vignette d'une proposition : son numéro et la taille de chaque classe."""

    def __init__(self, master: tk.Misc, index: int, proposal: ClassroomSet, on_select) -> None:
        super().__init__(master, on_click=lambda: on_select(index), base_color=Palette.SURFACE)
        self.index = index
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=f"Proposition {index + 1}",
            font=Fonts.body_bold(),
            text_color=Palette.TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_SM, 0))

        summary = " · ".join(f"{classroom.name} {len(classroom)}" for classroom in proposal)
        ctk.CTkLabel(
            self,
            text=summary,
            font=Fonts.small(),
            text_color=Palette.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=Metrics.PROPOSAL_LIST_WIDTH - 32,
        ).grid(row=1, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(2, Metrics.PAD_SM))

        self.activate()


class ClassroomResultCard(ctk.CTkFrame):
    """Une classe d'une proposition : nom, effectif, tags, et la liste de ses élèves."""

    def __init__(self, master: tk.Misc, classroom: Classroom, session: SessionState) -> None:
        super().__init__(
            master,
            fg_color=Palette.SURFACE,
            corner_radius=Metrics.RADIUS_SM,
            border_width=1,
            border_color=Palette.BORDER,
        )
        self.grid_columnconfigure(0, weight=1)

        header = Group(self)
        header.grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_MD, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text=classroom.name, font=Fonts.heading(), text_color=Palette.TEXT, anchor="w"
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            header,
            text=self._headcount_label(classroom, session),
            font=Fonts.small_bold(),
            text_color=Palette.TEXT_MUTED,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        if classroom.tags:
            tags = Group(self)
            tags.grid(row=1, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=(Metrics.PAD_SM, 0))
            for tag in sorted(classroom.tags, key=str.casefold):
                TagPill(tags, tag, color=Palette.SURFACE_ALT).pack(
                    side="left", padx=(0, Metrics.PAD_XS)
                )

        students = Group(self)
        students.grid(row=2, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=Metrics.PAD_MD)
        students.grid_columnconfigure(0, weight=1)

        names = sorted((student.name for student in classroom), key=str.casefold)
        if not names:
            ctk.CTkLabel(
                students, text="Classe vide", font=Fonts.italic(), text_color=Palette.TEXT_FAINT
            ).grid(row=0, column=0, sticky="w")
            return

        for row, name in enumerate(names):
            ctk.CTkLabel(
                students, text=name, font=Fonts.body(), text_color=Palette.TEXT, anchor="w"
            ).grid(row=row, column=0, sticky="ew", pady=1)

    def _headcount_label(self, classroom: Classroom, session: SessionState) -> str:
        model = next(
            (candidate for candidate in session.classrooms if candidate.name == classroom.name), None
        )
        if model is None or not model.has_size_rule:
            return f"{len(classroom)} élèves"
        low = model.min_size if model.min_size is not None else "–"
        high = model.max_size if model.max_size is not None else "–"
        return f"{len(classroom)} élèves ({low}–{high})"


class ResultsTab(ctk.CTkFrame):
    """Onglet des propositions, piloté par les signaux du contrôleur de génération."""

    def __init__(self, master: tk.Misc, session: SessionState, *, on_regenerate) -> None:
        super().__init__(master, fg_color="transparent")
        self._session = session
        self._proposals: list[ClassroomSet] = []
        self._items: list[ProposalListItem] = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_toolbar(on_regenerate)
        self._build_list()
        self._build_detail()

        self.show_idle()

    # ------------------------------------------------------------------ montage

    def _build_toolbar(self, on_regenerate) -> None:
        toolbar = Panel(self, height=Metrics.MENU_BAND_HEIGHT)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, Metrics.PAD_MD))
        toolbar.grid_propagate(False)
        toolbar.grid_columnconfigure(0, weight=1)

        self._status = ctk.CTkLabel(
            toolbar, text="", font=Fonts.body(), text_color=Palette.TEXT_MUTED, anchor="w"
        )
        self._status.grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=Metrics.PAD_LG)

        self._regenerate = GhostButton(
            toolbar, "Régénérer", on_regenerate, icon=Icons.REFRESH, width=126
        )
        self._regenerate.grid(row=0, column=1, padx=(0, Metrics.PAD_MD))

    def _build_list(self) -> None:
        self._list_panel = Panel(self, width=Metrics.PROPOSAL_LIST_WIDTH, fg_color=Palette.SURFACE_ALT)
        self._list_panel.grid(row=1, column=0, sticky="ns", padx=(0, Metrics.PAD_MD))
        self._list_panel.grid_propagate(False)
        self._list_panel.grid_columnconfigure(0, weight=1)
        self._list_panel.grid_rowconfigure(1, weight=1)

        self._list_header = SectionHeader(self._list_panel, "Propositions")
        self._list_header.grid(row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=Metrics.PAD_MD)

        self._list = ScrollArea(self._list_panel)
        self._list.grid(row=1, column=0, sticky="nsew", padx=Metrics.PAD_SM, pady=(0, Metrics.PAD_SM))

    def _build_detail(self) -> None:
        self._detail_panel = Panel(self)
        self._detail_panel.grid(row=1, column=1, sticky="nsew")
        self._detail_panel.grid_columnconfigure(0, weight=1)
        self._detail_panel.grid_rowconfigure(1, weight=1)

        self._detail_header = SectionHeader(self._detail_panel, "Détail")
        self._detail_header.grid(
            row=0, column=0, sticky="ew", padx=Metrics.PAD_MD, pady=Metrics.PAD_MD
        )

        self._detail = FlowGrid(
            self._detail_panel,
            min_tile_width=248,
            spread=True,
        )
        self._detail.grid(row=1, column=0, sticky="nsew", padx=Metrics.PAD_MD, pady=(0, Metrics.PAD_MD))

        self._placeholder = EmptyState(self._detail_panel, "", "")

    # ------------------------------------------------------------------- états

    def show_idle(self) -> None:
        self._status.configure(text="Aucune génération pour l'instant.")
        self._clear()
        self._show_placeholder(
            "Rien à afficher",
            "Configurez les classes et les élèves dans l'onglet Configuration, "
            "puis cliquez sur « Générer ».",
        )

    def show_running(self) -> None:
        self._status.configure(text="Génération en cours…")
        self._regenerate.configure(state="disabled")
        self._clear()
        self._show_placeholder("Génération en cours…", "Recherche de répartitions compatibles.")

    def show_result(self, result: GenerationResult) -> None:
        self._regenerate.configure(state="normal")

        if result.error is not None:
            self._status.configure(text="La génération a échoué.")
            self._clear()
            self._show_placeholder("Échec de la génération", result.error)
            return

        if result.is_empty:
            self._status.configure(text=f"Aucune solution trouvée en {result.duration:.2f} s.")
            self._clear()
            self._show_placeholder(
                "Aucune répartition possible",
                "Les contraintes sont incompatibles entre elles. Assouplissez les effectifs "
                "ou retirez une contrainte, puis relancez.",
            )
            return

        found = len(result.proposals)
        self._status.configure(
            text=f"{found} proposition{'s' if found > 1 else ''} "
            f"sur {result.requested} demandée{'s' if result.requested > 1 else ''} "
            f"· {result.duration:.2f} s"
        )
        self._clear()
        self._proposals = result.proposals
        self._list_header.set_detail(f"{found} trouvée{'s' if found > 1 else ''}")

        for index, proposal in enumerate(self._proposals):
            item = ProposalListItem(self._list, index, proposal, self.select)
            item.pack(fill="x", pady=(0, Metrics.PAD_SM))
            self._items.append(item)

        self.select(0)

    def select(self, index: int) -> None:
        if not 0 <= index < len(self._proposals):
            return

        for item in self._items:
            item.set_selected(item.index == index)

        self._placeholder.grid_remove()
        self._detail.grid()
        self._detail_header.set_detail(f"Proposition {index + 1}")

        self._clear_detail()
        self._detail.set_tiles(
            [
                ClassroomResultCard(self._detail, classroom, self._session)
                for classroom in self._proposals[index]
            ]
        )

    # ------------------------------------------------------------------ interne

    def _clear(self) -> None:
        self._proposals = []
        self._items = []
        self._list_header.set_detail("")
        for child in self._list.winfo_children():
            child.destroy()
        self._clear_detail()

    def _clear_detail(self) -> None:
        for child in self._detail.winfo_children():
            child.destroy()
        self._detail.set_tiles([])

    def _show_placeholder(self, title: str, detail: str) -> None:
        self._detail.grid_remove()
        self._placeholder.destroy()
        self._placeholder = EmptyState(self._detail_panel, title, detail)
        self._placeholder.grid(row=1, column=0, sticky="nsew", padx=Metrics.PAD_XL, pady=Metrics.PAD_XL)
        self._detail_header.set_detail("")
