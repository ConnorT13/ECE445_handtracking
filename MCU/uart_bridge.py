# uart_bridge.py — standalone UART test bridge for mirror FSM
# Run: python3 uart_bridge.py
# Requires /dev/serial0 enabled via raspi-config (disable login shell, enable hardware port)
# Simulates face recognition with a 3s sleep stub — CV integration is Phase 4

import time
import sys

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed. Run: pip3 install pyserial")
    sys.exit(1)

try:
    ser = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
except serial.SerialException as e:
    print(f"ERROR: could not open /dev/serial0 — {e}")
    print("Check raspi-config: disable serial login shell, enable hardware serial port.")
    sys.exit(1)

print("[BRIDGE] Listening on /dev/serial0 at 9600 baud")

while True:
    try:
        line = ser.readline().decode("ascii", errors="replace").strip()
    except serial.SerialException as e:
        print(f"[BRIDGE] Serial error: {e}")
        break

    if not line:
        continue

    if line == "PRESENCE":
        print("[BRIDGE] Presence detected")
        time.sleep(3)
        ser.write(b"MATCH\n")
    elif line == "RESET":
        print("[BRIDGE] Reset received")
    else:
        print(f"[BRIDGE] Unknown: {line}")
