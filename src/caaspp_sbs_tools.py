from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

CANONICAL_RENAMES = {
    "Subgroup ID": "Student Group ID",
    "Test Id": "Test ID",
    "Total Students Tested": "Students Tested",
    "Total Tested at Subgroup Level": "Students Tested",
    "Total Tested At Subgroup Level": "Students Tested",
    "Total Tested at Reporting Level": "Total Tested at Reporting Level",
    "Total Students Enrolled": "Total Students Enrolled",
    "Students Enrolled": "Total Students Enrolled",
    "CAASPP Reported Enrollment": "Total Students Enrolled",
}

REQUIRED_COLUMNS = [
    "County Code",
    "District Code",
    "School Code",
    "Student Group ID",
    "Grade",
    "Test ID",
    "Percentage Standard Met and Above",
]

DEFAULT_STUDENT_GROUPS = {"031": "SED", "111": "NSED"}
DEFAULT_TESTS = {"01": "ELA", "02": "MATH"}
DEFAULT_GRADES = ["03", "04", "05", "06", "08", "11"]


def extract_zip_if_needed(path: Path, work_dir: Path) -> List[Path]:
    """Return one or more .csv/.txt files. Extract ZIPs into work_dir."""
    path = Path(path)
    if path.suffix.lower() != ".zip":
        return [path]

    extract_dir = Path(work_dir) / path.stem
    extract_dir.mkdir(parents=True, exist_ok=True)
    found: List[Path] = []
    with zipfile.ZipFile(path, "r") as z:
        members = [
            m for m in z.namelist()
            if m.lower().endswith((".txt", ".csv"))
            and not m.startswith("__MACOSX")
            and not Path(m).name.startswith("._")
        ]
        if not members:
            raise ValueError(f"No .txt or .csv data file found inside {path.name}")
        for member in members:
            z.extract(member, extract_dir)
            found.append(extract_dir / member)
    return found


def collect_input_files(raw_dir: Path, work_dir: Path) -> List[Path]:
    """Collect ZIP/TXT/CSV files from raw_dir, extracting ZIPs as needed."""
    raw_dir = Path(raw_dir)
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    candidates = sorted(
        p for p in raw_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".zip", ".txt", ".csv"}
    )
    if not candidates:
        raise FileNotFoundError(
            f"No .zip, .txt, or .csv files found in {raw_dir}. "
            "Put CAASPP research files there, or upload them in Colab."
        )

    files: List[Path] = []
    for p in candidates:
        files.extend(extract_zip_if_needed(p, work_dir))
    return sorted(set(files))


def detect_delimiter(path: Path) -> Optional[str]:
    """Return '^', ',', or None for likely fixed-width ASCII."""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        first_line = f.readline()
    if "^" in first_line:
        return "^"
    if "," in first_line:
        return ","
    return None


def _slice(line: str, start: int, end: int) -> str:
    """1-indexed inclusive fixed-width slice."""
    return line[start - 1:end].strip()


def _fixed_width_layout_for_first_line(line: str) -> str:
    """
    Choose one of the public CAASPP SB research-file fixed-width layouts.

    The notebook only needs a subset of columns, so we parse the shared keys and
    the percent-met/exceeded field rather than every area/composite field.
    """
    # 2023-24+ districtwide/countywide fixed-width layout has district/school names;
    # Test Year is at positions 121-124 and Type ID at 115-116.
    if len(line) >= 201 and _slice(line, 121, 124).isdigit():
        return "2024_plus_named"

    # 2014-15 had a special layout: Grade at 49-50, Test ID at 51-52, percent at 84-86.
    if len(line) >= 86 and _slice(line, 19, 22) == "2015":
        return "2015_special"

    # 2015-16 through 2022-23 fixed-width layout: Grade at 41-42, Test ID at 43-44,
    # percent met/exceeded at 77-82, optional Type ID at 174-175 for newer years.
    if len(line) >= 82 and _slice(line, 19, 22).isdigit():
        return "2016_2023_standard"

    raise ValueError(
        "Could not identify this fixed-width CAASPP layout. "
        "If possible, download the caret-delimited or comma-delimited CAASPP file instead."
    )


