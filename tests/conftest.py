import pytest
import logging


@pytest.fixture(autouse=True, scope='session')
def enable_logging():
    logging.basicConfig(format='%(asctime)s: [%(levelname)s] %(message)s', level=logging.DEBUG)