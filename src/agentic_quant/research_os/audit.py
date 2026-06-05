from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from agentic_quant.experiments.manifest import ExperimentManifest
from agentic_quant.experiments.orchestration import ExperimentFoldResult
from agentic_quant.research_os.contract import ExperimentRunContract, validate_experiment_run_contract


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    category: str
    message: str
    recommendation: str


@dataclass(frozen=True)
class ExperimentAuditReport:
    run_id: str
    decision: str
    findings: tuple[AuditFinding, ...]
    checked_items: tuple[str, ...]

    def severity_counts(self) -> Mapping[str, int]:
        counts = {"pass": 0, "warning": 0, "fail": 0}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts

    def to_markdown(self) -> str:
        counts = self.severity_counts()
        lines = [
            "# Trading Experiment Audit Report",
            "",
            f"- run id: `{self.run_id}`",
            f"- decision: `{self.decision}`",
            f"- pass: {counts.get('pass', 0)}",
            f"- warning: {counts.get('warning', 0)}",
            f"- fail: {counts.get('fail', 0)}",
            "",
            "## Checked Items",
            "",
        ]
        lines.extend(f"- {item}" for item in self.checked_items)
        lines.extend(["", "## Findings", "", "| Severity | Category | Finding | Recommendation |", "|---|---|---|---|"])
        for finding in self.findings:
            lines.append(
                f"| `{finding.severity}` | `{finding.category}` | {finding.message} | {finding.recommendation} |"
            )
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class PromotionPolicy:
    min_folds: int = 3
    min_test_observations: int = 60
    max_turnover: float = 0.8
    min_test_sharpe: float = 0.0
    max_validation_test_gap: float = 0.003
    required_artifacts: tuple[str, ...] = ("manifest_report", "backtest_report")


def audit_experiment(
    manifest: ExperimentManifest,
    folds: Sequence[ExperimentFoldResult],
    *,
    policy: PromotionPolicy = PromotionPolicy(),
) -> ExperimentAuditReport:
    if not folds:
        raise ValueError("folds must not be empty")

    findings = [
        *_audit_manifest(manifest, policy=policy),
        *_audit_time_ordering(folds),
        *_audit_validation_behavior(folds, policy=policy),
        *_audit_risk_metrics(manifest, folds, policy=policy),
        *_audit_operational_boundary(manifest),
    ]
    decision = _decision(findings)
    return ExperimentAuditReport(
        run_id=manifest.run_id,
        decision=decision,
        findings=tuple(findings),
        checked_items=(
            "manifest completeness",
            "time-ordered fold structure",
            "validation/test separation",
            "feature fit scope",
            "cost stress",
            "regime breakdown",
            "benchmark comparison",
            "risk metrics and tail behavior",
            "public/private operational boundary",
        ),
    )


def audit_experiment_run_contract(
    contract: ExperimentRunContract,
    *,
    policy: PromotionPolicy = PromotionPolicy(),
) -> ExperimentAuditReport:
    validated = validate_experiment_run_contract(contract)
    findings = [
        *_audit_contract_completeness(validated, policy=policy),
        *_audit_contract_time_ordering(validated),
        *_audit_contract_validation_behavior(validated, policy=policy),
        *_audit_contract_risk_metrics(validated, policy=policy),
        *_audit_contract_boundary(validated),
    ]
    return ExperimentAuditReport(
        run_id=validated.run_id,
        decision=_decision(findings),
        findings=tuple(findings),
        checked_items=(
            "experiment_run.v1 contract completeness",
            "time-ordered fold structure",
            "validation/test separation",
            "risk metrics and tail behavior",
            "public/private operational boundary",
        ),
    )


