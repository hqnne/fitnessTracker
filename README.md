# OPTION A - Smart Fitness Session Analyzer

Name: Hanne Austad
Student number: 375093

This repository contains a program that takes data from fitness trackers, analyzes it, validates it and and compares it with certain reference values, and finally classifies each session into a specific category (resting, moderate activity, high activity, recovery, insufficient data).

## File tree

- `main.py` runs all five scenarios (resting, moderate, high, recovery, insufficient) and prints a report for each
- `models.py` contains the classes
- `analysis.py` contains functions used for validation, calculations and reports
- `sample_data.py` creates the five scenarios using the provided generator
- `tests.py` contains tests
- `data_generator.py`, `example_usage.py`, `DATA_description.md` are the student starter files from Canvas (no changes have been made to these)

## Classes explained

The program uses 4 classes, and these are stored under `models.py`:

1. Person (encompasses participants and reference values - resting HR, skin response, temp)
2. Measurement (recorded observation)
3. WorkoutSession (one Person and Measurement objects)
4. SessionAnalysis (validates and summarizes the recorded sessions, and returns a result dict)

Measurement.from_dict is a class method that builds a Measurement object straight from one of the generators dictionaries.It's a class method instead of a regular one because theres no existing object to call on it yet. It's the way a Measurement gets created in the first place.

## Usage of composition and encapsulation

Composition was used instead of inheritance because the classes carry out different functions and do not share any behaviour. As such, composition was preferable in this program.

In this repo composition takes shape in the form of WorkoutSession containing a Person and its measurements, while SessionAnalysis contains a WorkoutSession. In terms of encapsulation, Person.\_baseline_heart_rate is set through a property that rejects non positive values. WorkOutSession.\_entries is private, and the entries property returns a copy.

## Functions explained

The functions are stored under `analysis.py`, and their individual purpose are as follows:

- check_entry: checks recorded measurement for missing/invalid values/low signal quality, and returns a list of potential problems
- calculate_mean: returns the avg of a list of numbers
- summarize: returns the avg, min and max of a list of numbers
- compare_to_baseline: returns how far a value is from participants reference value
- check_recovery: checks whether HR or activity both fell from the start of session to the end
- classify_session: applies the rules and returns a label & explanation
- write_report: prints ressults dict as a report

## Data used

Measurements are stored as a list in WorkOutSession.\_entries. Dictionaries are used for the input (LIMITS, raw generator data) and the output (summaries, comparison, rejected, and final result dict returned by SessionAnalysis.run, which write_report then prints).

## Rules and other key facts

The ranges listed in DATA_DESCRIPTION.md are used to determines wheter a measurement is rejected or not. If it falls outside of that range, the measurement is deemed invalid. Measurements are also rejected if they are missing values or if the signal quality is below 0.6.

The session analyzer classifies the sessions using this rulebook:

1. Insufficienet data: the session has less tthan 6 usable measurements
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
