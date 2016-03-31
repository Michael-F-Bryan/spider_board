import os
import logging
import time
import functools
import sys


# Constants
# =========

LOG_FILE = os.path.abspath('scraper_log.log')
FILESIZE_SUFFIX = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

# Functions
# =========

def get_logger(name, log_file, log_level=None):
    logger = logging.getLogger(name)

    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s: %(message)s",
            datefmt='%Y/%m/%d %I:%M:%S %p')

    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level or logging.DEBUG)
    logger.addHandler(file_handler)

    return logger

def humansize(nbytes):
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(FILESIZE_SUFFIX)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, FILESIZE_SUFFIX[i])


# Decorators
# ==========

def time_job(stream=sys.stdout, decimal_places=2):
    def actual_time_job(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # Start the timer.
            start = time.time()
            # Run the decorated function.
            ret = func(*args, **kwargs)
            # Stop the timer.
            end = time.time()
            elapsed = end - start

            stream.write("{0} took {1:.{2}f} seconds\n".format(
                    func.__name__, 
                    elapsed,
                    decimal_places))
        return wrapper
    return actual_time_job
