# OPTION A - Smart Fitness Session Analyzer

Hanne Austad, 375093

This repository contains a program that extracts fitness tracker data from CSV files, validates it and and compares it with each participants baseline values. The program classifies every session into five distinct categories: resting, moderate activity, high activity, recovery, insufficient data. Invalid rows are rejected individually, alongside a clear reason, so that the program can continue running instead of collapsing when it counters bad data.

This revision builds upon Assignment 1. This time the analysis has been reorganized into a package and utilizes real CSV files rather than the simulated generator.

## File tree

fitnessTracker
├── data
│ ├── fitness_sessions.csv
│ ├── fitness_sessions_invalid.csv
│ └── participants.csv
├── fitness_analyzer
│ ├── **init**.py
│ ├── analysis.py
│ ├── exceptions.py
│ ├── loaders.py
│ ├── models.py
│ └── reports.py
├── student_starter_files
│ ├── DATA_DESCRIPTION.md
│ ├── data_generator.py
│ └── example_usage.py
├── main.py
├── README.md
├── requirements.txt
└── tests.py

## Classes explained

The program uses 4 classes, and these are stored under `models.py`:

1. `Person` (participant id and reference values - resting HR, skin response, temp)
2. `Measurement` (one recorded observation)
3. `WorkoutSession` (one session ID, one Person and its Measurement objects)
4. `SessionAnalysis` (validates and summarizes a session, and returns a result dict)

`Measurement.from_dict` is a class method that builds a `Measurement` object straight from a dictinary.It's a class method instead of a regular one because theres no existing object to call on it yet. It's the way a `Measurement` gets created in the first place.

## Usage of composition and encapsulation

Composition was used instead of inheritance because the classes carry out different functions and do not share any behaviour. As such, composition was preferable in this program.

In this repo composition takes shape in the form of `WorkoutSession` containing a `Person` and its measurements, while `SessionAnalysis` contains a `WorkoutSession`. In terms of encapsulation, `Person._baseline_heart_rate` is set through a property that rejects non positive values. `WorkOutSession._entries` is private, and the `entries` property returns a copy.

## Functions explained

Stored under fitness_analyzer/`analysis.py`:

- `check_entry`: checks recorded measurement for missing/invalid values/low signal quality, and returns a list of problems
- `calculate_mean`: returns the avg of a list of numbers
- `summarize`: returns the avg, min and max of a list of numbers
- `compare_to_baseline`: returns how far a value is from participants reference value
- `check_recovery`: checks whether HR or activity both fell from the start of session to the end
- `classify_session`: applies the rules and returns a label & explanation
- `build_report_text`/`write_report`: build report as one string, used for both console and the saved report file

Stored under fitness_analyzer/`loaders.py`:

- `check_pattern`: checks a value against regex, raises Invalid Identifier/Record Error if requirements are not met
- `convert_field`: turns raw csv string into a number, raises Invalid Record Error instead of crashing on bad data.
- `field_from_problem`: works out which field a `check_entry` problem is about,so a rejected row can name said field
- `load_participants`: reads participants.csv into a dict of `Person` objects
- `load_sessions`: reads a session csv file ino a dict of `WorkoutSession` objects, with a list of every rejected row

Stored under fitness_analyzer/`reports.py`:

- `ensure_output_dir`: creates the output folder if it doesnt exist already
- `write_summary_csv`, `write_report_txt`, `write_rejected_txt`: created output files

# Data loading and validation

In `main.py`, `participants.csv` is loaded, followed by the valid and invalid session files (automatically deduced from the provided session file via pathlib). Each row is parsed using `csv.DictReader` and converted to proper data before proceeding. Two identifiers are validated using regular expressions (`re.fullmatch`) ensuring a full match rather than just a partial one.

- `participant_id`: `^P\d{3}$`
- `session_id`: `^FIT-\d{4}-\d{3}$`

A row is rejected based on the following criteria:

- Mismatched column count or missing required fields
- Values unable to be converted to numbers
- Improper participant or session ID formats
- Participant not present in `participants.csv`
- Value exceeding defined range in data dictionary
- `signal_quality` is below 0.6 (documented as `MIN_QUALITY` in `analysis.py`)

Rejected rows are documented with the source filename, row number, problematic field, and reason, saved to `rejected_records.txt`.

## Session registration

A session is registered as soon as both `participant_id` and `session_id` are validated, even if individual row measurements are rejected later. This allows for sessions to be classified with 0 usable entries, labeled "insufficient data", rather than silently disappearing from the report due to incorrect row validation.

## error handling

Custom exceptions `InvalidIdentifierError` and `InvalidRecordError` are raised and caught, both inheriting from `ValueError` and carrying the problematic field. Targeted try/except blocks are employed to address specific errors:

- `FileNotFoundError` and `PermissionError` when opening the profile file and each session file in `main.py`
- `ValueError` in `convert_field`, whena a number cant be parsed
- `KeyError` when looking up nonexistent IDs
- `csv.Error` when encountering corrupted CSV files
- `InvalidIdentifierError`/`InvalidRecordError`, per row, in `load_sessions`

No empty except blocks, and no bare `except Exception` anywhere. Real bugs should crash loudly instead of being left undiscovered.

## Data used

Measurements are stored as a list in `WorkOutSession._entries`. Dictionaries are used for the input (`LIMITS`, raw generator data) and the output (`summaries`, `comparison`, `rejected`, and final result dict returned by `SessionAnalysis.run`, which `write_report` then prints).

## Rules and other key facts

The ranges listed in `DATA_DESCRIPTION.md` are used to determine whether a measurement is rejected or not. If it falls outside of that range, the measurement is deemed invalid. Measurements are also rejected if they are missing values or if the signal quality is below 0.6.

The session analyzer classifies the sessions using this rulebook:

1. Insufficient data: the session has less tthan 6 usable measurements
2. Recovery: heart rate drops by 15 bpm (or more) and activity drosp by 0.2 (or more), from first third of sessino to last third
3. Resting: avg hearte rate is less than 15 bpm above resting reference
4. Moderate activity: avg heart rate is less than 43 bpm above resting reference (and rule 3 didnt already apply)
5. High activity: everything else

The 5 scenarios cover normal (resting, moderate, high), unusual (recovery), and invalid (poor quality) cases.

## Running the program

```bash
git clone https://github.com/hqnne/fitnessTracker.git
cd fitnessTracker
python3 main.py
```

## Example output

```
Scenario: high_activity
==================================================
participant P003
usable entries: 12 of 12
heart_rate: average 135.67, min 123, max 150
  difference from reference: 57.67
skin_response: average 1.8, min 1.3, max 2.1
  difference from reference: 0.63
temperature: average 33.34, min 33.17, max 33.65
  difference from reference: 0.58
activity_level: average 0.8, min 0.69, max 0.91
Classification: high activity
Why: average heart rate differs from resting reference by 57.67 bpm.
```

## Identified limitations

The program uses fake simulated data, not actual measurements from real people, so we don't know how well the chosen ranges and thresholds would hold up in reality. Measurements also get fully rejected even if only one value is bad, which in real life could risk wasting a lot of otherwise usable data. The generator seed is also fixed at a set value, so results stay the same between runs.
