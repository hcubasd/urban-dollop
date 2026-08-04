from urban_dollop.synth.time_intervals import time_intervals


def test_zero_sigma_is_a_single_interval():
    rows = time_intervals(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["time_interval"] == "interval_1"


def test_labels_are_sequential_and_in_order():
    rows = time_intervals(sigma=2.0)
    labels = [r["time_interval"] for r in rows]
    assert labels == [f"interval_{i + 1}" for i in range(len(rows))]


def test_durations_are_positive():
    rows = time_intervals(sigma=2.0)
    assert all(r["duration"] > 0 for r in rows)
