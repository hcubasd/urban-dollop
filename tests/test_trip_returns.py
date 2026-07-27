from urban_dollop.synth.trip_returns import trip_returns


def test_returns_list_of_dicts():
    rows = trip_returns()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    rows = trip_returns()
    for row in rows:
        assert "resource" in row
        assert "dwell_time" in row
        assert "load_pct" in row


def test_resource_names_are_sequential():
    rows = trip_returns()
    for i, row in enumerate(rows):
        assert row["resource"] == f"resource_{i + 1}"


def test_dwell_time_is_positive_integer():
    for row in trip_returns():
        assert isinstance(row["dwell_time"], int)
        assert row["dwell_time"] >= 1


def test_load_pct_in_unit_interval():
    for row in trip_returns():
        assert 0.0 <= row["load_pct"] < 1.0


def test_one_row_per_resource():
    rows = trip_returns()
    resources = [r["resource"] for r in rows]
    assert len(resources) == len(set(resources))
