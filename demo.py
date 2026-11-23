"""Replay the bundled fictional drive and render an elevation and speed chart."""

import json
from statistics import median
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt



def save_plot(readings, path, *, title="Elevation and speed over a drive", subtitle=None):
    if not readings:
        raise ValueError("A plot needs at least one reading.")

    start = readings[0]["timestamp"]
    steps = [b["timestamp"] - a["timestamp"] for a, b in zip(readings, readings[1:])
             if b["timestamp"] > a["timestamp"]]
    gap_limit = 3 * median(steps) if steps else float("inf")
    minutes, altitude, speed = [], [], []
    previous_time = start
    for row in readings:
        elapsed = (row["timestamp"] - start) / 60
        if row["timestamp"] - previous_time > gap_limit:
            minutes.append(elapsed)
            altitude.append(float("nan"))
            speed.append(float("nan"))
        minutes.append(elapsed)
        altitude.append(row.get("altitude_m", float("nan")))
        speed.append(row.get("speed_mph", float("nan")))
        previous_time = row["timestamp"]
    figure, (terrain, vehicle) = plt.subplots(2, 1, sharex=True, figsize=(9, 5.5))
    figure.subplots_adjust(left=0.10, right=0.97, top=0.77, bottom=0.13, hspace=0.40)
    figure.text(0.10, 0.93, title,
                fontsize=20, fontweight="bold", color="#182b37")
    if subtitle:
        figure.text(0.10, 0.87, subtitle, fontsize=11, color="#4a606d")

    terrain.plot(minutes, altitude, color="#00668B", linewidth=2.5)
    terrain.set_title("Elevation (m)", loc="left", fontsize=12, color="#00668B")
    vehicle.plot(minutes, speed, color="#AD4D25", linewidth=2.5)
    vehicle.set_title("Speed (mph)", loc="left", fontsize=12, color="#AD4D25")
    vehicle.set_xlabel("Elapsed time (minutes)", labelpad=6)
    vehicle.set_xlim(0, max(minutes[-1], 1 / 60))
    vehicle.set_ylim(bottom=0)

    for axis in (terrain, vehicle):
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.spines["bottom"].set_color("#bcc9ce")
        axis.tick_params(length=0, colors="#435762", pad=5)
        axis.grid(axis="y", linewidth=0.65, color="#d9e2e5")
        axis.set_axisbelow(True)
    figure.savefig(path, dpi=160, facecolor="white")
    plt.close(figure)


def main():
    from analyze import total_distance, total_fuel
    from coach_test import coaching_decision

    sample = Path(__file__).resolve().parent / "examples" / "synthetic_drive.json"
    with sample.open(encoding="utf-8") as file:
        readings = json.load(file)
    miles = total_distance(readings)
    gallons = total_fuel(readings)
    print(f"Synthetic drive: {len(readings)} readings")
    print(f"Distance: {miles:.2f} mi | Estimated fuel: {gallons:.3f} gal | "
          f"Estimated economy: {miles / gallons:.1f} MPG")
    print("Offline terrain replay")
    previous = None
    for index, row in enumerate(readings):
        decision = coaching_decision(readings, index, previous)
        if decision and decision != previous:
            print(f"  {row['timestamp']:3d}s  {decision}")
        previous = decision
    output = Path("demo-output.png")
    save_plot(readings, output, title="Elevation and speed over a simulated drive",
              subtitle="Synthetic drive  /  1 reading per second  /  Elevation drops out from 1:45 to 2:00")
    print(f"Chart saved to {output}")


if __name__ == "__main__":
    main()
