from urban_dollop.synth.time_intervals import time_intervals


def test_returns_list_of_dicts():
    rows = time_intervals()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    for row in time_intervals():
        assert "time_interval" in row
        assert "duration" in row


def test_time_interval_labels_are_strings():
    for row in time_intervals():
        assert isinstance(row["time_interval"], str)
        assert row["time_interval"].startswith("interval_")


def test_time_interval_labels_sequential():
    rows = time_intervals()
    for i, row in enumerate(rows):
        assert row["time_interval"] == f"interval_{i + 1}"


def test_duration_is_positive():
    for row in time_intervals():
        assert row["duration"] > 0.0


def test_no_duplicate_intervals():
    rows = time_intervals()
    labels = [r["time_interval"] for r in rows]
    assert len(labels) == len(set(labels))
