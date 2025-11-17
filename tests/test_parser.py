import textwrap

import pytest

from smart_timetable.exceptions import ValidationError
from smart_timetable.parser import read_courses_from_csv


def write_csv(tmp_path, content: str):
    csv_content = textwrap.dedent(content).strip() + "\n"
    file_path = tmp_path / "courses.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    return file_path


def test_parser_reads_courses(tmp_path):
    path = write_csv(
        tmp_path,
        """
        YEAR,BRANCH,COURSE CODE,ELECTIVE OR NOT,COURSE,FACULTY,CLASS AST,LAB AST,L-T-P-S-C,ROOM.NO,LAB ROOM,MERGE,SLOT
        2,CSE,CS201,CORE,Data Structures,Prof A,CA1,,3-1-0-0-4,A101,,,A1
        2,CSE/EEE,EL201,ELECTIVE,AI Elective,Prof B,CA2,,2-1-0-0-3,,LAB-1,,B1
        """,
    )
    courses = read_courses_from_csv(path)
    assert len(courses) == 2
    core = next(course for course in courses if not course.is_elective)
    assert core.slot == "A1"
    elective = next(course for course in courses if course.is_elective)
    assert elective.branches == ("CSE", "EEE")
    assert elective.ltpsc == (2, 1, 0, 0, 3)


def test_parser_rejects_bad_ltpsc(tmp_path):
    path = write_csv(
        tmp_path,
        """
        YEAR,BRANCH,COURSE CODE,ELECTIVE OR NOT,COURSE,FACULTY,CLASS AST,LAB AST,L-T-P-S-C,ROOM.NO,LAB ROOM,MERGE,SLOT
        2,CSE,CS201,CORE,Data Structures,Prof A,CA1,,invalid,A101,,,
        """,
    )
    with pytest.raises(ValidationError):
        read_courses_from_csv(path)
