from collections import defaultdict

from urban_dollop.synth.departures import departures


def test_returns_list_of_dicts():
    rows = departures()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    rows = departures()
    for row in rows:
        assert "resource" in row
        assert "time_interval" in row
        assert "probability" in row


def test_probabilities_sum_to_one_per_resource():
    by_resource = defaultdict(list)
    for row in departures():
        by_resource[row["resource"]].append(row["probability"])
    for probs in by_resource.values():
        assert abs(sum(probs) - 1.0) < 1e-10


def test_probabilities_are_non_negative():
    for row in departures():
        assert row["probability"] >= 0.0


def test_time_intervals_are_positive_integers():
    for row in departures():
        assert isinstance(row["time_interval"], int)
        assert row["time_interval"] >= 1


def test_intervals_are_subset_of_largest_set():
    by_resource = defaultdict(list)
    for row in departures():
        by_resource[row["resource"]].append(row["time_interval"])
    max_interval = max(max(intervals) for intervals in by_resource.values())
    full_set = set(range(1, max_interval + 1))
    for intervals in by_resource.values():
        assert set(intervals).issubset(full_set)


def test_resource_names_are_sequential():
    by_resource = defaultdict(list)
    for row in departures():
        by_resource[row["resource"]].append(row)
    for i, name in enumerate(by_resource):
        assert name == f"resource_{i + 1}"
