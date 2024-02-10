import logging
from functools import wraps
from time import time


def get_logger(level=logging.INFO):
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    return logger


def timeit(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = function(*args, **kwargs)
        end_time = time()
        logger = get_logger()
        logger.info(f"Function {function.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper
