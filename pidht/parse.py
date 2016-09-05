"""
The response from the DHT22 sensor is a series of pulses of varying lengths.
The driver will return a list of integers representing the lengths of the pulses
in us. These pulse widths are then compared to various timing tolerances defined below
to determine the actual temperature and humidity values measured by the sensor.

For more information, refer to http://akizukidenshi.com/download/ds/aosong/AM2302.pdf
"""
from collections import namedtuple
import logging

# Data type definitions
Timing = namedtuple('Timing', ['min', 'max'])  # represents a pulse-width range
Reading = namedtuple('Reading', ['temp', 'temp_f', 'humid'])

# Configuration
TOLERANCE = 5  # tolerance in us

# Expected quantities and times/tolerances
DATA_BITS = 40  # number of bits of data provided by sensor
EXPECTED_PULSES = 2 * DATA_BITS  # low then high pulse expected for each bit

# Timing tolerances for the single-bus communication protocol
# See section 7.3 of http://akizukidenshi.com/download/ds/aosong/AM2302.pdf
# Minimum and maximum timing values in us
T_LOW = Timing(40, 70)  # Signal low time
T_H0 = Timing(20, 40)  # Signal high time for 0 bit
T_H1 = Timing(60, 80)  # Signal high time for 1 bit


def within_tolerance(pulse, timing, tolerance=0):
    """
    Determines if the pulse width in us falls within the specified tolerance
    of the timing definition.
    :param pulse: The pulse width in us to analyze
    :param timing: The timing definition the pulse should be within
    :param tolerance: The tolerance in us that is acceptable for the pulse to be outside
    of both ends of the timing definition. Defaults to 0, i.e. the pulse width must be within
    or equal to either end of the timing definition.
    :return: True if the pulse width is within tolerance, else False
    """
    return timing.min - tolerance <= pulse <= timing.max + tolerance


def verify_checksum(parsed_data):
    # the checksum byte should equal the sum of the first 4 bytes
    expected = 0
    for i in range(4):  # loop through first 4 bytes, sum should wrap around at 2^8
        expected = (expected + int(parsed_data[i * 8 : (i + 1) * 8], 2)) % 2**8

    check = int(parsed_data[32:40], 2)  # last byte of data contains checksum
    if check != expected:
        logging.debug("Checksum failure: expected {0}, received {1}".format(expected, check))

    return check == expected


def parse_pulses(pulse_lengths):
    # every data bit is represented by a low pulse followed by high
    # the duration of the high pulse determines the value of the bit
    parsed_data = ""

    logging.debug("Pulse lengths: " + str(pulse_lengths))

    while len(parsed_data) < DATA_BITS:
        t_low = pulse_lengths.pop(0)
        t_high = pulse_lengths.pop(0)

        if not within_tolerance(t_low, T_LOW):
            logging.debug("Invalid data waveform, low time of {0} us out of tolerance".format(t_low))
            return None

        if within_tolerance(t_high, T_H0):
            parsed_data += "0"
        elif within_tolerance(t_high, T_H1):
            parsed_data += "1"
        else:
            logging.debug("Invalid data waveform, high time of {0} us out of tolerance".format(t_high))
            return None

    logging.debug("Parsed data: " + parsed_data)

    if not verify_checksum(parsed_data):
        return None

    # use parsed data to calculate temperature, humidity, and checksum
    humid = int(parsed_data[0:16], 2)
    temp = int(parsed_data[16:32], 2)

    # Read values are 10 larger than actual
    temp *= 0.1
    temp_f = temp * (9 / 5) + 32
    humid *= 0.1

    reading = Reading(temp, temp_f, humid)
    return reading
