from data_generator import generate_fitness_data
from models import Person, Measurement, WorkoutSession

SCENARIOS = ["resting", "moderate_activity", "high_activity", "recovery", "poor_quality"]


def build_session(scenario, seed=42, person_id="P001"):
    profile, observations = generate_fitness_data(
        participant_id=person_id, scenario=scenario, seed=seed, number_of_windows=12
    )
    person = Person(
        profile["participant_id"],
        profile["baseline_heart_rate"],
        profile["baseline_skin_response"],
        profile["baseline_temperature"],
    )
    session = WorkoutSession(person)
    for observation in observations:
        session.add_entry(Measurement.from_dict(observation))
    return session


def build_all_sessions():
    sessions = {}
    for i, scenario in enumerate(SCENARIOS):
        sessions[scenario] = build_session(scenario, person_id=f"P00{i + 1}")
    return sessions