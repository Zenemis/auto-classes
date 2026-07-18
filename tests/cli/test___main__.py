from auto_classes.cli.__main__ import build_parser


def test_build_parser_has_expected_prog_name() -> None:
    parser = build_parser()
    assert parser.prog == "auto-classes"
