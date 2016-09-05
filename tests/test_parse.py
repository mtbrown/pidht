from pidht.parse import within_tolerance, Timing


def test_within_tolerance():
    T_H0 = Timing(20, 40)  # Signal high time for 0 bit
    T_H1 = Timing(60, 80)  # Signal high time for 1 bit

    assert within_tolerance(30, T_H0, 0)
    assert not within_tolerance(41, T_H0, 0)
    assert within_tolerance(19, T_H0, 1)
    assert not within_tolerance(15, T_H0, 4)

    assert within_tolerance(60, T_H1, 0)
    assert not within_tolerance(81, T_H1, 0)
