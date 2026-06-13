"""Base class for all ACC output parsers."""

from abc import ABC, abstractmethod
from acc.core.logger import log


class BaseParser(ABC):
    """
    Base class for tool-specific output parsers.
    
    Subclasses declare which commands they handle via `tool_names`,
    implement `parse()` for structured compression, and inherit
    automatic fallback-to-raw on any failure.
    """

    tool_names: list[str] = []

    def can_handle(self, command: str) -> bool:
        """Check if this parser handles the given command name."""
        cmd_lower = command.lower()
        if cmd_lower.endswith(".exe"):
            cmd_lower = cmd_lower[:-4]
        # Strip path separators (e.g. /usr/bin/gcc -> gcc)
        cmd_lower = cmd_lower.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        return cmd_lower in self.tool_names

    @abstractmethod
    def parse(self, raw_output: str, **kwargs) -> str:
        """
        Parse and compress the raw output.

        Must return a compressed string. On any internal failure,
        implementations should call self.fallback() rather than raising.
        """

    def fallback(self, raw_output: str, reason: str = "unknown") -> str:
        """Return raw output unchanged. Called on parse failure."""
        log.warning(
            "Parser fallback triggered",
            extra={
                "parser": self.__class__.__name__,
                "reason": reason,
                "raw_length": len(raw_output),
            },
        )
        return raw_output
