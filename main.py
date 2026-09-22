from analysis import write_report
from models import SessionAnalysis
from sample_data import build_all_sessions


def main():
    sessions = build_all_sessions()
    for scenario, session in sessions.items():
        print(f"\nScenario: {scenario}")
        result = SessionAnalysis(session).run()
        write_report(result)


main()