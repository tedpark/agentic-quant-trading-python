from agentic_quant.risk.cvar import evaluate_action_risk, left_tail_cvar, risk_multiplier
from agentic_quant.risk.demo_cvar import render_markdown, toy_qrdqn_quantiles


def test_left_tail_cvar_uses_lowest_quantiles() -> None:
    cvar = left_tail_cvar([-0.04, -0.02, 0.01, 0.03], tail_fraction=0.5)

    assert cvar == -0.03


def test_risk_multiplier_thresholds() -> None:
    assert risk_multiplier(-0.04) == 0.0
    assert risk_multiplier(-0.02) == 0.5
    assert risk_multiplier(-0.01) == 1.0


def test_evaluate_action_risk_orders_safer_actions_first() -> None:
    rows = evaluate_action_risk(toy_qrdqn_quantiles(), tail_fraction=0.2)

    assert rows[0].action == "hold"
    assert rows[0].multiplier == 1.0
    assert any(row.action == "long_spread" and row.multiplier == 0.0 for row in rows)


def test_cvar_markdown_declares_boundary() -> None:
    markdown = render_markdown()

    assert "# QR-DQN / CVaR Smoke Example" in markdown
    assert "synthetic quantiles only" in markdown
    assert "not investment advice" in markdown
