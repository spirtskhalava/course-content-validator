"""Course Content Validator: QA checks for Markdown lessons and YAML quizzes."""

from .config import Config
from .models import Finding, Report, Severity
from .runner import validate_course

__all__ = ["Config", "Finding", "Report", "Severity", "validate_course"]
__version__ = "0.1.0"
