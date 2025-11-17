from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


LTPSC = Tuple[int, int, int, int, int]


@dataclass(frozen=True)
class Course:
    course_code: str
    course_title: str
    ltpsc: LTPSC
    slot: str
    year: str
    branches: Tuple[str, ...]
    is_elective: bool
    faculty: str
    class_assistant: Optional[str]
    lab_assistant: Optional[str]
    room: Optional[str]
    lab_room: Optional[str]
    merged_slot_label: Optional[str] = None
    raw: Dict[str, str] = field(default_factory=dict)

    @property
    def credits(self) -> int:
        """Return credit count derived from the L-T-P-S-C tuple."""
        return self.ltpsc[-1]


@dataclass
class BranchTimetable:
    year: str
    branch: str
    core_slots: Dict[str, Course] = field(default_factory=dict)


@dataclass
class YearElectiveOptions:
    year: str
    slot_electives: Dict[str, List[Course]] = field(default_factory=dict)


@dataclass
class TimetableSummary:
    branch_timetables: Dict[Tuple[str, str], BranchTimetable] = field(default_factory=dict)
    year_electives: Dict[str, YearElectiveOptions] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Dict]:
        branches = {}
        for (year, branch), table in sorted(self.branch_timetables.items()):
            branches.setdefault(year, {})[branch] = {
                slot: course.course_code for slot, course in sorted(table.core_slots.items())
            }

        electives = {}
        for year, opts in sorted(self.year_electives.items()):
            electives[year] = {
                slot: [course.course_code for course in courses]
                for slot, courses in sorted(opts.slot_electives.items())
            }

        return {"core": branches, "electives": electives}
