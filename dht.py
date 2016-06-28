import pigpio
import time
from collections import namedtuple

# Configuration
DATA_PIN = 25

# Datatype definitions
Timing = namedtuple('Timing', ['min', 'max'])
Reading = namedtuple('Reading', ['temp', 'temp_f', 'humid'])

# Expected quantities and times/tolerances
DATA_BITS = 40  # number of bits of data provided by sensor
EXPECTED_PULSES = 2 * DATA_BITS  # low then high pulse expected for each bit

# Timing tolerances for the single-bus communication
# See section 7.3 of http://akizukidenshi.com/download/ds/aosong/AM2302.pdf
# Minimum and maximum timing values in us
T_RESP = Timing(75, 85)  # Sensor low and high response
T_LOW = Timing(48, 65)  # Signal low time
T_H0 = Timing(22, 30)  # Signal high time for 0 bit
T_H1 = Timing(68, 75)  # Signal high time for 1 bit
TOLERANCE = 5  # tolerance in us, pigpio claims accuracy of "a few" us

# global variables modified by callback threads and read by main()
pulse_lengths = []
prev_time = 0


def main():
    pi = pigpio.pi()

    # attatch a callback function that will record all pulse lengths
    cb = pi.callback(DATA_PIN, pigpio.EITHER_EDGE, edge_callback)

    init_dht(pi, DATA_PIN)  # trigger sensor reading
    
    while len(pulse_lengths) < EXPECTED_PULSES:
        time.sleep(0.1)

    cb.cancel()  # stop listening for edges

    print("Pulse times: " + str(pulse_lengths))
    print("Count: " + str(len(pulse_lengths)))

    temp = parse_pulses(pulse_lengths)


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
    print(message)
    
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


    # remaining pulses should represent data bits
    # every data bit is represented by a low pulse followed by high
    # the duration of the high pulse determines the value of the bit
    parsed_data = ""
    
    if len(pulse_lengths) < EXPECTED_PULSES:
        print("Error reading sensor, unable to read all data bits")

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
          
    print(parsed_data)
    

    # use parsed data to calculate temperature, humidity, and checksum
    temp = int(parsed_data[0:16], 2)
    humid = int(parsed_data[16:32], 2)
    check = int(parsed_data[32:40], 2)

    # verify checksum
    expected = ((temp & 0xff00) >> 8) + (temp & 0x00ff)
    expected += ((humid & 0xff00) >> 8) + (humid & 0x00ff)
    expected = expected % 0xffff
    if check != expected:
        print("Checksum failure: expected {0}, received {1}".format(expected, check))

    print(temp, humid)


if __name__ == "__main__":
    main()
