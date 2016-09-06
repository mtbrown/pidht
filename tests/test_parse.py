from pidht.parse import T_H0, T_H1, T_LOW
from pidht.parse import within_tolerance, Timing, verify_checksum, parse_pulses, Reading


def generate_pulses(parsed_data):
    """
    Used by tests to convert an expected binary reading to a list of corresponding
    pulse durations that can be passed to parse_pulses().
    :param parsed_data:
    :return:
    """
    pulses = []
    for c in parsed_data:
        pulses.append(T_LOW.min)
        pulses.append(T_H0.min if c == '0' else T_H1.min)
    return pulses


def test_within_tolerance():
    T_H0 = Timing(20, 40)  # Signal high time for 0 bit
    T_H1 = Timing(60, 80)  # Signal high time for 1 bit

    assert within_tolerance(30, T_H0, 0)
    assert not within_tolerance(41, T_H0, 0)
    assert within_tolerance(19, T_H0, 1)
    assert not within_tolerance(15, T_H0, 4)

    assert within_tolerance(60, T_H1, 0)
    assert not within_tolerance(81, T_H1, 0)


def test_verify_checksum():
    # example taken from data sheet
    assert verify_checksum("0000001010010010000000010000110110100010")

    # shift example right 1 bit
    assert not verify_checksum("0000000101001001000000001000011011010001")
    # mutate random bit
    assert not verify_checksum("0000001010010110000000010000110110100010")
    # mutate checksum bit
    assert not verify_checksum("0000001010010010000000010000110110101010")


def test_parse_pulses_basic():
    # equivalent to 0000001010010010000000010000110110100010, taken from data sheet
    reading = parse_pulses([46, 35, 45, 26, 54, 35, 50, 30, 54, 26, 55, 27, 54, 75, 52, 33, 47, 75, 53,
                            34, 55, 27, 47, 73, 46, 31, 53, 26, 52, 65, 51, 26, 51, 32, 47, 34, 54, 25,
                            54, 35, 53, 35, 53, 34, 52, 31, 49, 75, 52, 25, 51, 28, 49, 27, 53, 28, 52,
                            70, 46, 65, 48, 30, 55, 66, 50, 69, 46, 33, 55, 71, 50, 35, 53, 25, 47, 34,
                            45, 73, 55, 29])
    assert abs(reading.temp - 26.9) < 0.1
    assert abs(reading.humid - 65.8) < 0.1
    assert abs(reading.temp_f - 80.42) < 0.01


def test_parse_pulses_negative_temp():
    pulses = generate_pulses("0000001010010010" + "1000000001100101" + "01111001")
    reading = parse_pulses(pulses)
    assert abs(reading.temp - -10.1) < 0.1
    assert abs(reading.humid - 65.8) < 0.1
    assert abs(reading.temp_f - 13.82) < 0.01
