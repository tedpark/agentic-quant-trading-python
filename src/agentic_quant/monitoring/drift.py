from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from statistics import median
from typing import Mapping, Sequence


EPSILON = 1e-9


@dataclass(frozen=True)
class FeatureDrift:
    name: str
    psi: float
    ks: float
    severity: str
    reference_count: int
    current_count: int
    reference_median: float
    current_median: float


@dataclass(frozen=True)
class DriftReport:
    features: tuple[FeatureDrift, ...]

    @property
    def worst_feature(self) -> FeatureDrift | None:
        return self.features[0] if self.features else None

    def severity_counts(self) -> dict[str, int]:
        counts = {"ok": 0, "moderate": 0, "significant": 0}
        for feature in self.features:
            counts[feature.severity] += 1
        return counts

    def to_markdown(self) -> str:
        counts = self.severity_counts()
        lines = [
            "# Drift Report",
            "",
            "This sample report compares reference and current feature distributions.",
            "It uses synthetic data only and does not expose a live trading universe.",
            "",
            "## Summary",
            "",
            f"- ok: {counts['ok']}",
            f"- moderate: {counts['moderate']}",
            f"- significant: {counts['significant']}",
            "",
            "## Features",
            "",
            "| Feature | Severity | PSI | KS | Reference Median | Current Median |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for feature in self.features:
            lines.append(
                "| "
                f"{feature.name} | {feature.severity} | {feature.psi:.4f} | "
                f"{feature.ks:.4f} | {feature.reference_median:.4f} | "
                f"{feature.current_median:.4f} |"
            )
        lines.extend(
            [
                "",
                "## Boundary",
                "",
                "This report is an engineering pattern, not investment advice or a live signal.",
            ]
        )
        return "\n".join(lines) + "\n"


def clean_values(values: Sequence[float]) -> list[float]:
    cleaned = [float(value) for value in values if isfinite(float(value))]
    if not cleaned:
        raise ValueError("feature values must contain at least one finite number")
    return cleaned


def quantile_edges(reference: Sequence[float], bins: int = 10) -> list[float]:
    if bins < 2:
        raise ValueError("bins must be at least 2")

    values = sorted(clean_values(reference))
    edges = [values[0]]
    for index in range(1, bins):
        position = round(index * (len(values) - 1) / bins)
        edges.append(values[position])
    edges.append(values[-1])

    deduped = [edges[0]]
    for edge in edges[1:]:
        if edge > deduped[-1]:
            deduped.append(edge)
    if len(deduped) < 2:
        raise ValueError("reference distribution must have at least two distinct values")
    return deduped


def bucket_counts(values: Sequence[float], edges: Sequence[float]) -> list[int]:
    cleaned = clean_values(values)
    counts = [0 for _ in range(len(edges) - 1)]
    for value in cleaned:
        bucket = 0
        while bucket < len(edges) - 2 and value > edges[bucket + 1]:
            bucket += 1
        counts[bucket] += 1
    return counts


def population_stability_index(
    reference: Sequence[float],
    current: Sequence[float],
    *,
    bins: int = 10,
) -> float:
    edges = quantile_edges(reference, bins=bins)
    reference_counts = bucket_counts(reference, edges)
    current_counts = bucket_counts(current, edges)
    reference_total = sum(reference_counts)
    current_total = sum(current_counts)

    psi = 0.0
    for reference_count, current_count in zip(reference_counts, current_counts, strict=True):
        reference_share = max(reference_count / reference_total, EPSILON)
        current_share = max(current_count / current_total, EPSILON)
        psi += (current_share - reference_share) * log(current_share / reference_share)
    return float(psi)


def ks_statistic(reference: Sequence[float], current: Sequence[float]) -> float:
    left = sorted(clean_values(reference))
    right = sorted(clean_values(current))
    values = sorted(set(left + right))
    left_index = 0
    right_index = 0
    max_distance = 0.0

    for value in values:
        while left_index < len(left) and left[left_index] <= value:
            left_index += 1
        while right_index < len(right) and right[right_index] <= value:
            right_index += 1
        left_cdf = left_index / len(left)
        right_cdf = right_index / len(right)
        max_distance = max(max_distance, abs(left_cdf - right_cdf))
    return max_distance


def classify_drift(psi: float, ks: float) -> str:
    if psi >= 0.25 or ks >= 0.2:
        return "significant"
    if psi >= 0.1 or ks >= 0.1:
        return "moderate"
    return "ok"


def detect_drift(
    reference: Mapping[str, Sequence[float]],
    current: Mapping[str, Sequence[float]],
    *,
    bins: int = 10,
) -> DriftReport:
    missing = sorted(set(reference) - set(current))
    if missing:
        raise ValueError(f"current data missing features: {missing}")

    features: list[FeatureDrift] = []
    for name, reference_values in reference.items():
        current_values = current[name]
        ref_clean = clean_values(reference_values)
        cur_clean = clean_values(current_values)
        psi = population_stability_index(ref_clean, cur_clean, bins=bins)
        ks = ks_statistic(ref_clean, cur_clean)
        features.append(
            FeatureDrift(
                name=name,
                psi=psi,
                ks=ks,
                severity=classify_drift(psi, ks),
                reference_count=len(ref_clean),
                current_count=len(cur_clean),
                reference_median=median(ref_clean),
                current_median=median(cur_clean),
            )
        )

    severity_rank = {"significant": 0, "moderate": 1, "ok": 2}
    ordered = tuple(
        sorted(features, key=lambda feature: (severity_rank[feature.severity], -feature.psi, -feature.ks))
    )
    return DriftReport(features=ordered)