def _audit_manifest(manifest: ExperimentManifest, *, policy: PromotionPolicy) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    if manifest.fold_count < policy.min_folds:
        findings.append(
            _fail(
                "manifest",
                f"Manifest has {manifest.fold_count} folds, below policy minimum {policy.min_folds}.",
                "Run enough walk-forward folds before promotion.",
            )
        )
    else:
        findings.append(_pass("manifest", "Manifest satisfies minimum fold count.", "Keep fold count in every run log."))

    if manifest.test_observations < policy.min_test_observations:
        findings.append(
            _fail(
                "manifest",
                f"Manifest has {manifest.test_observations} test observations, below policy minimum {policy.min_test_observations}.",
                "Increase test-window coverage before promotion.",
            )
        )
    else:
        findings.append(_pass("manifest", "Manifest satisfies minimum test observations.", "Keep sample count visible."))

    missing_artifacts = [name for name in policy.required_artifacts if name not in manifest.artifacts]
    if missing_artifacts:
        findings.append(
            _warn(
                "manifest",
                f"Manifest is missing expected artifacts: {', '.join(missing_artifacts)}.",
                "Attach the generated backtest, manifest, and audit reports before publishing.",
            )
        )
    else:
        findings.append(_pass("manifest", "Manifest includes expected report artifacts.", "Keep artifact paths stable."))

    protocol = " ".join(manifest.validation_protocol).lower()
    if "training" in protocol and "validation" in protocol and "test" in protocol:
        findings.append(_pass("validation", "Manifest declares train/validation/test separation.", "Keep this explicit."))
    else:
        findings.append(
            _fail(
                "validation",
                "Manifest does not clearly declare train/validation/test separation.",
                "Declare how thresholds and features are selected before test metrics are reported.",
            )
        )

    if "training window only" in protocol or "train" in protocol and "only" in protocol:
        findings.append(_pass("leakage", "Manifest declares train-only fitting.", "Keep transform fitting scoped to train windows."))
    else:
        findings.append(
            _warn(
                "leakage",
                "Manifest does not clearly state that transforms are fit on training data only.",
                "Add train-only fitting language for scalers, regimes, and feature transforms.",
            )
        )
    return tuple(findings)


def _audit_contract_completeness(
    contract: ExperimentRunContract, *, policy: PromotionPolicy
) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    if len(contract.folds) < policy.min_folds:
        findings.append(
            _fail(
                "contract",
                f"Contract has {len(contract.folds)} folds, below policy minimum {policy.min_folds}.",
                "Export enough walk-forward folds before promotion review.",
            )
        )
    else:
        findings.append(_pass("contract", "Contract satisfies minimum fold count.", "Keep fold count stable."))

    test_observations = sum(fold.test_metrics.observations for fold in contract.folds)
    if test_observations < policy.min_test_observations:
        findings.append(
            _fail(
                "contract",
                f"Contract has {test_observations} test observations, below policy minimum {policy.min_test_observations}.",
                "Increase test-window coverage before promotion review.",
            )
        )
    else:
        findings.append(_pass("contract", "Contract satisfies minimum test observations.", "Keep sample count visible."))

    missing = [name for name in policy.required_artifacts if name not in contract.artifacts]
    if missing:
        findings.append(
            _warn(
                "contract",
                f"Contract is missing expected artifacts: {', '.join(missing)}.",
                "Export the backtest, manifest, and audit artifact references.",
            )
        )
    else:
        findings.append(_pass("contract", "Contract includes expected report artifacts.", "Keep artifact paths stable."))

    if all(feature.fit_scope == "train_only" for feature in contract.features):
        findings.append(_pass("leakage", "All contract features declare train-only fit scope.", "Keep fit scope explicit."))
    else:
        findings.append(
            _fail(
                "leakage",
                "At least one contract feature is not train-only.",
                "Require train-only feature fitting before promotion review.",
            )
        )

    if contract.cost_stress:
        findings.append(_pass("cost", "Contract includes cost-stress scenarios.", "Keep cost stress in promotion review."))
    else:
        findings.append(_fail("cost", "Contract has no cost-stress scenarios.", "Export cost stress before promotion review."))

    if contract.regime_breakdown:
        findings.append(_pass("regime", "Contract includes regime breakdown.", "Keep regime-level fragility visible."))
    else:
        findings.append(_fail("regime", "Contract has no regime breakdown.", "Export regime breakdown before promotion review."))

    if contract.benchmark_comparison:
        findings.append(_pass("benchmark", "Contract includes benchmark comparison.", "Compare against a baseline."))
    else:
        findings.append(_warn("benchmark", "Contract has no benchmark comparison.", "Export benchmark deltas before promotion review."))
    return tuple(findings)


