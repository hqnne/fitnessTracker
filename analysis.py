MIN_QUALITY = 0.6
MIN_USABLE = 6
RECOVERY_HR_DROP = 15
RECOVERY_ACTIVITY_DROP = 0.2
RESTING_LIMIT = 15
MODERATE_LIMIT = 43

# based on values mentioned in data_description.md 
LIMITS = {
    "heart_rate": (35, 205),
    "skin_response": (0, float("inf")),
    "temperature": (25, 42),
    "activity_level": (0, 1),
    "signal_quality": (0, 1),
}

# flags and returns problems with entries. if there are no detected problems and the entry is valid, an empty list is returned
def check_entry(entry):
    problems = []
    values = {
        "heart_rate": entry.heart_rate,
        "skin_response": entry.skin_response,
        "temperature": entry.temperature,
        "activity_level": entry.activity_level,
        "signal_quality": entry.signal_quality,
    }
    for name, value in values.items():
        if value is None:
            problems.append(f"{name} missing")
        else:
            low, high = LIMITS[name]
            if value < low or value > high:
                problems.append(f"{name} out of range ({value})")

    if entry.signal_quality is not None and entry.signal_quality < MIN_QUALITY:
        problems.append(f"low signal quality ({entry.signal_quality})")
    return problems


def calculate_mean(numbers):
    return round(sum(numbers) / len(numbers), 2)


def summarize(numbers):
    return {"average": calculate_mean(numbers), "min": min(numbers), "max": max(numbers)}

# a positive result means the value is above the personal reference
def compare_to_baseline(value, baseline):
    return round(value - baseline, 2)

# compares the avg of the first third of the session with the last third. returns true if hr & activity dropped enough to satisfy criteria
def check_recovery(heart_rates, activities):
    third = len(heart_rates) // 3
    heart_rate_drop = calculate_mean(heart_rates[:third]) - calculate_mean(heart_rates[-third:])
    activity_drop = calculate_mean(activities[:third]) - calculate_mean(activities[-third:])
    return heart_rate_drop >= RECOVERY_HR_DROP and activity_drop >= RECOVERY_ACTIVITY_DROP

#checks if the session is uasble, and if it is, returns an intensity label for the recorded session
def classify_session(usable, total, hr_difference, recovering):
    if usable < MIN_USABLE:
        return "insufficient data", f"Only {usable} of {total} entries were usable (need {MIN_USABLE})."
    elif recovering:
        return "recovering", "heart rate and activity both fell clearly from the start to the end."

    text = f"average heart rate differs from resting reference by {hr_difference} bpm."
    if hr_difference < RESTING_LIMIT:
        return "resting", text
    elif hr_difference < MODERATE_LIMIT:
        return "moderate activity", text
    else:
        return "high activity", text


def write_report(result):
    print("=" * 50)
    print(f"participant {result['person_id']}")
    print(f"usable entries: {result['usable']} of {result['total']}")
    for timestamp, problems in result["rejected"].items():
        print(f" rejected entry {timestamp}: {', '.join(problems)}")
    for name, summary in result["summaries"].items():
        print(f"{name}: average {summary['average']}, min {summary['min']}, max {summary['max']}")
        if name in result["comparison"]:
            print(f"  difference from reference: {result['comparison'][name]}")
    print(f"Classification: {result['classification']}")
    print(f"Why: {result['explanation']}")