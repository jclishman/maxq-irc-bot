import logging
import sys
import time

current_time = time.strftime('%Y-%m-%d')

# Logging!
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=('%(asctime)s [%(levelname)s] > %(message)s'),)

logger = logging.getLogger(__name__)

handler = logging.FileHandler('Logs/MaxQ ' + current_time.replace(':', '') + '.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] > %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)