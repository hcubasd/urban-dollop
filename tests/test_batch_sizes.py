from collections import defaultdict

from urban_dollop.synth.batch_sizes import batch_sizes


def test_returns_list_of_dicts():
    rows = batch_sizes()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    rows = batch_sizes()
    for row in rows:
        assert "resource" in row
        assert "batch_size" in row
        assert "probability" in row


def test_probabilities_sum_to_one_per_resource():
    by_resource = defaultdict(list)
    for row in batch_sizes():
        by_resource[row["resource"]].append(row["probability"])
    for resource, probs in by_resource.items():
        assert abs(sum(probs) - 1.0) < 1e-10


def test_probabilities_are_non_negative():
    for row in batch_sizes():
        assert row["probability"] >= 0.0


def test_batch_sizes_are_positive_integers():
    for row in batch_sizes():
        assert isinstance(row["batch_size"], int)
        assert row["batch_size"] >= 1


def test_resource_names_are_sequential():
    by_resource = defaultdict(list)
    for row in batch_sizes():
        by_resource[row["resource"]].append(row)
    for i, name in enumerate(by_resource):
        assert name == f"resource_{i + 1}"
