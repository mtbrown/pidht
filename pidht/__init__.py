import logging
import time
import sys

from .driver import dht_read
from .parse import parse_pulses


def read(pin, retries=5):
    for i in range(retries):
        logging.debug("Attempting to read DHT sensor")
        pulse_lengths = dht_read(pin)

        logging.debug("Parsing DHT sensor response")
        reading = parse_pulses(pulse_lengths)
        if reading is None:
            logging.debug("Invalid DHT sensor response")
            if retries:
                time.sleep(0.1)
        else:
            logging.debug("Successfully read DHT sensor")
            return reading

    logging.error("Unable to read the DHT sensor, retries exhausted")
    return None
