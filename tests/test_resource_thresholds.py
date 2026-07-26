from urban_dollop.synth.resource_thresholds import resource_thresholds


def test_returns_list_of_rows():
    rows = resource_thresholds()
    assert isinstance(rows, list)
    assert len(rows) >= 1


def test_rows_have_required_keys():
    rows = resource_thresholds()
    for row in rows:
        assert "resource" in row
        assert "resource_level" in row
        assert "threshold" in row


def test_last_level_per_resource_has_no_threshold():
    rows = resource_thresholds()
    resources = dict()
    for row in rows:
        resources.setdefault(row["resource"], []).append(row)
    for levels in resources.values():
        assert levels[-1]["threshold"] is None


def test_all_but_last_level_have_threshold():
    rows = resource_thresholds()
    resources = dict()
    for row in rows:
        resources.setdefault(row["resource"], []).append(row)
    for levels in resources.values():
        for row in levels[:-1]:
            assert row["threshold"] is not None


def test_thresholds_are_sorted_ascending():
    rows = resource_thresholds()
    resources = dict()
    for row in rows:
        resources.setdefault(row["resource"], []).append(row)
    for levels in resources.values():
        mus = [row["threshold"] for row in levels if row["threshold"] is not None]
        assert mus == sorted(mus)


def test_resource_levels_are_sorted_subset_of_primes():
    from urban_dollop.helpers.primes import primes
    rows = resource_thresholds()
    max_level = max(row["resource_level"] for row in rows)
    full_primes = set(primes(len([r for r in rows if r["resource_level"] <= max_level])))
    resources = dict()
    for row in rows:
        resources.setdefault(row["resource"], []).append(row)
    for levels in resources.values():
        level_vals = [row["resource_level"] for row in levels]
        assert level_vals == sorted(level_vals)
        assert all(v in full_primes for v in level_vals)
