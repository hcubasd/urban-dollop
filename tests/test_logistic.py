from urban_dollop.helpers.logistic import logistic


def test_logistic_zero():
    assert logistic(0.0) == 0.5


def test_logistic_positive_large():
    assert logistic(100.0) > 0.999


def test_logistic_negative_large():
    assert logistic(-100.0) < 0.001


def test_logistic_output_in_unit_interval():
    for x in [-10.0, -1.0, 0.0, 1.0, 10.0]:
        assert 0.0 < logistic(x) < 1.0
