import argparse

from analyze import SAMPLE, load_drive, print_stats
from compare_drives import segment


def main():
    parser = argparse.ArgumentParser(description="Compare one time window to a full drive.")
    parser.add_argument("file", nargs="?", default=SAMPLE, help="drive JSON file")
    parser.add_argument("--start", type=float, default=0, help="start in seconds")
    parser.add_argument("--end", type=float, default=60, help="end in seconds")
    args = parser.parse_args()
    if not 0 <= args.start < args.end:
        parser.error("Use a nonnegative start time and a later end time.")
    drive = load_drive(args.file)
    # Use the whole drive as a baseline for the stretch of road the user picked.
    print_stats("Whole drive", drive)
    print_stats(f"Seconds {args.start:g} to {args.end:g}", segment(drive, args.start, args.end))


if __name__ == "__main__":
    main()
