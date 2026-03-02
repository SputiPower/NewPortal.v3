import logging


class LevelBasedConsoleFormatter(logging.Formatter):
    """
    Console formatter with level-dependent output:
    - DEBUG/INFO: asctime level message
    - WARNING: asctime level message pathname
    - ERROR/CRITICAL: asctime level message pathname exc_info
    """

    base_format = "%(asctime)s | %(levelname)s | %(message)s"
    warning_suffix = " | %(pathname)s"
    error_suffix = " | %(pathname)s | %(exc_info)s"

    def __init__(self, datefmt=None):
        super().__init__(datefmt=datefmt)
        self._base = logging.Formatter(fmt=self.base_format, datefmt=datefmt)
        self._warning = logging.Formatter(
            fmt=self.base_format + self.warning_suffix,
            datefmt=datefmt,
        )
        self._error = logging.Formatter(
            fmt=self.base_format + self.error_suffix,
            datefmt=datefmt,
        )

    def format(self, record):
        if record.levelno >= logging.ERROR:
            return self._error.format(record)
        if record.levelno >= logging.WARNING:
            return self._warning.format(record)
        return self._base.format(record)

