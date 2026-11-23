import json
import argparse
from pathlib import Path
import math

SAMPLE = Path(__file__).resolve().parent / "examples" / "synthetic_drive.json"


def load_drive(filename):
    with open(filename, encoding="utf-8") as stream:
        return json.load(stream)


def print_drive(drive_log):
    for i, reading in enumerate(drive_log):
        print(f"{i:3} {reading['speed_mph']:6.1f} mph {reading['fuel_rate_gph']:5.1f} gph")

def max_gap(drive_log):
    biggest = 0
    for i in range(len(drive_log)):
        if i + 1 < len(drive_log):
            gap = drive_log[i + 1]["timestamp"] - drive_log[i]["timestamp"]
            if gap > biggest:
                biggest = gap
            if gap > 1.5:
                print("WARNING: DROPPED READING!")
    return biggest

def count_slowdowns(drive_log):
    total = 0
    for i in range(len(drive_log)):
        if i + 1 < len(drive_log):
            if drive_log[i + 1]["speed_mph"] < drive_log[i]["speed_mph"]:
                total = total + 1
    return total

def top_speed(drive_log):
    if not drive_log:
        return 0.0
    top = drive_log[0]["speed_mph"]
    for reading in drive_log:
        if reading["speed_mph"] > top:
            top = reading["speed_mph"]
    return top

def avg_speed(drive_log):
    # Weight each speed by the time until the next reading.
    weighted_speed = 0.0
    seconds = 0.0
    for previous, current in zip(drive_log, drive_log[1:]):
        gap = current["timestamp"] - previous["timestamp"]
        if gap > 0:
            weighted_speed += previous["speed_mph"] * gap
            seconds += gap
    if seconds:
        return weighted_speed / seconds
    return drive_log[0]["speed_mph"] if drive_log else 0.0


def total_fuel(drive_log):
    gallons = 0
    for i in range(len(drive_log)):
        if i + 1 < len(drive_log):
            gap_hours = ((drive_log[i + 1]["timestamp"] - drive_log[i]["timestamp"]) / 3600)
            gallons = gallons + drive_log[i]["fuel_rate_gph"] * gap_hours
    return gallons

def total_distance(drive_log):
    miles = 0
    points = []
    for reading in drive_log:
        if "lat" in reading and "lon" in reading:
            points.append((reading["lat"], reading["lon"]))
    for i in range(len(points) - 1):
        lat1, lon1 = math.radians(points[i][0]), math.radians(points[i][1])
        lat2, lon2 = math.radians(points[i + 1][0]), math.radians(points[i + 1][1])
        a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        miles = miles + 2 * 3958.8 * math.asin(math.sqrt(a))
    return miles


def drive_stats(drive_log):
    if len(drive_log) < 2:
        return None
    miles = total_distance(drive_log)
    gallons = total_fuel(drive_log)
    fixes = sum("lat" in row and "lon" in row for row in drive_log)
    return {
        "miles": miles,
        "gallons": gallons,
        "mpg": miles / gallons if gallons > 0 and fixes >= 2 else None,
        "avg_speed": avg_speed(drive_log),
    }


def print_stats(label, drive_log):
    stats = drive_stats(drive_log)
    if stats is None:
        print(f"{label}: not enough readings")
        return
    mpg = f"{stats['mpg']:.1f}" if stats['mpg'] is not None else "n/a"
    print(f"{label}: {stats['avg_speed']:.1f} mph avg   {stats['miles']:.2f} GPS mi   "
          f"{stats['gallons']:.4f} estimated gal   {mpg} estimated MPG")


def main():
    parser = argparse.ArgumentParser(description="Estimate fuel use and distance from drive logs.")
    parser.add_argument("files", nargs="*", type=Path, help="drive JSON files")
    args = parser.parse_args()
    paths = args.files or sorted(Path.cwd().glob("drive_2*.json")) or [SAMPLE]
    for path in paths:
        print_stats(path.name, load_drive(path))


if __name__ == "__main__":
    main()
