import pandas as pd
from pathlib import Path
from re import match
from numpy import nan

FEATURE_GUIDES_DIR = Path(__file__).parent.parent / "data" / "feature_guides"


SPELLING_STAGES = {
    "primary": [
        ("emergent late", 5),
        ("letter name early", 10),
        ("letter name middle", 16),
        ("letter name late", 23),
        ("within pattern early", 28),
        ("within pattern middle", 35),
        ("within pattern late", 40),
        ("syllables and affixes early", 45),
        ("syllables and affixes middle", 50),
        ("syllables and affixes late", 55),
        ("derivational relations early", 60),
        ("derivational relations middle", 63),
    ],
    "elementary": [
        ("emergent late", 5),
        ("letter name early", 10),
        ("letter name middle", 16),
        ("letter name late", 23),
        ("within pattern early", 28),
        ("within pattern middle", 35),
        ("within pattern late", 40),
        ("syllables and affixes early", 45),
        ("syllables and affixes middle", 50),
        ("syllables and affixes late", 55),
        ("derivational relations early", 60),
        ("derivational relations middle", 63),
    ],
    "upper-level": [
        ("within pattern early", 3),
        ("within pattern middle", 12),
        ("within pattern late", 19),
        ("syllables and affixes early", 27),
        ("syllables and affixes middle", 36),
        ("syllables and affixes late", 46),
        ("derivational relations early", 53),
        ("derivational relations middle", 60),
        ("derivational relations late", 66),
    ],
}

VALID_LEVELS = list(SPELLING_STAGES.keys())

LEVEL_MENU = {
    "1": "primary",
    "2": "elementary",
    "3": "upper-level",
}

# Feature check definitions: (column_name, pattern_template)
# Pattern templates use %s as placeholder for the cell value.
FEATURE_CHECKS = {
    "elementary": [
        ("consonants.initial",                  "^%s"),
        ("consonants.final",                    r".*%s[aeiouy]*$"),
        ("short vowels",                        ".*%s+.*"),
        ("digraphs",                            ".*%s+.*"),
        ("blends",                              ".*%s+.*"),
        ("common long vowels",                  ".*%s+.*"),   # hyphen→dot applied separately
        ("other vowels",                        ".*%s+.*"),
        ("inflected endings",                   ".*%s$"),
        ("syllable junctures",                  ".*%s.*"),
        ("unaccented final syllables",          ".*%s$"),
        ("harder suffixes",                     ".*%s$"),
        ("bases or roots",                      ".*%s.*"),
    ],
    "upper-level": [
        ("blends and digraphs",                         ".*%s+.*"),
        ("vowels",                                      ".*%s+.*"),   # hyphen→dot applied separately
        ("complex consonants",                          ".*%s+.*"),
        ("inflected endings and syllable juncture",     ".*%s+.*"),
        ("unaccented final syllables",                  ".*%s$"),
        ("affixes",                                     ".*%s+.*"),
        ("reduced vowels in unaccented syllables",      ".*%s+.*"),
        ("greek and latin elements",                    ".*%s.*"),
        ("assimilated prefixes",                        ".*%s.*"),
    ],
}
# primary shares the same checks as elementary
FEATURE_CHECKS["primary"] = FEATURE_CHECKS["elementary"]

# Columns whose values need hyphen→dot substitution for regex (e.g. "a-e" → "a.e")
HYPHEN_DOT_COLUMNS = {"common long vowels", "vowels"}


def get_feature_guide(selection: str):
    """Load and return (level_name, feature_guide DataFrame) for the given selection.

    Accepts numeric strings ("1"/"2"/"3") or level names directly.
    Returns None on invalid input.
    """
    s = selection.strip().lower()
    if s in LEVEL_MENU:
        s = LEVEL_MENU[s]
    if s not in VALID_LEVELS:
        print("Valid options are: " + ", ".join(VALID_LEVELS))
        return None
    feature_guide = pd.read_csv(FEATURE_GUIDES_DIR / (s + ".csv"))
    feature_guide.fillna(0, inplace=True)
    feature_guide.columns = [col.lower() for col in feature_guide.columns]
    return s, feature_guide


