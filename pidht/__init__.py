import logging
import time

# Proceed even if driver is not installed so that parsing can be tested
try:
    DRIVER_AVAIL = True
    from .driver import dht_read
except ImportError:
    DRIVER_AVAIL = False
    print("pidht was not installed correctly and the driver is unavailable")

from .parse import parse_pulses


def read(pin, retries=5):
    if not DRIVER_AVAIL:
        print("Unable to read, driver was not installed correctly")
        return

    for i in range(retries):
        logging.debug("Attempting to read DHT sensor")
        pulse_lengths = dht_read(pin)

        logging.debug("Parsing DHT sensor response")
        reading = parse_pulses(pulse_lengths)
        if reading is None:
            logging.debug("Invalid DHT sensor response")
            if retries:
                time.sleep(0.5)
        else:
            logging.debug("Successfully read DHT sensor")
            return reading

    logging.error("Unable to read the DHT sensor, retries exhausted")
