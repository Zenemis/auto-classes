import json
from pathlib import Path

import pytest

from auto_classes.cli.__main__ import build_parser, main


def test_build_parser_has_expected_prog_name() -> None:
    parser = build_parser()
    assert parser.prog == "auto-classes"


def test_build_parser_requires_config() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_main_runs_algorithm_from_config_file(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "students": ["Alice", "Bob"],
                "classrooms": [{"name": "A", "tags": []}],
                "constraints": [{"type": "students_together", "student_a": "Alice", "student_b": "Bob"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["auto-classes", "--config", str(config_path)])

    main()

    output = capsys.readouterr().out
    assert "Solution 1" in output
    assert "Alice" in output
    assert "Bob" in output


def test_main_runs_algorithm_for_each_constraint_when_several_are_given(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "students": ["Alice", "Bob"],
                "classrooms": [{"name": "A", "tags": []}],
                "constraints": [
                    {"type": "students_together", "student_a": "Alice", "student_b": "Bob"},
                    {"type": "students_apart", "student_a": "Alice", "student_b": "Bob"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["auto-classes", "--config", str(config_path)])

    main()

    output = capsys.readouterr().out
    assert "Contrainte 1" in output
    assert "Contrainte 2" in output