def check_spelling_stage(level: str, feature_points: int) -> str:
    """Return the spelling stage name for the given level and feature point total."""
    stages = sorted(SPELLING_STAGES[level], key=lambda x: x[1])
    return next((stage for stage, threshold in stages if threshold > feature_points), stages[-1][0])


def _get_pattern(column: str, cell_value, template: str) -> str:
    """Build a regex pattern string from a cell value and template."""
    value = str(cell_value)
    if column in HYPHEN_DOT_COLUMNS:
        value = value.replace("-", ".")
    return template % value


def score_student(level: str, feature_guide: pd.DataFrame, test: pd.DataFrame, name: str):
    """Score a single student's spelling test.

    Returns (name, stage, answer_sheet) on success, or
    {"error": str, "student": name, "missing": [...]} on failure.
    """
    words = test[name].rename("test_words")
    word_guide = feature_guide.merge(words, on="feature", how="left")

    if word_guide["test_words"].isna().any():
        missing = list(word_guide.loc[word_guide["test_words"].isna(), "feature"])
        return {"error": "missing_features", "student": name, "missing": missing}

    answer_sheet = feature_guide.set_index("feature").map(lambda x: nan)
    feature_points = 0

    checks = FEATURE_CHECKS.get(level, [])
    for i in range(len(word_guide)):
        word = word_guide["test_words"][i]
        feature = word_guide["feature"][i]
        for column, template in checks:
            cell = word_guide[column][i]
            if cell == 0:
                continue
            pattern = _get_pattern(column, cell, template)
            if match(pattern, word):
                feature_points += 1
                answer_sheet.loc[feature, column] = 1

    # Fill remaining tested cells (non-NaN in guide, not scored 1) with 0
    fg_indexed = feature_guide.set_index("feature")
    for col in answer_sheet.columns:
        for row in answer_sheet.index:
            if answer_sheet.loc[row, col] != 1 and fg_indexed.loc[row, col] is not nan:
                answer_sheet.loc[row, col] = 0

    answer_sheet["feature points"] = answer_sheet.sum(axis=1)
    correct_words = [int(f == w) for f, w in zip(word_guide["feature"], word_guide["test_words"])]
    answer_sheet["words spelled correctly"] = correct_words
    answer_sheet.insert(0, "spelled words", list(word_guide["test_words"]))

    stage = check_spelling_stage(level, feature_points)
    return name, stage, answer_sheet


def score_all(level: str, feature_guide: pd.DataFrame, test: pd.DataFrame):
    """Score all students in the test DataFrame.

    Returns list of (name, stage, answer_sheet) on success, or
    raises ValueError with a descriptive message if any student has missing features.
    """
    results = [score_student(level, feature_guide, test, name) for name in test.columns]
    errors = [r for r in results if isinstance(r, dict) and r.get("error")]
    if errors:
        lines = [f"  • {e['student']}: {', '.join(e['missing'])}" for e in errors]
        raise ValueError(
            "The selected feature guide level does not match this workbook.\n"
            "Missing words for:\n" + "\n".join(lines)
        )
    return results


def write_output(out_path, results: list):
    """Write scored results to an Excel workbook at out_path."""
    writer = pd.ExcelWriter(out_path, engine="xlsxwriter")

    # Summary sheet
    summary = pd.DataFrame([[r[0], r[1]] for r in results], columns=["Name", "Learning Stage"])
    summary.to_excel(writer, sheet_name="Summary", index=False)

    # Individual student sheets
    for name, stage, answer_sheet in results:
        answer_sheet.to_excel(writer, sheet_name=name, startrow=2)
        worksheet = writer.book.get_worksheet_by_name(name)
        worksheet.write(0, 0, "Name")
        worksheet.write(0, 1, name)
        worksheet.write(1, 0, "Spelling Stage")
        worksheet.write(1, 1, stage)

        # Dynamic conditional formatting range (data starts at row 4, col C)
        n_rows = len(answer_sheet)
        n_cols = len(answer_sheet.columns)
        last_row = n_rows + 3
        last_col = n_cols + 1
        fmt_range = "C4:{}{}".format(chr(ord("A") + last_col), last_row)
        worksheet.conditional_format(fmt_range, {"type": "icon_set", "icon_style": "3_symbols"})

    writer.close()
