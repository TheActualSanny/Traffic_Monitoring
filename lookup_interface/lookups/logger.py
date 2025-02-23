import logging

main_logger = logging.getLogger('main_logger')
main_logger.setLevel(logging.ERROR)
logger_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logger_format)
main_logger.addHandler(stream_handler)