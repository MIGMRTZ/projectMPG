import os
import time
import json
import obd
import serial
from datetime import datetime

connection = obd.OBD("/dev/rfcomm0")
if not connection.is_connected():
    print("no truck connection - check adapter, bind, ignition")
    raise SystemExit(1)

gps_port = serial.Serial(os.environ.get("GPS_PORT", "/dev/ttyACM0"), 9600, timeout=1)

def nmea_to_degrees(raw, hemisphere):
    # GPS coordinates pack degrees and minutes together. The last two digits
    # before the decimal point start the minutes, even for a three-digit longitude.
    dot = raw.index(".")
    degrees = float(raw[:dot - 2])
    minutes = float(raw[dot - 2:])
    result = degrees + minutes / 60
    if hemisphere == "S" or hemisphere == "W":
        result = -result
    return result

def get_gps_fix():
    fix = {}
    # Position and altitude arrive in separate messages. Try up to ten lines
    # to collect both, then keep the position even if altitude is missing.
    for attempt in range(10):
        line = gps_port.readline().decode("ascii", errors = "replace").strip()
        fields = line.split(",")
        # An RMC message marked A gives a valid position and speed in knots.
        if "RMC" in line and fields[2] == "A":
            fix["lat"] = nmea_to_degrees(fields[3], fields[4])
            fix["lon"] = nmea_to_degrees(fields[5], fields[6])
            fix["gps_speed_mph"] = float(fields[7]) * 1.15078
        # A GGA message reports altitude in meters. A fix quality of 0 means no fix.
        if "GGA" in line and fields[6] != "0" and fields[9] != "":
            try:
                fix["altitude_m"] = float(fields[9])
            except ValueError:
                pass
        if "lat" in fix and "altitude_m" in fix:
            return fix
    if "lat" in fix:
        return fix
    return None

def get_reading():
    speed = connection.query(obd.commands.SPEED)
    rpm = connection.query(obd.commands.RPM)
    load = connection.query(obd.commands.ENGINE_LOAD)
    maf = connection.query(obd.commands.MAF)

    if speed.is_null() or maf.is_null():
        return None

    maf_gps = maf.value.magnitude
    # Estimate grams of fuel per second from airflow, assuming 14.7 g of air per gram of fuel.
    # Convert using 453.6 g per pound, 6.17 pounds per US gallon, and 3600 seconds per hour.
    fuel_gph = (maf_gps / 14.7) / 453.6 / 6.17 * 3600

    reading = {
        "timestamp": time.time(),
        "speed_mph": speed.value.to("mph").magnitude,
        "rpm": rpm.value.magnitude,
        "engine_load": load.value.magnitude,
        "maf_g_s": maf_gps,
        "fuel_rate_gph": fuel_gph
    }

    gps = get_gps_fix()
    # Keep the truck readings even when the GPS receiver has no position yet.
    if gps is not None:
        reading.update(gps)

    return reading

# Readings stay in memory during the drive. Ctrl-C ends the loop so the JSON file can be written.
drive_log = []
print("logger started - Ctrl-C to end drive and save")

try:
    while True:
        try:
            reading = get_reading()
            if reading is not None:
                drive_log.append(reading)
        except Exception as e:
            print(f"skipped a bad reading: {e}")
        time.sleep(1)
except KeyboardInterrupt:
    print("\ndrive ended by driver")

filename = f"drive_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
with open(filename, "w") as f:
    json.dump(drive_log, f, indent=2)

print(f"drive complete: {len(drive_log)} readings saved to {filename}")
