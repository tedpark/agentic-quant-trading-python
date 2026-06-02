from agentic_quant.validation.demo_walk_forward import render_markdown
from agentic_quant.validation.walk_forward import (
    aggregate_results,
    fit_standardizer,
    make_walk_forward_splits,
    run_walk_forward_validation,
    synthetic_regime_observations,
)


def test_walk_forward_splits_are_time_ordered() -> None:
    splits = make_walk_forward_splits(192, train_size=72, validation_size=24, test_size=24, step_size=24)

    assert len(splits) == 4
    for split in splits:
        assert split.train_end <= split.validation_start
        assert split.validation_end <= split.test_start
        assert split.test_end <= 192


def test_standardizer_uses_training_window_only() -> None:
    observations = synthetic_regime_observations(180)
    split = make_walk_forward_splits(180, train_size=72, validation_size=24, test_size=24)[0]
    train_standardizer = fit_standardizer(observations[split.train_start : split.train_end])
    leaked_standardizer = fit_standardizer(observations[split.train_start : split.test_end])

    assert train_standardizer.mean != leaked_standardizer.mean


def test_run_walk_forward_validation_reports_test_metrics() -> None:
    results = run_walk_forward_validation(
        synthetic_regime_observations(192),
        train_size=72,
        validation_size=24,
        test_size=24,
        step_size=24,
        thresholds=(0.0, 0.25, 0.5, 0.75, 1.0),
        transaction_cost=0.0004,
    )
    aggregate = aggregate_results(results)

    assert len(results) == 4
    assert aggregate.observations == 96
    assert all(result.validation_range[1] < result.test_range[0] for result in results)
    assert all(result.selected_threshold in {0.0, 0.25, 0.5, 0.75, 1.0} for result in results)


def test_walk_forward_markdown_declares_boundary() -> None:
    markdown = render_markdown()

    assert "# Walk-Forward Validation Sample" in markdown
    assert "training window only" in markdown
    assert "not investment advice" in markdown
    assert "private universes" in markdown
