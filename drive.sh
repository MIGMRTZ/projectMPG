#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"

export GPS_PORT="${GPS_PORT:-/dev/ttyACM0}"
if [[ ! -e "$GPS_PORT" ]]; then
    echo "GPS receiver not found at $GPS_PORT. Set GPS_PORT to its device path." >&2
    exit 1
fi

# Bind a paired adapter, or use an existing serial binding.
if [[ -n "${OBD_MAC:-}" ]]; then
    sudo rfcomm release 0 2>/dev/null || true
    sudo rfcomm bind 0 "$OBD_MAC" 1
fi
if [[ ! -r /dev/rfcomm0 || ! -w /dev/rfcomm0 ]]; then
    echo "A readable, writable /dev/rfcomm0 is required. Check the Bluetooth binding and serial group access." >&2
    exit 1
fi

exec python3 log_drive.py
