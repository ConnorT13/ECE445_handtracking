/**
 * VL53L3CX — Arduino Sample using PWFusion_VL53L3C library
 *
 * Install: arduino-cli lib install "PWFusion_VL53L3C"
 *
 * Wiring (Uno/Nano):
 *   VIN   → 3.3V
 *   GND   → GND
 *   SDA   → A4
 *   SCL   → A5
 *   XSHUT → D7  (optional — leave floating/unconnected if not used)
 */

#include <Wire.h>
#include <PWFusion_VL53L3C.h>

#define XSHUT_PIN 7   // Comment out / remove if XSHUT not wired

PWFusion_VL53L3C sensor;

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Wire.begin();
  Wire.setClock(400000);  // 400 kHz Fast Mode I2C

  // If XSHUT is wired, toggle it to hard-reset the sensor
#ifdef XSHUT_PIN
  pinMode(XSHUT_PIN, OUTPUT);
  digitalWrite(XSHUT_PIN, LOW);
  delay(10);
  digitalWrite(XSHUT_PIN, HIGH);
  delay(10);
#endif

  Serial.println("Initializing VL53L3CX...");

  // begin() returns 0 on success
  if (sensor.begin(Wire) != 0) {
    Serial.println("ERROR: Could not find sensor. Check wiring and I2C address.");
    while (1);
  }

  Serial.println("Sensor found!");

  // Distance mode:
  //   VL53L3C_DISTANCEMODE_SHORT  — up to ~1.3m, best ambient noise rejection
  //   VL53L3C_DISTANCEMODE_MEDIUM — up to ~3m
  //   VL53L3C_DISTANCEMODE_LONG   — up to ~3m+, most sensitive to ambient light
  sensor.setDistanceMode(VL53L3C_DISTANCEMODE_LONG);

  // Timing budget (microseconds). Higher = more accurate, slower updates.
  //   Valid: 8000, 15000, 20000, 33000, 50000, 100000, 200000, 500000
  sensor.setMeasurementTimingBudget(50000);

  // Inter-measurement period (ms). Must be >= timing budget / 1000.
  sensor.setInterMeasurementPeriod(55);

  sensor.startRanging();

  Serial.println("Ranging started.\n");
}

void loop() {
  // isDataReady() returns true when a fresh measurement is available
  if (!sensor.isDataReady()) return;

  VL53L3C_MultiRangingData_t data;
  sensor.getMultiRangingData(&data);

  int n = data.NumberOfObjectsFound;

  Serial.print("Targets found: ");
  Serial.println(n);

  for (int i = 0; i < n; i++) {
    VL53L3C_TargetRangeData_t &obj = data.RangeData[i];

    Serial.print("  [");
    Serial.print(i);
    Serial.print("]  ");
    Serial.print(obj.RangeMilliMeter);
    Serial.print(" mm");

    // Signal rate: higher = stronger return = more reliable
    float signal = (float)obj.SignalRateRtnMegaCps / 65536.0f;
    Serial.print("  Signal: ");
    Serial.print(signal, 2);
    Serial.print(" Mcps");

    Serial.print("  Status: ");
    Serial.println(statusStr(obj.RangeStatus));
  }

  if (n == 0) Serial.println("  (no targets)");

  Serial.println();

  sensor.clearInterrupt();  // Required to trigger the next measurement
}

const char* statusStr(uint8_t s) {
  switch (s) {
    case 0:  return "OK";
    case 1:  return "Sigma fail (noisy — try longer timing budget)";
    case 2:  return "Signal fail (too far or dark)";
    case 4:  return "Out of bounds";
    case 7:  return "Wrap-around (too close, <4cm)";
    case 14: return "No target";
    default: return "Unknown";
  }
}
