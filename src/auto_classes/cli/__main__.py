import argparse
from pathlib import Path

from auto_classes import __version__
from auto_classes.algorithm.generate_classes import generate_classes
from auto_classes.core import ClassroomSet
from auto_classes.serialization import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-classes", description="CLI de debug pour auto-classes")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--config", required=True, type=Path, help="Chemin vers un fichier de configuration JSON")
    return parser


def _format_classroom_set(classroom_set: ClassroomSet) -> str:
    lines = []
    for index, classroom in enumerate(classroom_set):
        tags = ", ".join(sorted(classroom.tags)) or "-"
        names = ", ".join(sorted(student.name for student in classroom.students)) or "(vide)"
        lines.append(f"Classe {index} [tags: {tags}] : {names}")
    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(args.config)

    for constraint_index, constraint in enumerate(config.constraints):
        if len(config.constraints) > 1:
            print(f"=== Contrainte {constraint_index + 1} ===")

        solutions = generate_classes(config.students, config.classroom_tags, constraint, config.num_solutions)

        if not solutions:
            print("Aucune solution trouvée")
            continue

        for index, solution in enumerate(solutions):
            print(f"--- Solution {index + 1} ---")
            print(_format_classroom_set(solution))
            print()


if __name__ == "__main__":
    main()
