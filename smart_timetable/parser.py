from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .exceptions import ParsingError, ValidationError
from .models import Course, LTPSC

REQUIRED_HEADERS = [
    "YEAR",
    "BRANCH",
    "COURSE CODE",
    "ELECTIVE OR NOT",
    "COURSE",
    "FACULTY",
    "CLASS AST",
    "LAB AST",
    "L-T-P-S-C",
    "ROOM.NO",
    "LAB ROOM",
    "MERGE",
    "SLOT",
]

HEADER_KEY_PATTERN = re.compile(r"[^A-Z0-9]+")
LTPSC_PATTERN = re.compile(r"^(\d+)-(\d+)-(\d+)-(\d+)-(\d+)$")
ELECTIVE_TRUE = {"ELECTIVE", "E", "YES", "Y", "TRUE", "1"}
ELECTIVE_FALSE = {"CORE", "C", "NO", "N", "FALSE", "0"}
BRANCH_SPLIT_PATTERN = re.compile(r"[,/&+|]")


def normalize_header_key(value: str) -> str:
    return HEADER_KEY_PATTERN.sub("", value.strip().upper())


def _build_header_map(headers: Iterable[str]) -> Dict[str, str]:
    header_map: Dict[str, str] = {}
    for header in headers:
        key = normalize_header_key(header)
        if key and key not in header_map:
            header_map[key] = header
    missing = [req for req in REQUIRED_HEADERS if normalize_header_key(req) not in header_map]
    if missing:
        raise ValidationError(
            f"Missing required columns: {', '.join(missing)}"
        )
    return header_map


def parse_ltpsc(value: str, row_num: int) -> LTPSC:
    cleaned = value.strip()
    match = LTPSC_PATTERN.match(cleaned)
    if not match:
        raise ValidationError(f"Row {row_num}: L-T-P-S-C must contain five integers (got '{value}')")
    return tuple(int(group) for group in match.groups())  # type: ignore[return-value]


def parse_elective_flag(value: str, row_num: int) -> bool:
    cleaned = value.strip().upper()
    if cleaned in ELECTIVE_TRUE:
        return True
    if cleaned in ELECTIVE_FALSE:
        return False
    raise ValidationError(
        f"Row {row_num}: ELECTIVE OR NOT must clearly indicate elective/core (got '{value}')"
    )


def parse_branch_list(raw: str, row_num: int) -> Tuple[str, ...]:
    if not raw.strip():
        raise ValidationError(f"Row {row_num}: BRANCH cannot be empty")
    candidates = BRANCH_SPLIT_PATTERN.split(raw.upper()) if BRANCH_SPLIT_PATTERN.search(raw) else [raw.upper()]
    seen = []
    for entry in candidates:
        token = entry.strip()
        if not token:
            continue
        if token == "ALL":
            return ("ALL",)
        if token not in seen:
            seen.append(token)
    if not seen:
        raise ValidationError(f"Row {row_num}: BRANCH could not be parsed (value='{raw}')")
    return tuple(seen)


def resolve_slot(row: Dict[str, str], header_map: Dict[str, str], row_num: int) -> Tuple[str, str | None]:
    merge_value = row.get(header_map[normalize_header_key("MERGE")], "").strip()
    slot_value = row.get(header_map[normalize_header_key("SLOT")], "").strip()
    chosen = merge_value or slot_value
    if not chosen:
        raise ValidationError(f"Row {row_num}: Either MERGE or SLOT column must provide a slot label")
    normalized = chosen.upper().replace(" ", "")
    merged_label = merge_value.upper().replace(" ", "") if merge_value else None
    return normalized, merged_label


def read_courses_from_csv(path: str | Path) -> List[Course]:
    file_path = Path(path)
    if not file_path.exists():
        raise ParsingError(f"Input CSV not found: {file_path}")
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ParsingError("CSV appears to have no header row")
        header_map = _build_header_map(reader.fieldnames)
        courses: List[Course] = []
        for idx, row in enumerate(reader, start=2):  # account for header row
            ltpsc = parse_ltpsc(row.get(header_map[normalize_header_key("L-T-P-S-C")], ""), idx)
            is_elective = parse_elective_flag(row.get(header_map[normalize_header_key("ELECTIVE OR NOT")], ""), idx)
            branches = parse_branch_list(row.get(header_map[normalize_header_key("BRANCH")], ""), idx)
            slot, merged = resolve_slot(row, header_map, idx)
            year_value = row.get(header_map[normalize_header_key("YEAR")], "").strip()
            if not year_value:
                raise ValidationError(f"Row {idx}: YEAR cannot be empty")
            course_code = row.get(header_map[normalize_header_key("COURSE CODE")], "").strip()
            if not course_code:
                raise ValidationError(f"Row {idx}: COURSE CODE cannot be empty")
            course_title = row.get(header_map[normalize_header_key("COURSE")], "").strip()
            if not course_title:
                raise ValidationError(f"Row {idx}: COURSE title cannot be empty")
            faculty = row.get(header_map[normalize_header_key("FACULTY")], "").strip()
            if not faculty:
                raise ValidationError(f"Row {idx}: FACULTY cannot be empty")
            class_ast = row.get(header_map[normalize_header_key("CLASS AST")], "").strip() or None
            lab_ast = row.get(header_map[normalize_header_key("LAB AST")], "").strip() or None
            room = row.get(header_map[normalize_header_key("ROOM.NO")], "").strip() or None
            lab_room = row.get(header_map[normalize_header_key("LAB ROOM")], "").strip() or None

            courses.append(
                Course(
                    course_code=course_code,
                    course_title=course_title,
                    ltpsc=ltpsc,
                    slot=slot,
                    year=year_value.strip(),
                    branches=branches,
                    is_elective=is_elective,
                    faculty=faculty,
                    class_assistant=class_ast,
                    lab_assistant=lab_ast,
                    room=room,
                    lab_room=lab_room,
                    merged_slot_label=merged,
                    raw={key: value for key, value in row.items()},
                )
            )
    if not courses:
        raise ValidationError("CSV does not contain any course rows")
    return courses