def _audit_contract_time_ordering(contract: ExperimentRunContract) -> tuple[AuditFinding, ...]:
    bad = [
        fold.fold
        for fold in contract.folds
        if not (fold.train_range[1] < fold.validation_range[0] and fold.validation_range[1] < fold.test_range[0])
    ]
    if bad:
        return (
            _fail(
                "validation",
                f"Contract folds are not strictly time ordered: {bad}.",
                "Export train < validation < test windows before promotion review.",
            ),
        )
    return (_pass("validation", "All contract folds are strictly time ordered.", "Keep random splits out of financial ML."),)


def _audit_contract_validation_behavior(
    contract: ExperimentRunContract, *, policy: PromotionPolicy
) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    selected = {fold.selected_threshold for fold in contract.folds}
    if len(selected) <= 1:
        findings.append(
            _warn(
                "validation",
                "The same threshold was selected in every contract fold.",
                "Check whether the validation grid is too narrow or the policy is insensitive.",
            )
        )
    else:
        findings.append(_pass("validation", "Threshold selection varies across contract folds.", "Track fold-level choices."))

    excessive_gaps = [
        fold.fold
        for fold in contract.folds
        if fold.validation_metrics.mean_return - fold.test_metrics.mean_return > policy.max_validation_test_gap
    ]
    if excessive_gaps:
        findings.append(
            _warn(
                "generalization",
                f"Validation-to-test degradation exceeded policy in contract folds: {excessive_gaps}.",
                "Inspect overfitting, threshold search width, and regime shift effects.",
            )
        )
    else:
        findings.append(
            _pass(
                "generalization",
                "Contract validation/test behavior is not uniformly optimistic.",
                "Still compare fold-level degradation before promotion.",
            )
        )
    return tuple(findings)


def _audit_contract_risk_metrics(contract: ExperimentRunContract, *, policy: PromotionPolicy) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    mean_cvar = sum(fold.test_metrics.cvar * fold.test_metrics.observations for fold in contract.folds) / sum(
        fold.test_metrics.observations for fold in contract.folds
    )
    if mean_cvar < 0:
        findings.append(_pass("risk", "Contract records CVaR as a left-tail loss metric.", "Keep CVaR in the promotion gate."))
    else:
        findings.append(
            _warn(
                "risk",
                "Contract mean CVaR is non-negative, which may indicate no active tail-loss sample or a metric issue.",
                "Inspect return distribution and CVaR calculation before trusting the run.",
            )
        )

    high_turnover = [fold.fold for fold in contract.folds if fold.test_metrics.turnover > policy.max_turnover]
    if high_turnover:
        findings.append(
            _warn(
                "cost",
                f"High test turnover detected in contract folds: {high_turnover}.",
                "Stress transaction costs and slippage before considering deployment.",
            )
        )
    else:
        findings.append(_pass("cost", "No contract fold exceeded the high-turnover threshold.", "Keep turnover in every report."))

    weak_sharpe = [fold.fold for fold in contract.folds if fold.test_metrics.sharpe <= policy.min_test_sharpe]
    if weak_sharpe:
        findings.append(
            _warn(
                "risk",
                f"Non-positive test Sharpe detected in contract folds: {weak_sharpe}.",
                "Do not promote the strategy without explaining failed folds.",
            )
        )
    else:
        findings.append(_pass("risk", "All contract folds have positive test Sharpe.", "Confirm this survives cost stress."))
    return tuple(findings)


def _audit_contract_boundary(contract: ExperimentRunContract) -> tuple[AuditFinding, ...]:
    boundary = " ".join(contract.public_boundary).lower()
    if not contract.allow_live_trading and "no live execution" in boundary and "no broker" in boundary:
        return (
            _pass(
                "boundary",
                "Contract explicitly excludes live execution and broker access.",
                "Keep public contracts separate from private strategy operations.",
            ),
        )
    return (
        _warn(
            "boundary",
            "Contract public/private boundary is not explicit enough.",
            "State that public artifacts do not include live execution, broker data, or private thresholds.",
        ),
    )


def _audit_time_ordering(folds: Sequence[ExperimentFoldResult]) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    bad = [
        fold.fold
        for fold in folds
        if not (fold.train_range[1] < fold.validation_range[0] and fold.validation_range[1] < fold.test_range[0])
    ]
    if bad:
        findings.append(
            _fail(
                "validation",
                f"Folds are not strictly time ordered: {bad}.",
                "Use train < validation < test windows before reporting out-of-sample metrics.",
            )
        )
    else:
        findings.append(_pass("validation", "All folds are strictly time ordered.", "Keep random splits out of financial ML."))
    return tuple(findings)


