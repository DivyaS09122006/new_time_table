from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

from .builder import StudentElectiveSelection, TimetableBuilder
from .exceptions import TimetableError
from .models import Course, TimetableSummary
from .parser import read_courses_from_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smart Timetable Planner")
    parser.add_argument("csv", help="Path to the course catalog CSV")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        help="Path to write the generated timetable (defaults to stdout)",
    )
    parser.add_argument("--student-year", help="Student year for personal schedule")
    parser.add_argument("--student-branch", help="Student branch for personal schedule")
    parser.add_argument(
        "--elective",
        action="append",
        default=[],
        metavar="SLOT=COURSE",
        help="Elective selection in the form SLOT=COURSECODE (repeat per slot)",
    )
    return parser


def parse_elective_args(pairs: list[str]) -> Dict[str, str]:
    selections: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Elective selection must be in SLOT=COURSE format (got '{pair}')")
        slot, course_code = pair.split("=", 1)
        slot_key = slot.upper().replace(" ", "")
        if slot_key in selections:
            raise ValueError(f"Duplicate elective selection for slot {slot}")
        selections[slot_key] = course_code.strip()
    return selections


def format_text(summary: TimetableSummary, student_schedule: Dict[str, Course] | None) -> str:
    lines: list[str] = []
    years = sorted({year for year, _ in summary.branch_timetables.keys()} | set(summary.year_electives.keys()))
    for year in years:
        lines.append(f"Year {year}")
        for (yr, branch), table in sorted(summary.branch_timetables.items()):
            if yr != year:
                continue
            lines.append(f"  Branch {branch}")
            for slot, course in sorted(table.core_slots.items()):
                lines.append(
                    f"    [Core] {slot:<8} {course.course_code:<10} {course.course_title} (Faculty: {course.faculty})"
                )
        elective_block = summary.year_electives.get(year)
        if elective_block:
            lines.append("  Elective Options:")
            for slot, courses in sorted(elective_block.slot_electives.items()):
                for idx, course in enumerate(courses, start=1):
                    prefix = "*" if idx == 1 else " "
                    lines.append(
                        f"    {prefix} {slot:<8} {course.course_code:<10} {course.course_title} (Faculty: {course.faculty})"
                    )
        lines.append("")

    if student_schedule:
        lines.append("Student Schedule")
        for slot, course in sorted(student_schedule.items()):
            course_type = "Elective" if course.is_elective else "Core"
            lines.append(
                f"  [{course_type}] {slot:<8} {course.course_code:<10} {course.course_title} (Faculty: {course.faculty})"
            )

    return "\n".join(lines).strip()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        courses = read_courses_from_csv(args.csv)
        builder = TimetableBuilder(courses)
        summary = builder.build()

        student_schedule = None
        if args.student_year and args.student_branch:
            selections = parse_elective_args(args.elective)
            student_selection = StudentElectiveSelection(
                year=args.student_year.strip(),
                branch=args.student_branch.strip().upper(),
                selections=selections,
            )
            student_schedule = builder.build_student_schedule(summary, student_selection)

        if args.format == "json":
            payload = summary.as_dict()
            if student_schedule:
                payload["student_schedule"] = {
                    slot: course.course_code for slot, course in sorted(student_schedule.items())
                }
            rendered = json.dumps(payload, indent=2)
        else:
            rendered = format_text(summary, student_schedule)

        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        return 0
    except TimetableError as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")
    except ValueError as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
