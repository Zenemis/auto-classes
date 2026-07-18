import argparse

from auto_classes import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-classes", description="CLI de debug pour auto-classes")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main() -> None:
    parser = build_parser()
    parser.parse_args()


if __name__ == "__main__":
    main()
