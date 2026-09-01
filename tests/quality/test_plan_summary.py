from pathlib import Path

from nadra.quality.plan_summary import main, summary_lines
from tests.quality._plan_fixture import (
    SHIPPED_SPEC,
    plan_with,
    task_block,
    write_project,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_empty_plan_reports_no_next_tasks(tmp_path: Path) -> None:
    root = write_project(tmp_path, spec=SHIPPED_SPEC, plan=plan_with())

    lines = summary_lines(root)

    assert lines == [
        "tasks: 0",
        "agent lane: 0",
        "human lane: 0",
        "next agent: none",
        "next human: none",
    ]


def test_repository_plan_is_valid_and_lane_counts_agree() -> None:
    lines = summary_lines(PROJECT_ROOT)

    assert lines[0].startswith("tasks: ")
    counts = {label: int(value) for label, value in (line.split(": ", 1) for line in lines[:3])}
    assert counts["agent lane"] + counts["human lane"] == counts["tasks"]


def test_summary_counts_statuses_and_selects_required_work(tmp_path: Path) -> None:
    optional = task_block(identifier="optional-first", optional=True)
    required = task_block(identifier="required-next")
    plan = plan_with(required, optional)
    root = write_project(tmp_path, plan=plan)

    lines = summary_lines(root)

    assert "tasks: 2" in lines
    assert "statuses: CLEAR=2" in lines
    assert "next agent: required-next [feature]" in lines


def test_invalid_plan_summary_refuses_to_schedule(tmp_path: Path) -> None:
    root = write_project(tmp_path, plan=plan_with())

    assert summary_lines(root) == ["plan is invalid; run make lint-spec-plan"]
    assert main(["--root", str(root)]) == 1
