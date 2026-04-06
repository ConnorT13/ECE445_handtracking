import serial
import time


class ArduinoController:
    def __init__(self,
                 port='COM5',
                 baudrate=9600,
                 timeout=1):
        """
        Initialize and open serial connection.
        """
        self.ser = None
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=timeout
            )

            # Clear buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            # Give Arduino time to reset
            time.sleep(2)

            print(f"Connected to Arduino on {port}")
        except serial.SerialException as e:
            print(f"WARNING: Could not connect to Arduino on {port}: {e}")
            print("Running without Arduino — UI will still work.")

    def send_cmd(self, byte_val: int):
        """
        Send a single byte command to Arduino and print response.
        """
        if self.ser is None or not self.ser.is_open:
            # print("Serial port not open.")
            return

        self.ser.write(bytes([byte_val]))

        response = self.ser.readline().decode('utf-8').strip()
        if response:
            print(f"Arduino: {response}")
        else:
            print("Arduino: (no response)")

    def run(self):
        """
        Interactive command loop.
        """
        try:
            while True:
                cmd = input("Enter command (on/off/toggle/quit): ").strip().lower()

                if cmd == "on":
                    self.send_cmd(0x01)
                elif cmd == "off":
                    self.send_cmd(0x02)
                elif cmd == "toggle":
                    self.send_cmd(0x03)
                elif cmd == "quit":
                    break
                else:
                    print("Unknown command")

        finally:
            self.close()

    def close(self):
        """
        Close serial connection cleanly.
        """
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            print("Serial connection closed.")