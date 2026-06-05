from __future__ import annotations

from pathlib import Path

from agentic_quant.research_os.cli import main


def test_cli_cycle_writes_report_contract_and_state(tmp_path: Path) -> None:
    report = tmp_path / "cycle.md"
    contract = tmp_path / "experiment_run.json"
    state = tmp_path / "state.json"

    exit_code = main(
        [
            "cycle",
            "--idea",
            "HMM regime features improve pair spread entries",
            "--output",
            str(report),
            "--contract-output",
            str(contract),
            "--state-output",
            str(state),
        ]
    )

    assert exit_code == 0
    assert "QuantSigma Lab Agent Research Cycle" in report.read_text(encoding="utf-8")
    assert '"schema_version": "experiment_run.v1"' in contract.read_text(encoding="utf-8")
    assert '"contract_validated": true' in state.read_text(encoding="utf-8")


def test_cli_review_reads_contract_and_writes_review(tmp_path: Path) -> None:
    report = tmp_path / "cycle.md"
    contract = tmp_path / "experiment_run.json"
    state = tmp_path / "state.json"
    review = tmp_path / "review.md"
    main(
        [
            "cycle",
            "--idea",
            "HMM regime features improve pair spread entries",
            "--output",
            str(report),
            "--contract-output",
            str(contract),
            "--state-output",
            str(state),
        ]
    )

    exit_code = main(["review", "--input", str(contract), "--output", str(review)])

    assert exit_code == 0
    markdown = review.read_text(encoding="utf-8")
    assert "Trading Experiment Audit Report" in markdown
    assert "experiment_run.v1 contract completeness" in markdown
