import textwrap

import pytest

from smart_timetable.builder import StudentElectiveSelection, TimetableBuilder
from smart_timetable.exceptions import ValidationError
from smart_timetable.parser import read_courses_from_csv


def build_courses(tmp_path, csv_body: str):
    csv_content = textwrap.dedent(csv_body).strip() + "\n"
    path = tmp_path / "courses.csv"
    path.write_text(csv_content, encoding="utf-8")
    return read_courses_from_csv(path)


def sample_csv():
    return """
    YEAR,BRANCH,COURSE CODE,ELECTIVE OR NOT,COURSE,FACULTY,CLASS AST,LAB AST,L-T-P-S-C,ROOM.NO,LAB ROOM,MERGE,SLOT
    2,CSE,CS201,CORE,Data Structures,Prof A,CA1,,3-1-0-0-4,A101,,,A1
    2,EEE,EE201,CORE,Circuits,Prof C,CA2,,3-0-2-0-4,A201,,A1+B1,
    2,CSE/EEE,EL201,ELECTIVE,AI Elective,Prof B,CA3,,2-1-0-0-3,,LAB-1,,B1
    2,CSE/EEE,EL202,ELECTIVE,Robotics,Prof D,CA4,,2-0-2-0-4,,LAB-2,,B1
    """


def test_builds_summary(tmp_path):
    courses = build_courses(tmp_path, sample_csv())
    builder = TimetableBuilder(courses)
    summary = builder.build()

    assert ("2", "CSE") in summary.branch_timetables
    assert "B1" in summary.year_electives["2"].slot_electives


def test_detects_core_slot_conflict(tmp_path):
    courses = build_courses(
        tmp_path,
        """
        YEAR,BRANCH,COURSE CODE,ELECTIVE OR NOT,COURSE,FACULTY,CLASS AST,LAB AST,L-T-P-S-C,ROOM.NO,LAB ROOM,MERGE,SLOT
        2,CSE,CS201,CORE,Data Structures,Prof A,CA1,,3-1-0-0-4,A101,,,A1
        2,CSE,CS202,CORE,Algorithms,Prof B,CA2,,3-1-0-0-4,A102,,,A1
        """,
    )
    builder = TimetableBuilder(courses)
    with pytest.raises(ValidationError):
        builder.build()


def test_detects_faculty_conflict(tmp_path):
    courses = build_courses(
        tmp_path,
        """
        YEAR,BRANCH,COURSE CODE,ELECTIVE OR NOT,COURSE,FACULTY,CLASS AST,LAB AST,L-T-P-S-C,ROOM.NO,LAB ROOM,MERGE,SLOT
        2,CSE,CS201,CORE,Data Structures,Prof A,CA1,,3-1-0-0-4,A101,,,A1
        2,EEE,EE201,CORE,Circuits,Prof A,CA2,,3-0-2-0-4,A201,,,A1
        """,
    )
    builder = TimetableBuilder(courses)
    with pytest.raises(ValidationError):
        builder.build()


def test_student_schedule(tmp_path):
    courses = build_courses(tmp_path, sample_csv())
    builder = TimetableBuilder(courses)
    summary = builder.build()
    selection = StudentElectiveSelection(
        year="2", branch="CSE", selections={"B1": "EL202"}
    )
    student_schedule = builder.build_student_schedule(summary, selection)
    assert student_schedule["B1"].course_code == "EL202"
