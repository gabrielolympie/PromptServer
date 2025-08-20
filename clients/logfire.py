import logfire
import logging
import os

if "LOGFIRE_TOKEN" in os.environ:
    logfire.configure()


def app_log(
    level: str,
    message: str,
    attributes: dict = None,
    tags: list = None,
):
    ## If logfire is setup, use logfire
    if "LOGFIRE_TOKEN" in os.environ:
        logfire.log(
            level=level,
            msg_template=message,
            attributes=attributes,
            tags=tags,
        )

    ## Else, use simple logging
    if os.environ["LOCAL_LOGGING"] == "True" or "LOGFIRE_TOKEN" not in os.environ:
        logging.basicConfig(level=logging.INFO)
        logging.log(
            level=logging.INFO,
            msg=message,
            extra=attributes,
        )
