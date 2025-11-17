from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .exceptions import ValidationError
from .models import BranchTimetable, Course, TimetableSummary, YearElectiveOptions


@dataclass
class StudentElectiveSelection:
    year: str
    branch: str
    # mapping slot -> course code
    selections: Dict[str, str]


class TimetableBuilder:
    """Builds validated timetable structures from parsed courses."""

    def __init__(self, courses: Iterable[Course]):
        self.courses = list(courses)

    def build(self) -> TimetableSummary:
        branch_tables: Dict[Tuple[str, str], BranchTimetable] = {}
        year_electives: Dict[str, YearElectiveOptions] = {}

        faculty_slots: Dict[Tuple[str, str], List[Course]] = defaultdict(list)
        room_slots: Dict[Tuple[str, str], List[Course]] = defaultdict(list)
        lab_slots: Dict[Tuple[str, str], List[Course]] = defaultdict(list)

        for course in self.courses:
            slot = course.slot
            faculty_slots[(course.faculty.lower(), slot)].append(course)
            if course.room:
                room_slots[(course.room.lower(), slot)].append(course)
            if course.lab_room:
                lab_slots[(course.lab_room.lower(), slot)].append(course)

            if course.is_elective:
                year_bundle = year_electives.setdefault(
                    course.year, YearElectiveOptions(year=course.year)
                )
                year_bundle.slot_electives.setdefault(slot, []).append(course)
            else:
                for branch in course.branches:
                    key = (course.year, branch)
                    branch_table = branch_tables.setdefault(
                        key, BranchTimetable(year=course.year, branch=branch)
                    )
                    if slot in branch_table.core_slots:
                        existing = branch_table.core_slots[slot]
                        raise ValidationError(
                            "Slot conflict: year %(year)s branch %(branch)s already has core %(existing)s "
                            "in slot %(slot)s, cannot add %(incoming)s" % {
                                "year": course.year,
                                "branch": branch,
                                "existing": existing.course_code,
                                "slot": slot,
                                "incoming": course.course_code,
                            }
                        )
                    branch_table.core_slots[slot] = course

        self._detect_resource_conflicts(faculty_slots, "faculty")
        self._detect_resource_conflicts(room_slots, "room")
        self._detect_resource_conflicts(lab_slots, "lab room")

        return TimetableSummary(branch_timetables=branch_tables, year_electives=year_electives)

    def _detect_resource_conflicts(
        self,
        assignments: Dict[Tuple[str, str], List[Course]],
        resource_name: str,
    ) -> None:
        for (resource, slot), courses in assignments.items():
            if len(courses) > 1:
                codes = ", ".join(sorted(course.course_code for course in courses))
                raise ValidationError(
                    f"{resource_name.title()} conflict in slot {slot} for {resource}: {codes}"
                )

    def build_student_schedule(
        self,
        summary: TimetableSummary,
        selection: StudentElectiveSelection,
    ) -> Dict[str, Course]:
        """Generate a per-student schedule by merging cores and selected electives."""
        key = (selection.year, selection.branch)
        if key not in summary.branch_timetables:
            raise ValidationError(
                f"No core timetable available for year {selection.year} branch {selection.branch}"
            )

        result = dict(summary.branch_timetables[key].core_slots)
        electives = summary.year_electives.get(selection.year, YearElectiveOptions(selection.year))

        for slot, course_code in selection.selections.items():
            slot_upper = slot.upper().replace(" ", "")
            options = electives.slot_electives.get(slot_upper)
            if not options:
                raise ValidationError(
                    f"Slot {slot} has no elective offerings for year {selection.year}"
                )
            matching = next((c for c in options if c.course_code == course_code), None)
            if not matching:
                raise ValidationError(
                    f"Course {course_code} is not an elective option in slot {slot} for year {selection.year}"
                )
            if slot_upper in result:
                raise ValidationError(
                    f"Cannot assign elective {course_code} to slot {slot}: core course already scheduled"
                )
            result[slot_upper] = matching
        return result