def read_fixed_width_caaspp(path: Path) -> pd.DataFrame:
    """Read CAASPP fixed-width ASCII research file into canonical-ish columns."""
    path = Path(path)
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        lines = [line.rstrip("\n\r") for line in f if line.strip()]
    if not lines:
        raise ValueError(f"Empty file: {path}")

    layout = _fixed_width_layout_for_first_line(lines[0])
    records = []
    for line in lines:
        if layout == "2024_plus_named":
            record = {
                "County Code": _slice(line, 1, 2),
                "District Code": _slice(line, 3, 7),
                "District Name": _slice(line, 8, 47),
                "School Code": _slice(line, 48, 54),
                "School Name": _slice(line, 55, 114),
                "Type ID": _slice(line, 115, 116),
                "Test Year": _slice(line, 121, 124),
                "Test ID": _slice(line, 126, 127),
                "Student Group ID": _slice(line, 128, 130),
                "Grade": _slice(line, 131, 132),
                "Total Students Enrolled": _slice(line, 133, 141),
                "Students Tested": _slice(line, 142, 150),
                "Percentage Standard Met and Above": _slice(line, 196, 201),
            }
        elif layout == "2016_2023_standard":
            record = {
                "County Code": _slice(line, 1, 2),
                "District Code": _slice(line, 3, 7),
                "School Code": _slice(line, 8, 14),
                "Test Year": _slice(line, 19, 22),
                "Student Group ID": _slice(line, 23, 25),
                "Grade": _slice(line, 41, 42),
                "Test ID": _slice(line, 43, 44),
                "Total Students Enrolled": _slice(line, 45, 51),
                "Students Tested": _slice(line, 52, 58),
                "Percentage Standard Met and Above": _slice(line, 77, 82),
                "Type ID": _slice(line, 174, 175) if len(line) >= 175 else "",
            }
        elif layout == "2015_special":
            record = {
                "County Code": _slice(line, 1, 2),
                "District Code": _slice(line, 3, 7),
                "School Code": _slice(line, 8, 14),
                "Test Year": _slice(line, 19, 22),
                "Student Group ID": _slice(line, 23, 25),
                "Grade": _slice(line, 49, 50),
                "Test ID": _slice(line, 51, 52),
                "Total Students Enrolled": _slice(line, 53, 59),
                "Students Tested": _slice(line, 60, 66),
                "Percentage Standard Met and Above": _slice(line, 84, 86),
                "Type ID": "",
            }
        else:
            raise AssertionError(layout)
        records.append(record)
    df = pd.DataFrame(records)
    df["_detected_format"] = f"fixed_width:{layout}"
    return df


def read_caaspp_file(path: Path) -> pd.DataFrame:
    """Read delimited or fixed-width CAASPP SB research file."""
    path = Path(path)
    sep = detect_delimiter(path)
    if sep is not None:
        df = pd.read_csv(
            path,
            sep=sep,
            dtype=str,
            encoding="utf-8-sig",
            engine="python",
            quoting=csv.QUOTE_MINIMAL,
        )
        df["_detected_format"] = "caret" if sep == "^" else "comma"
    else:
        df = read_fixed_width_caaspp(path)
    df["_source_file"] = path.name
    return normalize_caaspp_columns(df)


def normalize_caaspp_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace("\ufeff", "") for c in df.columns]
    df = df.rename(columns={k: v for k, v in CANONICAL_RENAMES.items() if k in df.columns})
    # Some older files contain repeated filler columns. Drop duplicate column names,
    # keeping the first occurrence. Required analytical columns are not duplicated.
    df = df.loc[:, ~pd.Index(df.columns).duplicated()].copy()
    for col in list(df.columns):
        df[col] = df[col].astype(str).str.strip()
    return normalize_codes(df)


