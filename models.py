from analysis import (
    MIN_USABLE, check_entry, check_recovery,
    classify_session, compare_to_baseline, summarize,
)

class Person:
    def __init__(self, person_id, baseline_heart_rate, baseline_skin_response, baseline_temperature):
        self.person_id = person_id
        self.baseline_heart_rate = baseline_heart_rate
        self.baseline_skin_response = baseline_skin_response
        self.baseline_temperature = baseline_temperature

#private attribute, can only be set through this property, blocks non positive values.
    @property
    def baseline_heart_rate(self):
        return self._baseline_heart_rate

    @baseline_heart_rate.setter
    def baseline_heart_rate(self, value):
        if value is None or value <= 0:
            raise ValueError("baseline_heart_rate must be a positive number")
        self._baseline_heart_rate = value


class Measurement:
    def __init__(self, timestamp, heart_rate, skin_response, temperature, activity_level, signal_quality):
        self.timestamp = timestamp
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level
        self.signal_quality = signal_quality

# class methods: this is how a Meaasurement first gets created from one of the generators dicts, no object exists yet to call it on
    @classmethod
    def from_dict(cls, data):
        return cls(
            data["timestamp"], data["heart_rate"], data["skin_response"],
            data["temperature"], data["activity_level"], data["signal_quality"],
        )

#composition example: holds one Person & a list of Measurements
class WorkoutSession:
    def __init__(self, person):
        self.person = person
        self._entries = []

# returns copy so the private list cant be changed from the outside 
    @property
    def entries(self):
        return self._entries.copy()

    def add_entry(self, measurement):
        self._entries.append(measurement)


class SessionAnalysis:
    def __init__(self, session):
        self.session = session

    def run(self):
        person = self.session.person
        usable = []
        rejected = {} # ^ divides entries into usable/non-usable
        for entry in self.session.entries:
            problems = check_entry(entry)
            if problems:
                rejected[entry.timestamp] = problems
            else:
                usable.append(entry)

        summaries = {}
        comparison = {}
        hr_difference = None
        recovering = False

        # calculate summary and compare to baseline (given theres enough usable data in session)
        if len(usable) >= MIN_USABLE:
            values = {
                "heart_rate": [entry.heart_rate for entry in usable],
                "skin_response": [entry.skin_response for entry in usable],
                "temperature": [entry.temperature for entry in usable],
                "activity_level": [entry.activity_level for entry in usable],
            }
            for name, numbers in values.items():
                summaries[name] = summarize(numbers)

            baselines = {
                "heart_rate": person.baseline_heart_rate,
                "skin_response": person.baseline_skin_response,
                "temperature": person.baseline_temperature,
            }
            for name, baseline in baselines.items():
                comparison[name] = compare_to_baseline(summaries[name]["average"], baseline)

            hr_difference = comparison["heart_rate"]
            recovering = check_recovery(values["heart_rate"], values["activity_level"])

        label, explanation = classify_session(len(usable), len(self.session.entries), hr_difference, recovering)
        return {
            "person_id": person.person_id,
            "total": len(self.session.entries),
            "usable": len(usable),
            "rejected": rejected,
            "summaries": summaries,
            "comparison": comparison,
            "classification": label,
            "explanation": explanation,
        }