"""Lancement de l'UI : `python -m auto_classes.ui` (ou `--demo` pour un jeu d'essai).

Le jeu d'essai s'obtient aussi en tenant les deux touches Ctrl au démarrage, seul moyen
de l'atteindre depuis l'exécutable, qu'on lance d'un double-clic.
"""

import argparse

from auto_classes.ui.app import run
from auto_classes.ui.debug_mode import both_control_keys_held
from auto_classes.ui.demo import build_demo_session
from auto_classes.ui.session import SessionState


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-classes-ui", description="Interface d'auto-classes")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="démarrer avec un jeu d'essai (classes, élèves et contraintes) pour explorer l'UI ;"
        " équivaut à tenir les deux touches Ctrl au lancement",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    demo = args.demo or both_control_keys_held()
    session: SessionState = build_demo_session() if demo else SessionState()
    run(session)


if __name__ == "__main__":
    main()
