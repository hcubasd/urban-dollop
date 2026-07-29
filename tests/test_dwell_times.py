from urban_dollop.synth.dwell_times import dwell_times


def test_returns_list_of_dicts():
    rows = dwell_times()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    rows = dwell_times()
    for row in rows:
        assert "resource" in row
        assert "dwell_time" in row
        assert "load_pct" in row


def test_resource_names_are_sequential():
    rows = dwell_times()
    for i, row in enumerate(rows):
        assert row["resource"] == f"resource_{i + 1}"


def test_dwell_time_is_positive_float():
    for row in dwell_times():
        assert isinstance(row["dwell_time"], float)
        assert row["dwell_time"] > 0.0


def test_load_pct_in_unit_interval():
    for row in dwell_times():
        assert 0.0 <= row["load_pct"] < 1.0


def test_one_row_per_resource():
    rows = dwell_times()
    resources = [r["resource"] for r in rows]
    assert len(resources) == len(set(resources))
