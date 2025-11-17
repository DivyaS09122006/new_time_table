# Smart Timetable Planner

Generate conflict-free course timetables from a CSV catalog that lists core and elective offerings across branches and academic years.

## Features
- Validates CSV headers and row-level constraints (slot labels, L-T-P-S-C pattern, elective flag clarity, year/branch presence).
- Normalizes merged slots automatically and enforces that core courses never overlap within the same branch-year combination.
- Detects slot conflicts across resources (faculty, classrooms, lab rooms) so instructors and rooms are never double-booked.
- Aggregates elective offerings per year/slot, ensuring each student can opt into at most one elective per slot.
- Provides an optional per-student merge that overlays core courses with chosen electives.

## CSV Schema
The input file must include these headers (case/spacing is validated):

`YEAR`, `BRANCH`, `COURSE CODE`, `ELECTIVE OR NOT`, `COURSE`, `FACULTY`, `CLASS AST`, `LAB AST`, `L-T-P-S-C`, `ROOM.NO`, `LAB ROOM`, `MERGE`, `SLOT`

Rules enforced:
- `L-T-P-S-C` must contain exactly five integers separated by hyphens.
- Either `MERGE` or `SLOT` must be populated; `MERGE` takes precedence to represent combined slots like `A1+B1`.
- `ELECTIVE OR NOT` must clearly specify elective/core (accepted values: `ELECTIVE`, `CORE`, `YES/NO`, `TRUE/FALSE`, etc.).
- Year, branch, course code, title, and faculty values cannot be blank.
- Branch values can be delimited with `/ , + & |` to target multiple branches. Use `ALL` to indicate a global branch bucket.

## Usage
Install dependencies (standard library only) and run the CLI:

```bash
python3 -m smart_timetable.cli path/to/courses.csv
```

Options:
- `--format {text,json}`: choose human-readable text (default) or JSON output.
- `--output FILE`: write the result to a file instead of stdout.
- `--student-year YEAR` and `--student-branch BRANCH`: produce a personalized schedule for a specific student.
- `--elective SLOT=COURSE`: specify elective picks per slot (repeatable). Example: `--elective B1=EL201 --elective C1=EL205`.

Example command:

```bash
python3 -m smart_timetable.cli data/catalog.csv --format json --output timetable.json \
  --student-year 2 --student-branch CSE --elective B1=EL201
```

## Tests
Run the automated suite (requires `pytest`, already declared in `pyproject.toml`):

```bash
python3 -m pytest
```

## Extending
The package exposes `read_courses_from_csv`, `TimetableBuilder`, and `TimetableSummary` for programmatic use. See `smart_timetable/cli.py` for an end-to-end reference workflow.
