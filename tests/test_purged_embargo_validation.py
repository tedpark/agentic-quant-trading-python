from agentic_quant.validation.demo_purged_embargo import render_markdown
from agentic_quant.validation.purged_embargo import (
    assert_no_label_overlap,
    intervals_overlap,
    make_label_spans,
    make_purged_embargo_splits,
    purge_and_embargo_train_indices,
)


def test_intervals_overlap_uses_half_open_ranges() -> None:
    assert intervals_overlap((0, 5), (4, 8))
    assert not intervals_overlap((0, 5), (5, 8))


def test_purge_removes_labels_that_overlap_test_span() -> None:
    spans = make_label_spans(64, label_horizon=5)
    train, purged, embargoed, heldout_span = purge_and_embargo_train_indices(
        spans,
        test_indices=range(24, 36),
        label_horizon=5,
        embargo_size=3,
    )

    assert heldout_span == (24, 40)
    assert 20 in purged
    assert 23 in purged
    assert 36 not in train
    assert 36 in purged
    assert 40 in embargoed
    assert 43 not in embargoed


def test_purged_embargo_splits_have_no_label_overlap() -> None:
    splits = make_purged_embargo_splits(
        101,
        label_horizon=5,
        test_size=12,
        embargo_size=3,
        step_size=12,
    )

    assert len(splits) == 8
    for split in splits:
        assert_no_label_overlap(split, label_horizon=5)
        assert set(split.train_indices).isdisjoint(split.test_indices)
        assert set(split.purged_indices).isdisjoint(split.train_indices)
        assert set(split.embargoed_indices).isdisjoint(split.train_indices)


def test_purged_embargo_markdown_declares_boundary() -> None:
    markdown = render_markdown()

    assert "# Purged + Embargoed Validation Sample" in markdown
    assert "label-overlap leakage" in markdown
    assert "not investment advice" in markdown
