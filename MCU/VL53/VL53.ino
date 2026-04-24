/**
 * VL53L3CX Time-of-Flight Sensor — Arduino Sample
 *
 * Wiring (Uno/Nano):
 *   VIN   → 3.3V
 *   GND   → GND
 *   SDA   → A4
 *   SCL   → A5
 *   XSHUT → D7  (optional — comment out XSHUT lines if not connected)
 *   GPIO1 → D2  (optional — for interrupt-driven mode)
 *
 * Library: "STM32duino VL53L3CX" via Arduino Library Manager
 */

#include <Wire.h>
#include <vl53l3cx_class.h>

#define XSHUT_PIN 7   // Set to -1 if XSHUT not connected

// Pass XSHUT pin to constructor (-1 = unmanaged)
VL53L3CX sensor(&Wire, XSHUT_PIN);

void setup() {
  Serial.begin(115200);
  while (!Serial);  // Wait for Serial on Leonardo/boards with native USB

  Wire.begin();
  Wire.setClock(400000);  // 400 kHz Fast Mode

  Serial.println("VL53L3CX Init...");

  // Power cycle via XSHUT if connected
  if (XSHUT_PIN >= 0) {
    pinMode(XSHUT_PIN, OUTPUT);
    digitalWrite(XSHUT_PIN, LOW);
    delay(10);
    digitalWrite(XSHUT_PIN, HIGH);
    delay(10);
  }

  if (sensor.begin() != 0) {
    Serial.println("ERROR: sensor.begin() failed. Check wiring.");
    while (1);
  }

  // Optional: change I2C address if running multiple sensors
  // sensor.VL53L3CX_SetDeviceAddress(0x54);  // New 8-bit address

  if (sensor.InitSensor(0x52) != 0) {  // 0x52 = default 8-bit I2C address
    Serial.println("ERROR: InitSensor() failed.");
    while (1);
  }

  // Distance mode: SHORT (~1.3m, less ambient noise)
  //                MEDIUM (~3m)
  //                LONG   (~3m+, max range, more ambient sensitivity)
  sensor.VL53L3CX_SetDistanceMode(VL53L3CX_DISTANCEMODE_LONG);

  // Timing budget in microseconds (higher = more accurate, slower)
  // Valid values: 8000, 15000, 20000, 33000, 50000, 100000, 200000, 500000
  sensor.VL53L3CX_SetMeasurementTimingBudgetMicroSeconds(50000);

  // Inter-measurement period must be >= timing budget
  sensor.VL53L3CX_SetInterMeasurementPeriodMilliSeconds(55);

  sensor.VL53L3CX_StartMeasurement();

  Serial.println("Ranging started. Waiting for data...\n");
}

void loop() {
  uint8_t dataReady = 0;

  // Poll until a measurement is ready
  sensor.VL53L3CX_GetMeasurementDataReady(&dataReady);
  if (!dataReady) return;

  VL53L3CX_MultiRangingData_t rangingData;
  sensor.VL53L3CX_GetMultiRangingData(&rangingData);

  int numObjects = rangingData.NumberOfObjectsFound;

  Serial.print("Objects detected: ");
  Serial.println(numObjects);

  for (int i = 0; i < numObjects; i++) {
    VL53L3CX_TargetRangeData_t *obj = &rangingData.RangeData[i];

    Serial.print("  [");
    Serial.print(i);
    Serial.print("] Distance: ");
    Serial.print(obj->RangeMilliMeter);
    Serial.print(" mm");

    Serial.print("  Signal: ");
    Serial.print((float)obj->SignalRateRtnMegaCps / 65536.0f, 2);
    Serial.print(" Mcps");

    Serial.print("  Ambient: ");
    Serial.print((float)obj->AmbientRateRtnMegaCps / 65536.0f, 2);
    Serial.print(" Mcps");

    Serial.print("  Status: ");
    Serial.print(obj->RangeStatus);
    Serial.print(" (");
    Serial.print(rangeStatusToString(obj->RangeStatus));
    Serial.println(")");
  }

  if (numObjects == 0) {
    Serial.println("  (no targets in range)");
  }

  Serial.println();

  // Clear interrupt and restart measurement
  sensor.VL53L3CX_ClearInterruptAndStartMeasurement();

  delay(10);
}

// Helper: decode range status codes
const char* rangeStatusToString(uint8_t status) {
  switch (status) {
    case 0:  return "Valid";
    case 1:  return "Sigma fail";
    case 2:  return "Signal fail";
    case 4:  return "Out of bounds";
    case 7:  return "Wrap-around";
    case 14: return "No target";
    default: return "Unknown";
  }
}
