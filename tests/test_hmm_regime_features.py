from agentic_quant.features.demo_regime_features import render_markdown
from agentic_quant.features.regime import (
    build_feature_rows,
    classify_regimes,
    fit_regime_model,
    fit_standardizer,
    run_regime_feature_pipeline,
    synthetic_market_bars,
)


def test_rolling_features_do_not_depend_on_future_prices() -> None:
    original = list(synthetic_market_bars(120))
    changed_future = original.copy()
    changed_future[-1] = type(original[-1])(timestamp=original[-1].timestamp, close=original[-1].close * 10)

    original_rows = build_feature_rows(original)
    changed_rows = build_feature_rows(changed_future)

    assert original_rows[20] == changed_rows[20]
    assert original_rows[-1] != changed_rows[-1]


def test_standardizer_uses_training_rows_only() -> None:
    rows = build_feature_rows(synthetic_market_bars(160))
    train = rows[:80]
    leaked = rows[:120]

    train_standardizer = fit_standardizer(train)
    leaked_standardizer = fit_standardizer(leaked)

    assert train_standardizer.means["realized_volatility"] != leaked_standardizer.means["realized_volatility"]


def test_regime_model_classifies_low_and_high_volatility_states() -> None:
    rows = build_feature_rows(synthetic_market_bars(180))
    model = fit_regime_model(rows[:100])
    classified = classify_regimes(rows[100:130], model)

    assert {state.name for state in model.states} == {"low_vol", "high_vol"}
    assert len(classified) == 30
    assert all(row.regime in {"low_vol", "high_vol"} for row in classified)


def test_regime_feature_pipeline_reports_fold_outputs() -> None:
    results = run_regime_feature_pipeline(
        synthetic_market_bars(220),
        train_size=80,
        validation_size=20,
        test_size=20,
        step_size=20,
    )

    assert len(results) >= 5
    assert all(result.train_range[1] < result.test_range[0] for result in results)
    assert all(result.sample_test_rows for result in results)


def test_regime_feature_markdown_declares_boundary() -> None:
    markdown = render_markdown()

    assert "# HMM-Style Regime Feature Pipeline Sample" in markdown
    assert "training window only" in markdown
    assert "not investment advice" in markdown
    assert "private universes" in markdown
