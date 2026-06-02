from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class LabelSpan:
    sample_index: int
    start: int
    end: int


@dataclass(frozen=True)
class PurgedEmbargoSplit:
    fold: int
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]
    purged_indices: tuple[int, ...]
    embargoed_indices: tuple[int, ...]
    test_label_span: tuple[int, int]


def make_label_spans(data_length: int, *, label_horizon: int) -> tuple[LabelSpan, ...]:
    if data_length <= 0:
        raise ValueError("data_length must be positive")
    if label_horizon <= 0:
        raise ValueError("label_horizon must be positive")
    if label_horizon >= data_length:
        raise ValueError("label_horizon must be smaller than data_length")

    return tuple(
        LabelSpan(sample_index=index, start=index, end=index + label_horizon)
        for index in range(data_length - label_horizon + 1)
    )


def intervals_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    left_start, left_end = left
    right_start, right_end = right
    if left_start >= left_end or right_start >= right_end:
        raise ValueError("intervals must be half-open [start, end) ranges")
    return left_start < right_end and right_start < left_end


def test_label_span(test_indices: Sequence[int], *, label_horizon: int) -> tuple[int, int]:
    if not test_indices:
        raise ValueError("test_indices must not be empty")
    ordered = tuple(sorted(test_indices))
    return (ordered[0], ordered[-1] + label_horizon)


def purge_and_embargo_train_indices(
    label_spans: Sequence[LabelSpan],
    *,
    test_indices: Sequence[int],
    label_horizon: int,
    embargo_size: int,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], tuple[int, int]]:
    if embargo_size < 0:
        raise ValueError("embargo_size must be non-negative")

    test_set = set(test_indices)
    label_by_index = {span.sample_index: span for span in label_spans}
    missing = sorted(test_set - set(label_by_index))
    if missing:
        raise ValueError(f"test indices without labels: {missing}")

    heldout_span = test_label_span(test_indices, label_horizon=label_horizon)
    embargo_span = (heldout_span[1], heldout_span[1] + embargo_size)

    train: list[int] = []
    purged: list[int] = []
    embargoed: list[int] = []

    for span in label_spans:
        index = span.sample_index
        if index in test_set:
            continue
        if intervals_overlap((span.start, span.end), heldout_span):
            purged.append(index)
            continue
        if embargo_size > 0 and embargo_span[0] <= index < embargo_span[1]:
            embargoed.append(index)
            continue
        train.append(index)

    return tuple(train), tuple(purged), tuple(embargoed), heldout_span


def make_purged_embargo_splits(
    data_length: int,
    *,
    label_horizon: int,
    test_size: int,
    embargo_size: int,
    step_size: int | None = None,
    min_train_size: int = 1,
) -> tuple[PurgedEmbargoSplit, ...]:
    if test_size <= 0:
        raise ValueError("test_size must be positive")
    if min_train_size <= 0:
        raise ValueError("min_train_size must be positive")

    spans = make_label_spans(data_length, label_horizon=label_horizon)
    label_count = len(spans)
    step = step_size or test_size
    if step <= 0:
        raise ValueError("step_size must be positive")

    folds: list[PurgedEmbargoSplit] = []
    fold = 1
    for test_start in range(0, label_count - test_size + 1, step):
        test_indices = tuple(range(test_start, test_start + test_size))
        train, purged, embargoed, heldout_span = purge_and_embargo_train_indices(
            spans,
            test_indices=test_indices,
            label_horizon=label_horizon,
            embargo_size=embargo_size,
        )
        if len(train) < min_train_size:
            continue
        folds.append(
            PurgedEmbargoSplit(
                fold=fold,
                train_indices=train,
                test_indices=test_indices,
                purged_indices=purged,
                embargoed_indices=embargoed,
                test_label_span=heldout_span,
            )
        )
        fold += 1

    if not folds:
        raise ValueError("no folds available after purge/embargo")
    return tuple(folds)


def assert_no_label_overlap(split: PurgedEmbargoSplit, *, label_horizon: int) -> None:
    for index in split.train_indices:
        if intervals_overlap((index, index + label_horizon), split.test_label_span):
            raise ValueError(f"train index {index} overlaps test label span {split.test_label_span}")
