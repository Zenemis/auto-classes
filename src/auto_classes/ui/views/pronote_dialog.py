"""Fenêtre de connexion à Pronote, puis import des élèves de l'établissement.

Trois chemins, du plus commode au plus laborieux :

- **Compte enregistré** — un jeton obtenu par QR code lors d'un import précédent. Rien à
  saisir. C'est le mode présélectionné dès qu'un compte existe.
- **QR code** — l'enregistrement initial : on colle le contenu du QR code affiché par
  PRONOTE et le code à quatre chiffres. Ce chemin ignore l'ENT, puisque le QR code porte
  déjà l'adresse et un jeton d'accès.
- **Identifiants** — la connexion classique, avec l'ENT s'il en faut un.

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

from auto_classes.pronote import (
    ENT_NONE,
    Connection,
    PronoteError,
    Roster,
    SavedCredentials,
    available_ents,
    connect_with_qr_code,
    connect_with_token,
    fetch_roster,
    forget_credentials,
    load_credentials,
    save_credentials,
)
from auto_classes.ui.components import GhostButton, ModalDialog, PrimaryButton
from auto_classes.ui.theme import Fonts, Metrics, Palette

DIALOG_WIDTH = 480
POLL_INTERVAL_MS = 60

MODE_SAVED = "Compte enregistré"
MODE_QR = "QR code"
MODE_PASSWORD = "Identifiants"

WRAP = DIALOG_WIDTH - 2 * Metrics.PAD_XL

VIE_SCOLAIRE_NOTICE = (
    "L'import lit les classes de l'espace Vie scolaire, le seul que Pronote ouvre aux "
    "outils externes avec les listes d'élèves. Un compte Professeurs ne convient pas."
)

QR_NOTICE = (
    "Dans Pronote, affichez le QR code de connexion et choisissez un code à quatre "
    "chiffres. Lisez le QR code avec votre téléphone, puis collez ci-dessous le texte "
    "obtenu. Le compte restera enregistré : les imports suivants ne demanderont plus rien."
)

SAVED_NOTICE = (
    "Ce compte a été enregistré lors d'un import précédent. Pronote renouvelle son jeton "
    "à chaque connexion ; il n'y a rien à ressaisir."
)


class PronoteDialog(ModalDialog):
    """Connexion à Pronote. `show()` renvoie un `Roster`, ou None si l'on renonce."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        fetcher: Callable[..., Roster] = fetch_roster,
        qr_connector: Callable[..., Connection] = connect_with_qr_code,
        token_connector: Callable[..., Connection] = connect_with_token,
        credentials: SavedCredentials | None = None,
        on_credentials_changed: Callable[[SavedCredentials | None], None] | None = None,
        ents: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        super().__init__(master, "Importer depuis Pronote", width=DIALOG_WIDTH)

        self._fetcher = fetcher
        self._qr_connector = qr_connector
        self._token_connector = token_connector
        self._credentials = credentials if credentials is not None else load_credentials()
        self._on_credentials_changed = on_credentials_changed or _store_credentials
        self._ents = available_ents() if ents is None else ents
        self._thread: threading.Thread | None = None
        self._results: queue.Queue[tuple[Roster | None, str | None]] = queue.Queue()

        self._note(VIE_SCOLAIRE_NOTICE).pack(anchor="w", pady=(0, Metrics.PAD_MD))

        self._modes = [MODE_QR, MODE_PASSWORD]
        if self._credentials is not None:
            self._modes.insert(0, MODE_SAVED)

        self._mode = ctk.CTkSegmentedButton(
            self.content,
            values=self._modes,
            command=self._on_mode_changed,
            height=Metrics.CONTROL_HEIGHT,
            corner_radius=Metrics.RADIUS_SM,
            fg_color=Palette.SURFACE_ALT,
            selected_color=Palette.PRIMARY,
            selected_hover_color=Palette.PRIMARY_HOVER,
            unselected_color=Palette.SURFACE_ALT,
            unselected_hover_color=Palette.HOVER,
            text_color=Palette.TEXT,
            font=Fonts.body(),
        )
        self._mode.pack(fill="x")

        self._panels = {
            MODE_SAVED: self._build_saved_panel(),
            MODE_QR: self._build_qr_panel(),
            MODE_PASSWORD: self._build_password_panel(),
        }

        self._cancel_button = GhostButton(self.footer, "Annuler", self.cancel, width=96)
        self._cancel_button.pack(side="right")
        self._connect_button = PrimaryButton(self.footer, "Se connecter", self._submit, width=136)
        self._connect_button.pack(side="right", padx=(0, Metrics.PAD_SM))

        self._mode.set(self._modes[0])
        self._on_mode_changed(self._modes[0])

    # ------------------------------------------------------------------- montage

    def _note(self, text: str, *, master: tk.Misc | None = None) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            master if master is not None else self.content,
            text=text,
            font=Fonts.small(),
            text_color=Palette.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=WRAP,
        )

    def _label(self, master: tk.Misc, text: str) -> None:
        ctk.CTkLabel(master, text=text, font=Fonts.body_bold(), text_color=Palette.TEXT).pack(
            anchor="w", pady=(Metrics.PAD_MD, 0)
        )

    def _entry(self, master: tk.Misc, *, placeholder: str = "", show: str = "") -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            master,
            placeholder_text=placeholder,
            show=show,
            font=Fonts.body(),
            height=Metrics.CONTROL_HEIGHT,
            fg_color=Palette.SURFACE,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT,
        )
        entry.pack(fill="x", pady=(Metrics.PAD_SM, 0))
        entry.bind("<Return>", lambda _event: self._submit())
        return entry

    def _build_saved_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self.content, fg_color="transparent")
        if self._credentials is None:
            return panel

        self._label(panel, f"{self._credentials.username} — {self._credentials.server}")
        self._note(SAVED_NOTICE, master=panel).pack(anchor="w", pady=(Metrics.PAD_SM, 0))
        GhostButton(panel, "Oublier ce compte", self._forget, width=168).pack(
            anchor="w", pady=(Metrics.PAD_MD, 0)
        )
        return panel

    def _build_qr_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self.content, fg_color="transparent")

        self._note(QR_NOTICE, master=panel).pack(anchor="w", pady=(Metrics.PAD_MD, 0))

        self._label(panel, "Contenu du QR code")
        self._qr_payload = ctk.CTkTextbox(
            panel,
            height=76,
            font=Fonts.body(),
            fg_color=Palette.SURFACE,
            border_color=Palette.BORDER,
            border_width=1,
            text_color=Palette.TEXT,
            wrap="char",
        )
        self._qr_payload.pack(fill="x", pady=(Metrics.PAD_SM, 0))

        self._label(panel, "Code à quatre chiffres")
        self._qr_pin = self._entry(panel, placeholder="1234")
        return panel

    def _build_password_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self.content, fg_color="transparent")

        self._label(panel, "Adresse Pronote de l'établissement")
        self._url = self._entry(panel, placeholder="https://0123456a.index-education.net/pronote/")
        self._label(panel, "Identifiant")
        self._username = self._entry(panel)
        self._label(panel, "Mot de passe")
        self._password = self._entry(panel, show="•")

        self._label(panel, "ENT")
        self._ent = ctk.CTkOptionMenu(
            panel,
            values=[ENT_NONE, *self._ents],
            width=WRAP,
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
        return panel

    # ------------------------------------------------------------------- modes

    def _on_mode_changed(self, mode: str) -> None:
        self.clear_error()
        for name, panel in self._panels.items():
            if name == mode:
                panel.pack(fill="x", expand=True)
            else:
                panel.pack_forget()

    def _forget(self) -> None:
        """Efface le compte enregistré et bascule sur l'enregistrement par QR code."""
        self._credentials = None
        self._on_credentials_changed(None)

        self._panels[MODE_SAVED].destroy()
        self._panels[MODE_SAVED] = ctk.CTkFrame(self.content, fg_color="transparent")
        self._modes = [MODE_QR, MODE_PASSWORD]
        self._mode.configure(values=self._modes)
        self._mode.set(MODE_QR)
        self._on_mode_changed(MODE_QR)

    # ------------------------------------------------------------------ connexion

    def _submit(self) -> None:
        if self._thread is not None:
            return

        self.clear_error()
        # Les valeurs sont lues ici, sur le thread UI : le thread de travail ne doit
        # toucher à aucun widget, pas même pour lire un champ.
        try:
            work = self._prepare()
        except PronoteError as error:
            self.show_error(str(error))
            return

        self._set_connecting(True)
        self._thread = threading.Thread(
            target=self._work, args=(work,), name="auto-classes-pronote", daemon=True
        )
        self._thread.start()
        self.after(POLL_INTERVAL_MS, self._poll)

    def _prepare(self) -> Callable[[], Roster]:
        """Ferme sur les valeurs saisies et rend le travail à exécuter hors du thread UI."""
        mode = self._mode.get()

        if mode == MODE_SAVED:
            credentials = self._credentials
            if credentials is None:  # pragma: no cover - le mode n'existe pas sans compte
                raise PronoteError("Aucun compte enregistré.")
            return lambda: self._connect(self._token_connector, credentials)

        if mode == MODE_QR:
            payload = self._qr_payload.get("1.0", "end")
            pin = self._qr_pin.get()
            return lambda: self._connect(self._qr_connector, payload, pin)

        url = self._url.get()
        username = self._username.get()
        password = self._password.get()
        ent = self._ents.get(self._ent.get())
        return lambda: self._fetcher(url, username, password, ent)

    def _connect(self, connector: Callable[..., Connection], *args: Any) -> Roster:
        """Connexion par jeton : le jeton renouvelé est réécrit avant de rendre la liste.

        PRONOTE invalide l'ancien jeton dès celui-ci délivré ; ne pas l'enregistrer
        rendrait le compte inutilisable au lancement suivant.
        """
        connection = connector(*args)
        # Appelé depuis le thread de connexion, ce qui est sans danger : l'écriture ne
        # touche que le disque. C'est aussi le plus tôt possible, donc le plus sûr.
        self._on_credentials_changed(connection.credentials)
        return connection.roster

    def _work(self, work: Callable[[], Roster]) -> None:
        """Exécuté dans le thread de connexion : ne touche ni widget ni signal."""
        try:
            roster = work()
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


def _store_credentials(credentials: SavedCredentials | None) -> None:
    """Écriture par défaut : le disque. Les tests injectent autre chose."""
    if credentials is None:
        forget_credentials()
    else:
        save_credentials(credentials)