def _audit_validation_behavior(folds: Sequence[ExperimentFoldResult], *, policy: PromotionPolicy) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    selected = {fold.selected_threshold for fold in folds}
    if len(selected) <= 1:
        findings.append(
            _warn(
                "validation",
                "The same threshold was selected in every fold.",
                "Check whether the validation grid is too narrow or the policy is insensitive.",
            )
        )
    else:
        findings.append(_pass("validation", "Threshold selection varies across folds.", "Track fold-level threshold choices."))

    validation_test_gaps = [
        (fold.fold, fold.validation_metrics.mean_return - fold.test_metrics.mean_return) for fold in folds
    ]
    excessive_gaps = [fold for fold, gap in validation_test_gaps if gap > policy.max_validation_test_gap]
    if excessive_gaps:
        findings.append(
            _warn(
                "generalization",
                f"Validation-to-test degradation exceeded policy in folds: {excessive_gaps}.",
                "Inspect overfitting, threshold search width, and regime shift effects.",
            )
        )
    else:
        findings.append(
            _pass(
                "generalization",
                "Validation/test behavior is not uniformly optimistic.",
                "Still compare fold-level degradation before promotion.",
            )
        )
    return tuple(findings)


def _audit_risk_metrics(
    manifest: ExperimentManifest, folds: Sequence[ExperimentFoldResult], *, policy: PromotionPolicy
) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    if manifest.mean_test_cvar < 0:
        findings.append(_pass("risk", "Mean test CVaR is recorded as a left-tail loss metric.", "Keep CVaR in the promotion gate."))
    else:
        findings.append(
            _warn(
                "risk",
                "Mean test CVaR is non-negative, which may indicate no active tail-loss sample or a metric issue.",
                "Inspect return distribution and CVaR calculation before trusting the run.",
            )
        )

    high_turnover = [fold.fold for fold in folds if fold.test_metrics.turnover > policy.max_turnover]
    if high_turnover:
        findings.append(
            _warn(
                "cost",
                f"High test turnover detected in folds: {high_turnover}.",
                "Stress transaction costs and slippage before considering deployment.",
            )
        )
    else:
        findings.append(_pass("cost", "No fold exceeded the high-turnover threshold.", "Keep turnover in every report."))

    weak_sharpe = [fold.fold for fold in folds if fold.test_metrics.sharpe <= policy.min_test_sharpe]
    if weak_sharpe:
        findings.append(
            _warn(
                "risk",
                f"Non-positive test Sharpe detected in folds: {weak_sharpe}.",
                "Do not promote the strategy without explaining failed folds.",
            )
        )
    else:
        findings.append(_pass("risk", "All folds have positive test Sharpe.", "Confirm this survives cost stress."))
    return tuple(findings)


def _audit_operational_boundary(manifest: ExperimentManifest) -> tuple[AuditFinding, ...]:
    boundary = " ".join(manifest.public_boundary).lower()
    if "no live execution" in boundary and "no broker" in boundary:
        return (
            _pass(
                "boundary",
                "Manifest explicitly excludes broker integration and live execution.",
                "Keep public artifacts separate from private strategy operations.",
            ),
        )
    return (
        _warn(
            "boundary",
            "Public/private execution boundary is not explicit.",
            "State that public artifacts do not include live execution, broker data, or private thresholds.",
        ),
    )


def _decision(findings: Sequence[AuditFinding]) -> str:
    if any(finding.severity == "fail" for finding in findings):
        return "reject"
    if any(finding.severity == "warning" for finding in findings):
        return "review_required"
    return "paper_trade_candidate"


def _pass(category: str, message: str, recommendation: str) -> AuditFinding:
    return AuditFinding("pass", category, message, recommendation)


def _warn(category: str, message: str, recommendation: str) -> AuditFinding:
    return AuditFinding("warning", category, message, recommendation)


def _fail(category: str, message: str, recommendation: str) -> AuditFinding:
    return AuditFinding("fail", category, message, recommendation)
