import argparse

from analyze import SAMPLE, load_drive

def elevation_trend(drive_log, i, lookahead_seconds=15):
    if "altitude_m" not in drive_log[i]:
        return None

    now_time = drive_log[i]["timestamp"]
    now_alt = drive_log[i]["altitude_m"]

    future_alt = None
    for j in range(i + 1, len(drive_log)):
        elapsed = drive_log[j]["timestamp"] - now_time
        # Allow a late sample, but do not treat a long GPS gap as a 15-second trend.
        if elapsed > lookahead_seconds + 2:
            break
        if elapsed >= lookahead_seconds and "altitude_m" in drive_log[j]:
            future_alt = drive_log[j]["altitude_m"]
            break

    if future_alt is None:
        return None

    return future_alt - now_alt


def coaching_decision(drive_log, i, current_state, lookahead_seconds=15):
    trend = elevation_trend(drive_log, i, lookahead_seconds)
    if trend is None:
        return None

    speed = drive_log[i]["speed_mph"]
    if speed < 25:
        return None

    if current_state == "coast - dip ahead":
        return "coast - dip ahead" if trend <= -3 else None
    elif current_state == "hold speed - climb ahead":
        return "hold speed - climb ahead" if trend >= 3 else None
    else:
        if trend <= -5:
            return "coast - dip ahead"
        elif trend >= 5:
            return "hold speed - climb ahead"
        else:
            return None


def main():
    parser = argparse.ArgumentParser(description="Replay terrain cues using recorded future altitude.")
    parser.add_argument("file", nargs="?", default=SAMPLE, help="drive JSON file")
    drive = load_drive(parser.parse_args().file)
    if not drive:
        print("No readings in this drive.")
        return

    start_time = drive[0]["timestamp"]
    print("=== Offline coach replay ===")
    last_state = None
    for i, reading in enumerate(drive):
        decision = coaching_decision(drive, i, last_state)
        if decision != last_state and decision is not None:
            elapsed = reading["timestamp"] - start_time
            print(f"t={elapsed:.0f}s speed={reading['speed_mph']:.0f} mph -> {decision}")
        last_state = decision


if __name__ == "__main__":
    main()
