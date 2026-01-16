"""ContentLint - ESLint for writing."""

__version__ = "1.0.0"

from .engine import ContentLinter
from .rules import RuleRegistry

__all__ = ["ContentLinter", "RuleRegistry"]
