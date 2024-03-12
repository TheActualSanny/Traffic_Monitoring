import logging

def logger_setup():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  [%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M::%S'

    )

logger_setup()
logger = logging.getLogger(__name__)
