"""
Structlog configuration with FastAPI.
Features:
- async bound logger
- contextvars to log request-id and other meta data
- custom format for default logging loggers and structlog loggers
Refs:
- https://gist.github.com/nkhitrov/38adbb314f0d35371eba4ffb8f27078f
- https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e
"""

import logging
import sys

import structlog
from structlog.types import EventDict, Processor


# https://github.com/hynek/structlog/issues/35#issuecomment-591321744
def rename_event_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Log entries keep the text message in the `event` field, but Datadog
    uses the `message` field. This processor moves the value from one field to
    the other.
    See https://github.com/hynek/structlog/issues/35#issuecomment-591321744
    """
    event_dict["message"] = event_dict.pop("event")
    return event_dict


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def init_logger(log_level: str, enable_json_logs: bool = False):
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        drop_color_message_key,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        # structlog.processors.CallsiteParameterAdder(
        #     {
        #         structlog.processors.CallsiteParameter.PATHNAME,
        #         structlog.processors.CallsiteParameter.FILENAME,
        #         structlog.processors.CallsiteParameter.MODULE,
        #         structlog.processors.CallsiteParameter.FUNC_NAME,
        #         structlog.processors.CallsiteParameter.THREAD,
        #         structlog.processors.CallsiteParameter.THREAD_NAME,
        #         structlog.processors.CallsiteParameter.PROCESS,
        #         structlog.processors.CallsiteParameter.PROCESS_NAME,
        #     }
        # ),
    ]
    if enable_json_logs:
        # We rename the `event` key to `message` only in JSON logs, as Datadog looks for the
        # `message` key but the pretty ConsoleRenderer looks for `event`
        shared_processors.append(rename_event_key)
        # Format the exception only for JSON logs, as we want to pretty-print them when
        # using the ConsoleRenderer
        shared_processors.append(structlog.processors.format_exc_info)



    structlog.configure(
        processors=shared_processors
        + [
            # Prepare event dict for `ProcessorFormatter`.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        # call log with await syntax in thread pool executor
        wrapper_class=structlog.stdlib.AsyncBoundLogger,
        cache_logger_on_first_use=True,
    )

    log_renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if enable_json_logs
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            log_renderer,
        ],
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    for _log in ["uvicorn", "uvicorn.error"]:
        # Clear the log handlers for uvicorn loggers, and enable propagation
        # so the messages are caught by our root logger and formatted correctly
        # by structlog
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True

    # Since we re-create the access logs ourselves, to add all information
    # in the structured log (see the `logging_middleware` in main.py), we clear
    # the handlers and prevent the logs to propagate to a logger higher up in the
    # hierarchy (effectively rendering them silent).
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False    

    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Log any uncaught exception instead of letting it be printed by Python
        (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
        See https://stackoverflow.com/a/16993115/3641865
        """
        

        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return


        root_logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )
    # set handle exception
    sys.excepthook = handle_exception


def get_logger(name):
    return structlog.stdlib.get_logger(name)