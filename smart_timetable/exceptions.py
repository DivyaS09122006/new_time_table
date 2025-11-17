class TimetableError(Exception):
    """Base error class for timetable planner issues."""


class ValidationError(TimetableError):
    """Raised when the input data violates required constraints."""


class ParsingError(TimetableError):
    """Raised when the CSV cannot be parsed successfully."""
