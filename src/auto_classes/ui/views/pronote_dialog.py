"""Fenêtre de connexion à Pronote, puis import des élèves de l'établissement.

La connexion part sur un thread : un serveur Pronote lointain met facilement plusieurs
secondes à répondre, et la fenêtre doit rester dessinée pendant ce temps. Le résultat
traverse une `Queue` relevée par `after`, comme pour la génération — toucher à Tk depuis
le thread de travail lèverait « main thread is not in main loop ».
"""

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from auto_classes.pronote import ENT_NONE, PronoteError, Roster, available_ents, fetch_roster
from auto_classes.ui.components import GhostButton, ModalDialog, PrimaryButton
from auto_classes.ui.theme import Fonts, Metrics, Palette

DIALOG_WIDTH = 460
POLL_INTERVAL_MS = 60

INTRO = (
    "L'import lit les classes de l'espace Vie scolaire, le seul que Pronote ouvre aux "
    "outils externes avec les listes d'élèves. Un compte Professeurs ne convient pas."
)


class PronoteDialog(ModalDialog):
    """Identifiants Pronote, puis récupération des classes. `show()` renvoie un `Roster`."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        fetcher: Callable[..., Roster] = fetch_roster,
        ents: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        super().__init__(master, "Importer depuis Pronote", width=DIALOG_WIDTH)

        self._fetcher = fetcher
        self._ents = available_ents() if ents is None else ents
        self._thread: threading.Thread | None = None
        self._results: queue.Queue[tuple[Roster | None, str | None]] = queue.Queue()

        ctk.CTkLabel(
            self.content,
            text=INTRO,
            font=Fonts.small(),
            text_color=Palette.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=DIALOG_WIDTH - 2 * Metrics.PAD_XL,
        ).pack(anchor="w", pady=(0, Metrics.PAD_MD))

        self._url = self._field(
            "Adresse Pronote de l'établissement",
            placeholder="https://0123456a.index-education.net/pronote/",
        )
        self._username = self._field("Identifiant")
        self._password = self._field("Mot de passe", show="•")

        ctk.CTkLabel(
            self.content, text="ENT", font=Fonts.body_bold(), text_color=Palette.TEXT
        ).pack(anchor="w", pady=(Metrics.PAD_MD, 0))
        self._ent = ctk.CTkOptionMenu(
            self.content,
            values=[ENT_NONE, *self._ents],
            width=DIALOG_WIDTH - 2 * Metrics.PAD_XL,
            height=Metrics.CONTROL_HEIGHT,
            corner_radius=Metrics.RADIUS_SM,
            fg_color=Palette.SURFACE_ALT,
            button_color=Palette.SURFACE_ALT,
            button_hover_color=Palette.HOVER,
            text_color=Palette.TEXT,
            dropdown_fg_color=Palette.SURFACE,
            dropdown_hover_color=Palette.HOVER,
            dropdown_text_color=Palette.TEXT,
            font=Fonts.body(),
            dropdown_font=Fonts.body(),
            anchor="w",
        )
        self._ent.set(ENT_NONE)
        self._ent.pack(fill="x", pady=(Metrics.PAD_SM, 0))

        self._cancel_button = GhostButton(self.footer, "Annuler", self.cancel, width=96)
        self._cancel_button.pack(side="right")
        self._connect_button = PrimaryButton(self.footer, "Se connecter", self._submit, width=136)
        self._connect_button.pack(side="right", padx=(0, Metrics.PAD_SM))

        for entry in (self._url, self._username, self._password):
            entry.bind("<Return>", lambda _event: self._submit())
        self._url.after(120, self._url.focus_set)

    # ------------------------------------------------------------------- montage

    def _field(self, label: str, *, placeholder: str = "", show: str = "") -> ctk.CTkEntry:
        ctk.CTkLabel(
            self.content, text=label, font=Fonts.body_bold(), text_color=Palette.TEXT
        ).pack(anchor="w", pady=(Metrics.PAD_MD, 0))
        entry = ctk.CTkEntry(
            self.content,
            placeholder_text=placeholder,
            show=show,
            font=Fonts.body(),
            height=Metrics.CONTROL_HEIGHT,
            fg_color=Palette.SURFACE,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT,
        )
        entry.pack(fill="x", pady=(Metrics.PAD_SM, 0))
        return entry

    # ------------------------------------------------------------------ connexion

    def _submit(self) -> None:
        if self._thread is not None:
            return

        self.clear_error()
        self._set_connecting(True)

        # Les valeurs sont lues ici, sur le thread UI : le thread de travail ne doit
        # toucher à aucun widget, pas même pour lire un champ.
        url = self._url.get()
        username = self._username.get()
        password = self._password.get()
        ent = self._ents.get(self._ent.get())

        self._thread = threading.Thread(
            target=self._work,
            args=(url, username, password, ent),
            name="auto-classes-pronote",
            daemon=True,
        )
        self._thread.start()
        self.after(POLL_INTERVAL_MS, self._poll)

    def _work(self, url: str, username: str, password: str, ent: Any) -> None:
        """Exécuté dans le thread de connexion : ne touche ni widget ni signal."""
        try:
            roster = self._fetcher(url, username, password, ent)
        except PronoteError as error:
            self._results.put((None, str(error)))
        except Exception as error:  # remonté tel quel plutôt qu'avalé
            self._results.put((None, f"{type(error).__name__} : {error}"))
        else:
            self._results.put((roster, None))

    def _poll(self) -> None:
        thread = self._thread
        if thread is None or not self.winfo_exists():
            return  # fenêtre refermée pendant la connexion : plus rien à afficher

        try:
            roster, error = self._results.get_nowait()
        except queue.Empty:
            if thread.is_alive():
                self.after(POLL_INTERVAL_MS, self._poll)
                return
            roster, error = None, "La connexion s'est interrompue sans résultat."

        self._thread = None
        self._set_connecting(False)
        if error is not None:
            self.show_error(error)
            return
        self.accept(roster)

    def _set_connecting(self, connecting: bool) -> None:
        self._connect_button.configure(
            text="Connexion…" if connecting else "Se connecter",
            state="disabled" if connecting else "normal",
        )
