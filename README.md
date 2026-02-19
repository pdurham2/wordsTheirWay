# Words Their Way Scorer

A tool for scoring student spelling inventories using the [Words Their Way](https://www.pearson.com/en-us/subject-catalog/p/words-their-way-word-study-for-phonics-vocabulary-and-spelling-instruction/P200000000481) framework. Given a student spelling test workbook, it scores each student's responses against phonetic feature patterns and determines their spelling development stage.

## Features

- Supports three inventory levels: **Primary** (K–1), **Elementary** (K–2), and **Upper Level** (Grades 3–7+)
- Scores each student across all phonetic features and calculates a spelling stage
- Outputs a formatted Excel workbook with a summary sheet and individual student sheets with conditional formatting
- Available as both a **web app** (Streamlit) and a **command-line tool**

## Project Structure

```
wordsTheirWay/
├── app.py                  # Streamlit web app
├── wordsTheirWay.py        # CLI entry point
├── requirements.txt
├── wtw/
│   └── scorer.py           # Core scoring logic
└── data/
    ├── WTW6e_Inventories_1507909154.pdf   # Source reference
    ├── feature_guides/
    │   ├── primary.csv
    │   ├── elementary.csv
    │   └── upper-level.csv
    └── samples/
        ├── writing_sample_1.xlsx
        └── upper-level_writing_sample.xlsx
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Web App

```bash
streamlit run app.py
```

1. Select the feature guide level that matches your inventory
2. Upload a student spelling test workbook (`.xlsx`)
3. Click **Score workbook**
4. Review the results summary and download the scored workbook

### Command Line

```bash
python wordsTheirWay.py
```

Follow the prompts to select a level and provide a workbook path.

## Input Format

The input workbook must have:
- A column named `name` containing the target words (one per row)
- One additional column per student, with their spelled responses

| name   | jake   | jane   |
|--------|--------|--------|
| bed    | bed    | bad    |
| ship   | shep   | ship   |
| ...    | ...    | ...    |

The target words must match the selected feature guide exactly. See `data/samples/` for examples and `data/WTW6e_Inventories_1507909154.pdf` for the full inventory reference.

## Output Format

The output workbook contains:
- **Summary sheet** — each student's name and spelling stage
- **Individual sheets** — feature-by-feature scoring with conditional formatting (✓/✗ icons)
