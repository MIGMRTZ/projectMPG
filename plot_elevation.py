import argparse
from pathlib import Path

from analyze import SAMPLE, load_drive
from demo import save_plot


def main():
    parser = argparse.ArgumentParser(description="Plot elevation and speed on a shared time axis.")
    parser.add_argument("file", nargs="?", type=Path, default=SAMPLE, help="drive JSON file")
    parser.add_argument("--output", type=Path, default=Path("elevation_speed_overlay.png"))
    args = parser.parse_args()
    drive = load_drive(args.file)
    if not drive:
        parser.exit(message="No readings to plot.\n")
    subtitle = "Synthetic example" if args.file.resolve() == SAMPLE else None
    save_plot(drive, args.output, subtitle=subtitle)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
