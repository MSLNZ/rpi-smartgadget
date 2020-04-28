import pytest

from smartgadget import dewpoint


def measure(t, h, model, expected):
    assert abs(dewpoint(t, h, model=model) - expected) < 1e-9


def test_simple():
    measure(20, 50, 'simple', 10)

    with pytest.raises(ValueError) as err:
        dewpoint(10, 40, model='simple')


def test_general():
    # humidity < 0
    with pytest.raises(ValueError):
        dewpoint(20, -1)

    # humidity > 100
    with pytest.raises(ValueError):
        dewpoint(20, 101)

    # model = 'wrong'
    with pytest.raises(ValueError):
        dewpoint(20, 50, model='wrong')


# model = 'hardy'
# 	TEST RANGE (Range currently undefined)
# 	TEST VALUES


# model = 'wexler'
# 	TEST RANGE DEW < 0
# 	TEST RANGE DEW > 100
# 	TEST RANGE FROST < -100
# 	TEST RANGE FROST > 0.01
# 	TEST VALUES


# model = 'sonntag'
# 	TEST RANGE DEW < 0
# 	TEST RANGE DEW > 100
# 	TEST RANGE FROST < -100
# 	TEST RANGE FROST > 0.01
# 	TEST VALUES


# model = 'clausiusclapeyron'
# 	TEST RANGE (Range currently undefined)
# 	TEST VALUES


# model = 'ardenbuck'
# 	TEST RANGE DEW < 0
# 	TEST RANGE DEW > 50
# 	TEST RANGE FROST < -40
# 	TEST RANGE FROST > 0
# 	TEST VALUES


# model = 'ardenbuck'
# 	TEST RANGE DEW < -40
# 	TEST RANGE DEW > 60
# 	TEST RANGE FROST < -65
# 	TEST RANGE FROST > 0.01
# 	TEST VALUES


# model = 'wagnerpruss'
# 	TEST RANGE DEW < -20
# 	TEST RANGE DEW > 350
# 	TEST RANGE FROST < -70
# 	TEST RANGE FROST > 0
# 	TEST VALUES


# model = 'simple'
# 	TEST RANGE h < 50
# 	TEST VALUES
