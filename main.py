import argparse
from pathlib import Path

from fitness_analyzer.loaders import load_participants, load_sessions
from fitness_analyzer.models import SessionAnalysis
from fitness_analyzer.reports import ensure_output_dir, write_summary_csv, write_report_txt, write_rejected_txt


def parse_args():
    parser = argparse.ArgumentParser(description="analyze fitness session data from csv files")
    parser.add_argument("--profiles", required=True, help="path to participants.csv")
    parser.add_argument("--sessions", required=True, help="path to fitness_sessions.csv")
    parser.add_argument("--output", required=True, help="folder to save the reports in")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        participants = load_participants(args.profiles)
    except FileNotFoundError:
        print(f"cannot find profile file: {args.profiles}")
        return
    except PermissionError:
        print(f"no permission to read profile file: {args.profiles}")
        return

    sessions_path = Path(args.sessions)
    invalid_path = sessions_path.with_name(sessions_path.stem + "_invalid" + sessions_path.suffix)

    all_sessions = {}
    all_rejected = []

    for path in [sessions_path, invalid_path]:
        try:
            sessions, rejected = load_sessions(path, participants, path.name)
            all_sessions.update(sessions)
            all_rejected.extend(rejected)
        except FileNotFoundError:
            print(f"cannot find session file: {path}")
        except PermissionError:
            print(f"no permission to read session file: {path}")

    results = []
    for session in all_sessions.values():
        results.append(SessionAnalysis(session).run())

    output_dir = ensure_output_dir(args.output)
    write_summary_csv(results, output_dir)
    write_report_txt(results, output_dir)
    write_rejected_txt(all_rejected, output_dir)

    accepted_total = sum(result["usable"] for result in results)
    print(f"processed {len(results)} sessions")
    print(f"accepted rows: {accepted_total}")
    print(f"rejected rows: {len(all_rejected)}")
    print("created report files:")
    print(f"  {output_dir / 'analysis_summary.csv'}")
    print(f"  {output_dir / 'analysis_report.txt'}")
    print(f"  {output_dir / 'rejected_records.txt'}")


if __name__ == "__main__":
    main()