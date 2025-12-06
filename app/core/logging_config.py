import logging.config
import sys

def setup_logging():
    """
    Configures the application's logging to output structured JSON logs.
    """
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout, 
            },
        },
        "loggers": {
            "app": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "alembic": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "": {
                "handlers": ["console"],
                "level": "WARNING",
            },
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)