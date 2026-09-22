from analysis import check_entry, check_recovery, classify_session, compare_to_baseline, summarize
from models import Measurement, Person
from sample_data import build_session
from models import SessionAnalysis


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


def test_calculations():
    assert summarize([1, 2, 3]) == {"average": 2, "min": 1, "max": 3}
    assert compare_to_baseline(90, 70) == 20
    assert check_recovery([150, 150, 120, 100, 80, 80], [0.9, 0.9, 0.5, 0.3, 0.1, 0.1])
    assert not check_recovery([100, 100, 100, 100, 100, 100], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5])


def test_classify_session():
    assert classify_session(3, 12, None, False)[0] == "insufficient data"
    assert classify_session(12, 12, 5, False)[0] == "resting"
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

    session = build_session("resting")
    session.entries.append(Measurement(99, 100, 2.0, 33.0, 0.5, 0.9))
    assert len(session.entries) == 12


def test_scenarios():
    expected = {
        "resting": "resting",
        "moderate_activity": "moderate activity",
        "high_activity": "high activity",
        "recovery": "recovering",
        "poor_quality": "insufficient data",
    }
    for scenario, label in expected.items():
        result = SessionAnalysis(build_session(scenario)).run()
        assert result["classification"] == label, scenario


test_check_entry()
test_calculations()
test_classify_session()
test_encapsulation()
test_scenarios()
print("All tests passed.")