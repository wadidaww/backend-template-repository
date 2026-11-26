from __future__ import annotations

import logging
import sys

import structlog


def setup_logging(app_env: str = "development") -> None:
    dev = app_env == "development"
    log_level = logging.DEBUG if dev else logging.INFO

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    renderer: list[structlog.types.Processor] = (
        [structlog.dev.ConsoleRenderer()]
        if dev
        else [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
    )

    structlog.configure(
        processors=[*shared_processors, *renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)
    # Third-party loggers that are too chatty at DEBUG.
    for noisy in ("aiosqlite", "asyncio", "httpcore", "multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
