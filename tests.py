from pathlib import Path
from fitness_analyzer.analysis import check_entry, check_recovery, classify_session, compare_to_baseline, summarize
from fitness_analyzer.exceptions import InvalidIdentifierError, InvalidRecordError
from fitness_analyzer.loaders import (
    check_pattern, convert_field, load_participants, load_sessions,
    PARTICIPANT_ID_PATTERN, SESSION_ID_PATTERN,
)
from fitness_analyzer.models import Measurement, Person, SessionAnalysis, WorkoutSession

DATA_DIR = Path("data")

def test_check_entry():
    good = Measurement(0, 100, 2.0, 33.0, 0.5, 0.9)
    missing_heart_rate = Measurement(0, None, 2.0, 33.0, 0.5, 0.9)
    impossible_heart_rate = Measurement(0, 265, 2.0, 33.0, 0.5, 0.9)
    negative_activity = Measurement(0, 100, 2.0, 33.0, -0.2, 0.9)
    low_quality = Measurement(0, 100, 2.0, 33.0, 0.5, 0.3)

    assert check_entry(good) == []
    assert len(check_entry(missing_heart_rate)) == 1
    assert len(check_entry(impossible_heart_rate)) == 1
    assert len(check_entry(negative_activity)) == 1
    assert len(check_entry(low_quality)) == 1

def test_check_entry_boundaries():
    at_cutoff = Measurement(0, 100, 2.0, 33.0, 0.5, 0.6)
    below_cutoff = Measurement(0, 100, 2.0, 33.0, 0.5, 0.59)
    assert check_entry(at_cutoff) == []
    assert len(check_entry(below_cutoff)) == 1

    low_edge = Measurement(0, 35, 2.0, 33.0, 0.5, 0.9)
    high_edge = Measurement(0, 205, 2.0, 33.0, 0.5, 0.9)
    assert check_entry(low_edge) == []
    assert check_entry(high_edge) == []

def test_calculations():
    assert summarize([1, 2, 3]) == {"average": 2, "min": 1, "max": 3}
    assert compare_to_baseline(90, 70) == 20
    assert check_recovery([150, 150, 120, 100, 80, 80], [0.9, 0.9, 0.5, 0.3, 0.1, 0.1])
    assert not check_recovery([100, 100, 100, 100, 100, 100], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

def test_classify_session():
    assert classify_session(3, 12, None, False)[0] == "insufficient data"
    assert classify_session(6, 12, 5, False)[0] == "resting"
    assert classify_session(12, 12, 30, False)[0] == "moderate activity"
    assert classify_session(12, 12, 60, False)[0] == "high activity"
    assert classify_session(12, 12, 30, True)[0] == "recovering"

def test_encapsulation():
    person = Person("P1", 65, 1.5, 32.0)
    try:
        person.baseline_heart_rate = -5
        assert False, "negative heart rate was accepted"
    except ValueError:
        pass
    assert person.baseline_heart_rate == 65

    session = WorkoutSession("FIT-2026-999", person)
    session.add_entry(Measurement(0, 100, 2.0, 33.0, 0.5, 0.9))
    session.entries.append(Measurement(1, 100, 2.0, 33.0, 0.5, 0.9))
    assert len(session.entries) == 1

def test_identifier_patterns():
    check_pattern("P001", PARTICIPANT_ID_PATTERN, "participant_id")
    check_pattern("FIT-2026-001", SESSION_ID_PATTERN, "session_id")

    try:
        check_pattern("001", PARTICIPANT_ID_PATTERN, "participant_id")
        assert False, "bad participant id was accepted"
    except InvalidIdentifierError:
        pass

    try:
        check_pattern("FIT-26-102", SESSION_ID_PATTERN, "session_id")
        assert False, "bad session id was accepted"
    except InvalidIdentifierError:
        pass

    try:
        check_pattern(None, PARTICIPANT_ID_PATTERN, "participant_id")
        assert False, "missing id was accepted"
    except InvalidRecordError:
        pass

def test_convert_field():
    assert convert_field("70", "timestamp") == 70
    assert convert_field("1.5", "heart_rate") == 1.5

    try:
        convert_field("fast", "heart_rate")
        assert False, "non-numeric value was accepted"
    except InvalidRecordError:
        pass

    try:
        convert_field("", "activity_level")
        assert False, "missing value was accepted"
    except InvalidRecordError:
        pass

def test_missing_file():
    try:
        load_participants(DATA_DIR / "does_not_exist.csv")
        assert False, "missing file did not raise an error"
    except FileNotFoundError:
        pass

def test_load_real_data():
    participants = load_participants(DATA_DIR / "participants.csv")
    assert "P001" in participants
    assert len(participants) == 3

    sessions, rejected = load_sessions(DATA_DIR / "fitness_sessions.csv", participants, "fitness_sessions.csv")
    assert "FIT-2026-001" in sessions
    assert len(rejected) == 5  

    assert "FIT-2026-005" in sessions
    assert len(sessions["FIT-2026-005"].entries) == 0

    invalid_sessions, invalid_rejected = load_sessions(
        DATA_DIR / "fitness_sessions_invalid.csv", participants, "fitness_sessions_invalid.csv"
    )
    assert len(invalid_rejected) == 10
    assert set(invalid_sessions.keys()) == {"FIT-2026-101", "FIT-2026-102", "FIT-2026-103"}
    assert len(invalid_sessions["FIT-2026-101"].entries) == 1
    assert len(invalid_sessions["FIT-2026-102"].entries) == 0
    assert len(invalid_sessions["FIT-2026-103"].entries) == 0


def test_rejected_records_have_a_field():
    participants = load_participants(DATA_DIR / "participants.csv")
    _, rejected = load_sessions(DATA_DIR / "fitness_sessions_invalid.csv", participants, "fitness_sessions_invalid.csv")
    assert all("field" in record for record in rejected)

    heart_rate_issues = [r for r in rejected if r["field"] == "heart_rate"]
    assert len(heart_rate_issues) >= 1

    participant_issues = [r for r in rejected if r["field"] == "participant_id"]
    assert len(participant_issues) >= 1 


def test_full_analysis():
    participants = load_participants(DATA_DIR / "participants.csv")
    sessions, rejected = load_sessions(DATA_DIR / "fitness_sessions.csv", participants, "fitness_sessions.csv")

    result = SessionAnalysis(sessions["FIT-2026-001"]).run()
    assert result["classification"] == "resting"

    # every row in in this has poor signal & 0 usable entries, but session is still reported and labeled as insufficnet data
    result = SessionAnalysis(sessions["FIT-2026-005"]).run()
    assert result["usable"] == 0
    assert result["classification"] == "insufficient data"

test_check_entry()
test_check_entry_boundaries()
test_calculations()
test_classify_session()
test_encapsulation()
test_identifier_patterns()
test_convert_field()
test_missing_file()
test_load_real_data()
test_rejected_records_have_a_field()
test_full_analysis()
print("All tests passed.")