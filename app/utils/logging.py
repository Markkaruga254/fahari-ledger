"""Shared logging configuration.

Every module that talks to an external service (Africa's Talking, an ASR
provider) logs through the standard `logging` module under the `fahari.*`
namespace instead of using `print`, so operators can see delivery/transcription
failures in whatever log aggregation the deployment uses, at the right level
(warning for a retried transient failure, error once retries are exhausted).
"""
import logging
import os


def setup_logging() -> None:
    """Idempotent: safe to call once at app startup and again in scripts."""
    root = logging.getLogger()
    if root.handlers:
        return

    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
