from agentic_quant.experiments.demo_mini_backtest import render_markdown
from agentic_quant.experiments.orchestration import run_mini_experiment, simulate_rows
from agentic_quant.features.regime import synthetic_market_bars


def test_mini_experiment_runs_time_ordered_folds() -> None:
    results = run_mini_experiment(
        synthetic_market_bars(240),
        train_size=90,
        validation_size=24,
        test_size=24,
        step_size=24,
        thresholds=(0.0, 0.4, 0.8, 1.2),
    )

    assert len(results) >= 4
    assert all(row.train_range[1] < row.validation_range[0] < row.test_range[0] for row in results)
    assert all(row.selected_threshold in {0.0, 0.4, 0.8, 1.2} for row in results)


def test_test_rows_receive_forward_returns_without_empty_activity() -> None:
    result = run_mini_experiment(
        synthetic_market_bars(180),
        train_size=70,
        validation_size=20,
        test_size=20,
        thresholds=(0.0, 0.5, 1.0),
    )[0]

    assert result.sample_test_rows
    assert result.test_metrics.observations == 20
    assert result.test_metrics.turnover >= 0
    assert result.test_metrics.cvar <= max(row.forward_return for row in result.sample_test_rows)


def test_threshold_changes_simulated_turnover() -> None:
    result = run_mini_experiment(
        synthetic_market_bars(180),
        train_size=70,
        validation_size=20,
        test_size=20,
        thresholds=(0.0, 0.5, 1.0),
    )[0]

    low_threshold = simulate_rows(result.sample_test_rows, threshold=0.0)
    high_threshold = simulate_rows(result.sample_test_rows, threshold=10.0)

    assert low_threshold.turnover >= high_threshold.turnover


def test_mini_experiment_is_deterministic() -> None:
    kwargs = dict(train_size=80, validation_size=20, test_size=20, thresholds=(0.0, 0.4, 0.8))

    first = run_mini_experiment(synthetic_market_bars(220), **kwargs)
    second = run_mini_experiment(synthetic_market_bars(220), **kwargs)

    assert first == second


def test_mini_backtest_markdown_declares_public_boundary() -> None:
    markdown = render_markdown()

    assert "# Mini Backtest Orchestration Sample" in markdown
    assert "training window only" in markdown
    assert "not investment advice" in markdown
    assert "live execution" in markdown
