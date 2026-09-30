import csv
import re

from fitness_analyzer.exceptions import InvalidIdentifierError, InvalidRecordError
from fitness_analyzer.models import Person, Measurement, WorkoutSession
from fitness_analyzer.analysis import check_entry

PARTICIPANT_ID_PATTERN = re.compile(r"^P\d{3}$")
SESSION_ID_PATTERN = re.compile(r"^FIT-\d{4}-\d{3}$")

NUMBER_FIELDS = ["heart_rate", "skin_response", "temperature", "activity_level", "signal_quality"]

# checks value against regex pattern, raise exceptions and block improper data
def check_pattern(value, pattern, label):
    if value is None:
        raise InvalidRecordError(label, f"{label} is missing")
    if not pattern.fullmatch(value):
        raise InvalidIdentifierError(label, f"{label} '{value}' has an invalid format")

# turns one raw csv string into a number, raises InvalidRecordError instead of crashing on bad data
def convert_field(value, field_name):
    if value is None or value == "":
        raise InvalidRecordError(field_name, f"{field_name} is missing")
    try:
        if field_name == "timestamp": #timestamp is a whole number, but everything else can have decimals.
            return int(value)
        return float(value)
    except ValueError:
        raise InvalidRecordError(field_name, f"{field_name} value '{value}' is not a number")

# works out which field a check_entry problem is about , so a rejected row can name that field
def field_from_problem(problem):
    if problem.startswith("low signal quality"):
        return "signal_quality"
    return problem.split()[0]

#reads participants.csv ++ returns a dict of participant_id -> Person
def load_participants(path):
    participants = {}
    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            check_pattern(row.get("participant_id"), PARTICIPANT_ID_PATTERN, "participant_id")
            person = Person(
                row["participant_id"],
                float(row["baseline_heart_rate"]),
                float(row["baseline_skin_response"]),
                float(row["baseline_temperature"]),
            )
            participants[person.person_id] = person
    return participants

# reads a session csv file. returns a dict of session_id -> WorkoutSession, ++ a list of rejected rows
def load_sessions(path, participants, source_name):
    sessions = {}
    rejected = []

    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        try:
            for row_number, row in enumerate(reader, start=2):  # (row1 is the header)
                try:
                    if None in row: # DictReader dumps any extra columns under the key None, so this catches rows that are too long
                        raise InvalidRecordError("row", "row has more columns than expected")

                    check_pattern(row.get("session_id"), SESSION_ID_PATTERN, "session_id")
                    check_pattern(row.get("participant_id"), PARTICIPANT_ID_PATTERN, "participant_id")

                    session_id = row["session_id"]
                    participant_id = row["participant_id"]

                    try:
                        person = participants[participant_id]
                    except KeyError:
                        raise InvalidRecordError("participant_id", f"unknown participant {participant_id}")

                    # session gets registered as soon as we know its participant, even if this particular row's own measurement later turns out to be unusable
                    if session_id not in sessions:
                        sessions[session_id] = WorkoutSession(session_id, person)

                    timestamp = convert_field(row.get("timestamp"), "timestamp")
                    values = {}
                    for field in NUMBER_FIELDS:
                        values[field] = convert_field(row.get(field), field)

                    measurement = Measurement(
                        timestamp, values["heart_rate"], values["skin_response"],
                        values["temperature"], values["activity_level"], values["signal_quality"],
                    )

                    problems = check_entry(measurement)
                    if problems:
                        fields = ", ".join(field_from_problem(problem) for problem in problems)
                        raise InvalidRecordError(fields, ", ".join(problems))

                    sessions[session_id].add_entry(measurement)

                except (InvalidIdentifierError, InvalidRecordError) as error:
                    rejected.append({
                        "file": source_name, "row": row_number, "field": error.field, "reason": str(error),
                    })
        # catches broken CSV file, not a bad row
        except csv.Error as error: 
            rejected.append({"file": source_name, "row": "-", "field": "-", "reason": f"could not read the rest of the file: {error}"})

    return sessions, rejected