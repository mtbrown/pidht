import pigpio
import time
from collections import namedtuple
import logging

# Configuration
DATA_PIN = 25

# Datatype definitions
Timing = namedtuple('Timing', ['min', 'max'])
Reading = namedtuple('Reading', ['temp', 'temp_f', 'humid'])

# Expected quantities and times/tolerances
DATA_BITS = 40  # number of bits of data provided by sensor
EXPECTED_PULSES = 2 * DATA_BITS  # low then high pulse expected for each bit
TIMEOUT = 3 * 100000  # timeout in us

# Timing tolerances for the single-bus communication
# See section 7.3 of http://akizukidenshi.com/download/ds/aosong/AM2302.pdf
# Minimum and maximum timing values in us
T_RESP = Timing(75, 85)  # Sensor low and high response
T_LOW = Timing(48, 70)  # Signal low time
T_H0 = Timing(22, 30)  # Signal high time for 0 bit
T_H1 = Timing(68, 75)  # Signal high time for 1 bit
TOLERANCE = 5  # tolerance in us, pigpio claims accuracy of "a few" us

# global variables modified by callback threads and read by main()
pulse_lengths = []
prev_time = 0


def main():
    print(read(DATA_PIN))


def read(pin, retries=3):
    for i in range(retries):
        reading = try_read(pin)
        if reading is not None:
            return reading

    return None


def try_read(pin):
    pi = pigpio.pi()

    # attatch a callback function that will record all pulse lengths
    cb = pi.callback(pin, pigpio.EITHER_EDGE, edge_callback)

    init_dht(pi, pin)  # trigger sensor reading
    
    start = pi.get_current_tick()
    while len(pulse_lengths) < EXPECTED_PULSES and pigpio.tickDiff(start, pi.get_current_tick()) < TIMEOUT:
        time.sleep(0.1)

    cb.cancel()  # stop listening for edges

    logging.debug("Pulse times: " + str(pulse_lengths))
    logging.debug("Count: " + str(len(pulse_lengths)))

    reading = parse_pulses(pulse_lengths)
    return reading


def init_dht(pi, pin):
    pi.set_mode(pin, pigpio.OUTPUT)
    pi.set_pull_up_down(pin, pigpio.PUD_UP)

    pi.write(pin, 0)
    time.sleep(0.001)  # hold data pin low for 1ms
    pi.set_mode(pin, pigpio.INPUT)  # release bus


def edge_callback(pin, level, time):
    global prev_time
    global pulse_lengths

    delta = pigpio.tickDiff(prev_time, time)  # Use tickDiff() to handle clock wrap-around
    message = "Detected {0} edge on pin {1} at time {2}, was {3} for {4}us".format(
            "rising" if level else "falling", pin, time, "low" if level else "high", delta)
    logging.debug(message)
    
    prev_time = time
    pulse_lengths.append(delta)


def within_tolerance(pulse, timing):
    return timing.min - TOLERANCE <= pulse <= timing.max + TOLERANCE


def parse_pulses(pulse_lengths):
    # attempt to locate sensor response pulses to locate start of data
    # there should be a low pulse followed by a high pulse, both within T_RESP
    # initialization pulse data is discarded
    resp_pulse_count = 0  # consecutive response pulse count
    while resp_pulse_count < 2 and pulse_lengths:
        pulse = pulse_lengths.pop(0)
        if within_tolerance(pulse, T_RESP):
            resp_pulse_count += 1
        else:
            resp_pulse_count = 0
    if not pulse_lengths:
        print("Unable to locate sensor response pulse when parsing waveform")
        return None


    # remaining pulses should represent data bits
    # every data bit is represented by a low pulse followed by high
    # the duration of the high pulse determines the value of the bit
    parsed_data = ""
    
    if len(pulse_lengths) < EXPECTED_PULSES:
        print("Error reading sensor, unable to read all data bits")
        return None

    while len(parsed_data) < DATA_BITS:
        t_low = pulse_lengths.pop(0)
        t_high = pulse_lengths.pop(0)

        if not within_tolerance(t_low, T_LOW):
            print("Invalid data waveform, low time of {0} out of tolerance".format(t_low))

        if within_tolerance(t_high, T_H0):
            parsed_data += "0"
        elif within_tolerance(t_high, T_H1):
            parsed_data += "1"
        else:
            print("Invalid data waveform, high time of {0} out of tolerance".format(t_high))
          
    logging.debug(parsed_data)
    

    # use parsed data to calculate temperature, humidity, and checksum
    humid = int(parsed_data[0:16], 2)
    temp = int(parsed_data[16:32], 2)
    check = int(parsed_data[32:40], 2)

    # verify checksum, the checksum byte should equal the sum of the other 4 bytes
    expected = 0
    for i in range(4):  # loop through first 4 bytes, sum should wrap around at 2^8
        expected = (expected + int(parsed_data[i * 8 : (i + 1) * 8], 2)) % 2**8

    if check != expected:
        logging.error("Checksum failure: expected {0}, received {1}".format(expected, check))
        return None

    # Read values are 10 larger than actual
    temp *= 0.1
    temp_f = temp * (9 / 5) + 32
    humid *= 0.1

    reading = Reading(temp, temp_f, humid)
    return reading


if __name__ == "__main__":
    main()
