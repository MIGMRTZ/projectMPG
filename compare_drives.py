import argparse
from pathlib import Path

from analyze import SAMPLE, drive_stats, load_drive, print_stats


def segment(drive_log, start_sec, end_sec):
    if not drive_log:
        return []
    start_time = drive_log[0]["timestamp"]
    result = []
    for reading in drive_log:
        elapsed = reading["timestamp"] - start_time
        if start_sec <= elapsed <= end_sec:
            result.append(reading)
    return result


def main():
    parser = argparse.ArgumentParser(description="Compare whole drives and their first ten minutes.")
    parser.add_argument("files", nargs="*", type=Path, help="one or more drive JSON files")
    paths = parser.parse_args().files or sorted(Path.cwd().glob("drive_2*.json")) or [SAMPLE]
    for path in paths:
        readings = load_drive(path)
        print(path.name)
        print_stats("  Whole drive", readings)
        print_stats("  First ten minutes", segment(readings, 0, 600))


if __name__ == "__main__":
    main()
