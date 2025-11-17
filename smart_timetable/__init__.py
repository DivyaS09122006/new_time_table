"""Smart Timetable Planner package."""

from .models import Course, TimetableSummary
from .parser import read_courses_from_csv
from .builder import TimetableBuilder

__all__ = [
    "Course",
    "TimetableSummary",
    "read_courses_from_csv",
    "TimetableBuilder",
]
