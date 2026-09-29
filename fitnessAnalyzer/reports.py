import csv
from pathlib import Path

from fitnessAnalyzer.analysis import build_report_text

SUMMARY_FIELDS = ["session_id", "participant_id", "total", "usable", "classification"]

# creates  output folder
def ensure_output_dir(output_path):
    path = Path(output_path)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise SystemExit(f"no permission to create output folder: {path}")
    return path


# writes 1 row per sesh into analysis_summary.csv
def write_summary_csv(results, output_dir):
    path = output_dir / "analysis_summary.csv"
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "session_id": result["session_id"],
                "participant_id": result["person_id"],
                "total": result["total"],
                "usable": result["usable"],
                "classification": result["classification"],
            })

# writesreadable report for every session in analysis_report.txt
def write_report_txt(results, output_dir):
    path = output_dir / "analysis_report.txt"
    with open(path, "w", encoding="utf-8") as file:
        for result in results:
            file.write(build_report_text(result))
            file.write("\n\n")


# writes every rejected row, with the reason it was rejected, into rejected_records.txt
def write_rejected_txt(rejected, output_dir):
    path = output_dir / "rejected_records.txt"
    with open(path, "w", encoding="utf-8") as file:
        if not rejected:
            file.write("no rows were rejected\n")
        for record in rejected:
            file.write(f"{record['file']}, row {record['row']}, field {record['field']}: {record['reason']}\n")