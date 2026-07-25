from urban_dollop.helpers.primes import primes
from urban_dollop.synth.resource_thresholds import resource_thresholds


def test_returns_headers_and_rows():
    headers, rows = resource_thresholds()
    assert isinstance(headers, list)
    assert isinstance(rows, list)
    assert len(rows) >= 1


def test_headers_are_primes():
    headers, _ = resource_thresholds()
    assert headers == primes(len(headers))


def test_rows_have_resource_and_header_keys():
    headers, rows = resource_thresholds()
    for row in rows:
        assert "resource" in row
        for h in headers:
            assert h in row


def test_mus_are_sorted_ascending():
    headers, rows = resource_thresholds()
    for row in rows:
        values = [row[h] for h in headers if row[h] is not None]
        assert values == sorted(values)


def test_resource_names_are_sequential():
    _, rows = resource_thresholds()
    for i, row in enumerate(rows):
        assert row["resource"] == f"resource_{i + 1}"