def normalize_codes(df: pd.DataFrame) -> pd.DataFrame:
    widths = {
        "County Code": 2,
        "District Code": 5,
        "School Code": 7,
        "Student Group ID": 3,
        "Grade": 2,
        "Test ID": 2,
        "Type ID": 2,
    }
    for col, width in widths.items():
        if col in df.columns:
            # Do not zero-fill blanks or nan strings.
            s = df[col].replace({"nan": "", "None": "", "*": ""})
            df[col] = s.apply(lambda x: str(x).zfill(width) if str(x).strip() != "" else "")
    return df


def require_columns(df: pd.DataFrame, source_name: str, required: Iterable[str] = REQUIRED_COLUMNS) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        preview_cols = list(df.columns)
        raise ValueError(
            f"Missing required columns in {source_name}: {missing}\n"
            f"Columns found: {preview_cols}\n"
            "This usually means the wrong CAASPP file type was selected, "
            "or a fixed-width layout changed. Try the caret/comma-delimited file if available."
        )


def clean_number(value):
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().replace(",", "")
    if text in {"", "*", "nan", "None"}:
        return pd.NA
    return pd.to_numeric(text, errors="coerce")


def process_caaspp_files(
    input_files: Iterable[Path],
    county_code: str,
    district_code: str,
    district_name: str = "district",
    grades: List[str] = DEFAULT_GRADES,
    student_groups: Dict[str, str] = DEFAULT_STUDENT_GROUPS,
    tests: Dict[str, str] = DEFAULT_TESTS,
    year_order: Optional[List[str]] = None,
    districtwide_school_code: str = "0000000",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (wide, audit_long, gap_long, avg_gap_by_grade, band_gap_by_year)."""
    county_code = str(county_code).zfill(2)
    district_code = str(district_code).zfill(5)
    districtwide_school_code = str(districtwide_school_code).zfill(7)
    grades = [str(g).zfill(2) for g in grades]
    student_groups = {str(k).zfill(3): v for k, v in student_groups.items()}
    tests = {str(k).zfill(2): v for k, v in tests.items()}

    frames = []
    errors = []
    for path in input_files:
        try:
            df = read_caaspp_file(Path(path))
            require_columns(df, Path(path).name)
            frames.append(df)
        except Exception as e:
            errors.append((str(path), str(e)))

    if not frames:
        msg = "No CAASPP files could be read."
        if errors:
            msg += "\n\nErrors:\n" + "\n\n".join(f"{p}: {err}" for p, err in errors)
        raise ValueError(msg)

    raw = pd.concat(frames, ignore_index=True)

    sub = raw[
        (raw["County Code"] == county_code)
        & (raw["District Code"] == district_code)
        & (raw["School Code"] == districtwide_school_code)
        & (raw["Student Group ID"].isin(student_groups.keys()))
        & (raw["Grade"].isin(grades))
        & (raw["Test ID"].isin(tests.keys()))
    ].copy()

    if "Type ID" in sub.columns:
        # Older files may have missing/blank Type ID; newer district rows should be 06.
        type_id_clean = sub["Type ID"].astype(str).str.strip().replace({"nan": "", "None": ""})
        sub = sub[(type_id_clean.isin(["", "06"]))]

    if sub.empty:
        raise ValueError(
            f"No matching districtwide SED/NSED rows found for county={county_code}, "
            f"district={district_code}. Check that you downloaded All Student Groups, "
            f"not All Students only, and that codes are correct."
        )

    # Build audit/long table.
    rows = []
    for _, r in sub.iterrows():
        grade_label = str(int(r["Grade"]))
        group_label = student_groups[r["Student Group ID"]]
        subject_label = tests[r["Test ID"]]
        school_year = test_year_to_school_year(r.get("Test Year", ""))
        rows.append({
            "School Year": school_year,
            "Test Year": r.get("Test Year", ""),
            "Metric": f"{grade_label} - {group_label} {subject_label}",
            "Grade": int(r["Grade"]),
            "Student Group": group_label,
            "Student Group ID": r["Student Group ID"],
            "Subject": subject_label,
            "Test ID": r["Test ID"],
            "Percentage Standard Met and Above": clean_number(r["Percentage Standard Met and Above"]),
            "Students Tested": clean_number(r["Students Tested"]) if "Students Tested" in r.index else pd.NA,
            "County Code": r["County Code"],
            "District Code": r["District Code"],
            "School Code": r["School Code"],
            "Type ID": r.get("Type ID", ""),
            "Source File": r.get("_source_file", ""),
            "Detected Format": r.get("_detected_format", ""),
        })
    audit_long = pd.DataFrame(rows)
    audit_long["Percentage Standard Met and Above"] = pd.to_numeric(audit_long["Percentage Standard Met and Above"], errors="coerce")
    audit_long["Students Tested"] = pd.to_numeric(audit_long["Students Tested"], errors="coerce")

    # Deduplicate if user accidentally included the same year file twice.
    key_cols = ["School Year", "Grade", "Student Group ID", "Subject"]
    dup_mask = audit_long.duplicated(key_cols, keep=False)
    if dup_mask.any():
        # Keep the first, but leave an explanatory warning in a column.
        audit_long["Duplicate Warning"] = ""
        audit_long.loc[dup_mask, "Duplicate Warning"] = "Duplicate year/grade/group/subject row found; first value used in wide outputs."
    else:
        audit_long["Duplicate Warning"] = ""

    audit_dedup = audit_long.drop_duplicates(key_cols, keep="first")

    if year_order is None:
        year_order = sorted(audit_dedup["School Year"].unique(), reverse=True)

    desired_columns = []
    for grade in [str(int(g)) for g in grades]:
        for group_label in student_groups.values():
            for subject_label in tests.values():
                desired_columns.append(f"{grade} - {group_label} {subject_label}")

    wide = (
        audit_dedup.pivot_table(
            index="School Year",
            columns="Metric",
            values="Percentage Standard Met and Above",
            aggfunc="first",
        )
        .reindex(index=year_order, columns=desired_columns)
        .reset_index()
    )

    # Gap table: one row per year/grade/subject.
    piv = audit_dedup.pivot_table(
        index=["School Year", "Grade", "Subject"],
        columns="Student Group",
        values=["Percentage Standard Met and Above", "Students Tested"],
        aggfunc="first",
    )
    # Flatten safely.
    gap_records = []
    for idx, row in piv.iterrows():
        school_year, grade, subject = idx
        sed_pct = row.get(("Percentage Standard Met and Above", "SED"), pd.NA)
        nsed_pct = row.get(("Percentage Standard Met and Above", "NSED"), pd.NA)
        sed_n = row.get(("Students Tested", "SED"), pd.NA)
        nsed_n = row.get(("Students Tested", "NSED"), pd.NA)
        gap_records.append({
            "School Year": school_year,
            "Grade": int(grade),
            "Subject": subject,
            "SED % Met/Exceeded": sed_pct,
            "NSED % Met/Exceeded": nsed_pct,
            "Gap: NSED minus SED": nsed_pct - sed_pct if pd.notna(nsed_pct) and pd.notna(sed_pct) else pd.NA,
            "SED Students Tested": sed_n,
            "NSED Students Tested": nsed_n,
        })
    gap_long = pd.DataFrame(gap_records)
    gap_long["Grade Band"] = gap_long["Grade"].apply(lambda g: "Lower grades (3-5)" if g in [3, 4, 5] else "Upper grades (6, 8, 11)")
    gap_long["Subject"] = pd.Categorical(gap_long["Subject"], categories=list(tests.values()), ordered=True)
    gap_long["School Year"] = pd.Categorical(gap_long["School Year"], categories=year_order, ordered=True)
    gap_long = gap_long.sort_values(["School Year", "Grade", "Subject"]).reset_index(drop=True)

    avg_gap_by_grade = (
        gap_long.groupby(["Grade", "Subject"], observed=False)["Gap: NSED minus SED"]
        .mean()
        .unstack("Subject")
        .reset_index()
    )
    if set(tests.values()).issubset(avg_gap_by_grade.columns):
        avg_gap_by_grade["Combined Average Gap"] = avg_gap_by_grade[list(tests.values())].mean(axis=1)

    band_gap_by_year = (
        gap_long.groupby(["School Year", "Grade Band"], observed=False)["Gap: NSED minus SED"]
        .mean()
        .unstack("Grade Band")
        .reset_index()
    )
    if {"Lower grades (3-5)", "Upper grades (6, 8, 11)"}.issubset(band_gap_by_year.columns):
        band_gap_by_year["Upper minus lower"] = band_gap_by_year["Upper grades (6, 8, 11)"] - band_gap_by_year["Lower grades (3-5)"]

    # Convert categorical years back to strings for export.
    for df in [gap_long, band_gap_by_year]:
        if "School Year" in df.columns:
            df["School Year"] = df["School Year"].astype(str)

    return wide, audit_long, gap_long, avg_gap_by_grade, band_gap_by_year


def test_year_to_school_year(value: str) -> str:
    text = str(value).strip()
    if not text or text == "nan":
        return "Unknown"
    year = int(float(text))
    return f"{str(year - 1)[-2:]}-{str(year)[-2:]}"


def export_outputs(
    output_dir: Path,
    district_slug: str,
    wide: pd.DataFrame,
    audit_long: pd.DataFrame,
    gap_long: pd.DataFrame,
    avg_gap_by_grade: pd.DataFrame,
    band_gap_by_year: pd.DataFrame,
) -> Dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    district_slug = district_slug.lower().replace(" ", "_").replace("/", "_")
    paths = {
        "wide_csv": output_dir / f"{district_slug}_caaspp_wide.csv",
        "audit_csv": output_dir / f"{district_slug}_caaspp_audit_long.csv",
        "gap_csv": output_dir / f"{district_slug}_caaspp_gap_chart_data.csv",
        "summary_xlsx": output_dir / f"{district_slug}_caaspp_chart_ready_outputs.xlsx",
    }
    wide.to_csv(paths["wide_csv"], index=False)
    audit_long.to_csv(paths["audit_csv"], index=False)
    gap_long.to_csv(paths["gap_csv"], index=False)
    with pd.ExcelWriter(paths["summary_xlsx"], engine="openpyxl") as writer:
        wide.to_excel(writer, sheet_name="Wide Time Series", index=False)
        audit_long.to_excel(writer, sheet_name="Audit Long", index=False)
        gap_long.to_excel(writer, sheet_name="Gap Chart Data", index=False)
        avg_gap_by_grade.to_excel(writer, sheet_name="Avg Gap by Grade", index=False)
        band_gap_by_year.to_excel(writer, sheet_name="Band Gap by Year", index=False)
    return paths


def print_sanity_checks(audit_long: pd.DataFrame, grades: List[str] = DEFAULT_GRADES) -> None:
    print("Rows pulled:", len(audit_long))
    print("Years:", ", ".join(map(str, sorted(audit_long["School Year"].unique(), reverse=True))))
    print("Student groups:", sorted(audit_long["Student Group ID"].unique()))
    print("Grades:", sorted(audit_long["Grade"].unique()))
    print("Subjects:", sorted(audit_long["Subject"].unique()))
    if "Students Tested" in audit_long.columns:
        print("Smallest test subgroup:", int(audit_long["Students Tested"].min()))
        display_cols = ["School Year", "Metric", "Students Tested", "Percentage Standard Met and Above", "Source File"]
        print("\nFive smallest subgroups:")
        print(audit_long.sort_values("Students Tested")[display_cols].head(5).to_string(index=False))
    expected_per_year = len(grades) * 2 * 2
    counts = audit_long.groupby("School Year").size().sort_index()
    bad = counts[counts != expected_per_year]
    if not bad.empty:
        print("\nWARNING: Some years do not have the expected number of rows.")
        print(counts.to_string())
