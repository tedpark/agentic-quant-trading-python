from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from re import sub


@dataclass(frozen=True)
class ExperimentPlan:
    run_id: str
    hypothesis: str
    feature_candidates: tuple[str, ...]
    validation_protocol: tuple[str, ...]
    risk_checks: tuple[str, ...]
    failure_cases: tuple[str, ...]

    def to_markdown(self) -> str:
        lines = [
            "# Hypothesis-to-Experiment Plan",
            "",
            f"- run id: `{self.run_id}`",
            f"- hypothesis: {self.hypothesis}",
            "",
            "## Feature Candidates",
            "",
        ]
        lines.extend(f"- {item}" for item in self.feature_candidates)
        lines.extend(["", "## Validation Protocol", ""])
        lines.extend(f"- {item}" for item in self.validation_protocol)
        lines.extend(["", "## Risk Checks", ""])
        lines.extend(f"- {item}" for item in self.risk_checks)
        lines.extend(["", "## Expected Failure Cases", ""])
        lines.extend(f"- {item}" for item in self.failure_cases)
        return "\n".join(lines) + "\n"


def plan_experiment(idea: str) -> ExperimentPlan:
    normalized = idea.strip()
    if not normalized:
        raise ValueError("idea must not be empty")

    return ExperimentPlan(
        run_id=sha256(normalized.lower().encode("utf-8")).hexdigest()[:12],
        hypothesis=_hypothesis(normalized),
        feature_candidates=_feature_candidates(normalized),
        validation_protocol=(
            "Use walk-forward train / validation / test windows.",
            "Fit scalers, regime models, and feature transforms on training windows only.",
            "Use purging and embargo when labels overlap adjacent windows.",
            "Select thresholds on validation windows and report untouched test-window metrics.",
        ),
        risk_checks=(
            "Report CVaR / Expected Shortfall, not only average return.",
            "Compare drawdown and turnover under transaction-cost assumptions.",
            "Break out performance by detected regime.",
        ),
        failure_cases=(
            "Signal disappears after transaction costs.",
            "Feature importance is unstable across folds.",
            "Performance concentrates in one regime and fails during regime shift.",
            "Validation improves while untouched test metrics degrade.",
        ),
    )


def _hypothesis(idea: str) -> str:
    clean = sub(r"\s+", " ", idea)
    return f"If {clean}, then it should improve out-of-sample risk-adjusted performance under leakage-aware validation."


def _feature_candidates(idea: str) -> tuple[str, ...]:
    text = idea.lower()
    features = [
        "rolling return / volatility features",
        "z-score velocity and acceleration",
        "spread mean-reversion strength",
    ]
    if "hmm" in text or "regime" in text:
        features.extend(["HMM-style regime label", "regime transition probability", "regime-specific volatility"])
    if "pair" in text or "spread" in text or "cointegration" in text:
        features.extend(["cointegration residual", "spread half-life", "rolling correlation stability"])
    if "rl" in text or "qrdqn" in text or "qr-dqn" in text:
        features.extend(["return quantile features", "CVaR-aware action score", "policy entropy proxy"])
    return tuple(dict.fromkeys(features))
