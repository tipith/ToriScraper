try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os
import sys
import inspect
import logging
import logging.handlers
import stat
from pathlib import Path

conf_logger = logging.getLogger('Config')

# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# use this if you want to include modules from a subfolder
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "subfolder")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class LoggerWriter:
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


def setup_logging(log_subdir):
    log_file = Path(__location__, log_subdir, 'log.txt')
    if not log_file.parents[0].exists():
        log_file.parents[0].mkdir()

    numeric_level = getattr(logging, loglevel.upper(), logging.DEBUG)

    fmt = logging.Formatter('%(asctime)s %(name)8s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    rootlog = logging.getLogger()
    rootlog.setLevel(numeric_level)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    rootlog.addHandler(ch)

    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3)
    fh.setFormatter(fmt)
    rootlog.addHandler(fh)

    sys.stderr = LoggerWriter(rootlog)

    try:
        os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    except OSError:
        pass


config = configparser.RawConfigParser()
config.read(os.path.join(__location__, 'config.ini'))

try:
    gmail_user = config.get('EMAIL', 'gmail_user')
    gmail_pass = config.get('EMAIL', 'gmail_pass')
except (configparser.NoOptionError, configparser.NoSectionError):
    pass

db_user = config.get('DATABASE', 'db_user')
db_pass = config.get('DATABASE', 'db_pass')
db_host = config.get('DATABASE', 'db_host')
db_name = config.get('DATABASE', 'db_name')

loglevel = config.get('COMMON', 'loglevel')

setup_logging('logs')

