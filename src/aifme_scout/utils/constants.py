"""Constants used across the Scout codebase."""

from enum import StrEnum


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ScanMode(StrEnum):
    NO_LLM = "no-llm"
    LLM = "llm"


DEFAULT_LOG_LEVEL = "WARNING"
DEFAULT_CRAWL_DELAY_MS = 1000
DEFAULT_MAX_PAGES = 25
CONFIG_FILE_NAME = "scout.config.yaml"
ENV_PREFIX = "SCOUT_"
