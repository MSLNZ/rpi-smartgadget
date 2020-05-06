import pytest

from smartgadget import dewpoint


def measure(t, h, model, df, expected):
    assert abs(dewpoint(t, h, model=model, isdew=df) - expected) < 1e-9


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
def test_hardy():
    print('this is currently empty')
    # TEST RANGE (Range currently undefined)
    # with pytest.raises(ValueError):
    #    dewpoint(temp, humd, model='hardy')
    # TEST VALUES


# model = 'wexler'
def test_wexler():
    # TEST RANGE DEW < 0
    with pytest.raises(ValueError):
        dewpoint(-1, 50, model='wexler', isdew=True)
    # TEST RANGE DEW > 100
    with pytest.raises(ValueError):
        dewpoint(101, 50, model='wexler', isdew=True)
    # TEST RANGE FROST < -100
    with pytest.raises(ValueError):
        dewpoint(-101, 50, model='wexler', isdew=False)
    # TEST RANGE FROST > 0.01
    with pytest.raises(ValueError):
        dewpoint(0.02, 50, model='wexler', isdew=False)
    # TEST VALUES


# model = 'sonntag'
def test_sonntag():
    # TEST RANGE DEW < 0
    with pytest.raises(ValueError):
        dewpoint(-1, 50, model='sonntag', isdew=True)
    # TEST RANGE DEW > 100
    with pytest.raises(ValueError):
        dewpoint(101, 50, model='sonntag', isdew=True)
    # TEST RANGE FROST < -100
    with pytest.raises(ValueError):
        dewpoint(-101, 50, model='sonntag', isdew=False)
    # TEST RANGE FROST > 0.01
    with pytest.raises(ValueError):
        dewpoint(0.02, 50, model='sonntag', isdew=False)
    # TEST VALUES


# model = 'clausiusclapeyron'
def test_clausiusclapeyron():
    print('this is currently empty')
    # TEST RANGE (Range currently undefined)
    # with pytest.raises(ValueError):
    #      dewpoint(-1, 50, model='sonntag', isdew=True)
    # 	TEST VALUES


# model = 'ardenbuck'
def test_ardenbuck():
    # TEST RANGE DEW < 0
    with pytest.raises(ValueError):
        dewpoint(-1, 50, model='ardenbuck', isdew=True)
    # TEST RANGE DEW > 50
    with pytest.raises(ValueError):
        dewpoint(51, 50, model='ardenbuck', isdew=True)
    # TEST RANGE FROST < -40
    with pytest.raises(ValueError):
        dewpoint(-41, 50, model='ardenbuck', isdew=False)
    # TEST RANGE FROST > 0
    with pytest.raises(ValueError):
        dewpoint(1, 50, model='ardenbuck', isdew=False)
    # TEST VALUES


# model = 'magnus'
def test_magnus():
    # TEST RANGE DEW < -45
    with pytest.raises(ValueError):
        dewpoint(-46, 50, model='magnus', isdew=True)
    # TEST RANGE DEW > 60
    with pytest.raises(ValueError):
        dewpoint(61, 50, model='magnus', isdew=True)
    # TEST RANGE FROST < -65
    with pytest.raises(ValueError):
        dewpoint(-66, 50, model='magnus', isdew=False)
    # TEST RANGE FROST > 0.01
    with pytest.raises(ValueError):
        dewpoint(0.02, 50, model='magnus', isdew=False)
    # TEST VALUES


# model = 'wagnerpruss'
def test_wagnerpruss():
    # TEST RANGE DEW < -20
    with pytest.raises(ValueError):
        dewpoint(-21, 50, model='wagnerpruss', isdew=True)
    # TEST RANGE DEW > 350
    with pytest.raises(ValueError):
        dewpoint(351, 50, model='wagnerpruss', isdew=True)
    # TEST RANGE FROST < -70
    with pytest.raises(ValueError):
        dewpoint(-71, 50, model='wagnerpruss', isdew=False)
    # TEST RANGE FROST > 0
    with pytest.raises(ValueError):
        dewpoint(1, 50, model='wagnerpruss', isdew=False)
    # TEST VALUES


# model = 'simple'
def test_simple():
    # TEST RANGE h < 50
    with pytest.raises(ValueError):
        dewpoint(20, 49, model='simple')
    # TEST VALUES
    # measure(20, 50, 'simple', True, 10)
