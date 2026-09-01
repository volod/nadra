import logging

from nadra.cli import build_parser, main


def test_parser_selects_the_info_command() -> None:
    parser = build_parser()

    assert parser.prog == "nadra"
    assert parser.parse_args(["info"]).command == "info"


def test_info_command_logs_the_project_identity(caplog) -> None:  # type: ignore[no-untyped-def]
    caplog.set_level(logging.INFO)

    assert main(["info"]) == 0
    assert "nadra" in caplog.text
