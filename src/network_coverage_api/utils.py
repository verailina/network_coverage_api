import importlib.resources
import logging
from functools import wraps
from pathlib import Path
from time import time


def get_logger(level=logging.INFO):
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("network-coverage-api")
    logger.setLevel(level)
    return logger


def timeit(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = function(*args, **kwargs)
        end_time = time()
        logger = get_logger()
        logger.info(
            f"Function {function.__name__} took {end_time - start_time:.4f} seconds"
        )
        return result

    return wrapper


def get_data_path(file_name: str) -> Path:
    data_dir = importlib.resources.files("network_coverage_api.data")
    with importlib.resources.as_file(data_dir) as data_dir:
        data_path = data_dir.joinpath(file_name)
        return data_path
