import logging
import time
import sys

current_time = time.strftime('%H:%M:%S')


# Logging!
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format=('%(asctime)s [%(levelname)s] > %(message)s'),
)

logger = logging.getLogger(__name__)

handler = logging.FileHandler('Logs/MaxQ ' + current_time.replace(':', '') + '.log')
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] > %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)