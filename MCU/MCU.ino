// main.ino — HAL verification sketch (no FSM logic)
#include "hal.h"

void setup() {
    Serial.begin(9600);
    pinMode(HAL_LED_PIN, OUTPUT);
    hal_tof_init();
    Serial.println(F("HAL ready"));
}

void loop() {
    static uint32_t lastTof  = 0;
    static uint32_t lastBlink = 0;
    static bool     ledState  = false;

    uint32_t now = millis();

    // Poll ToF every 100 ms
    if (now - lastTof >= 100) {
        lastTof = now;
        int16_t dist = hal_tof_read_mm();
        Serial.println(dist);
    }

    // Blink LED at ~1 Hz to confirm HAL_LED_PIN is wired correctly
    if (now - lastBlink >= 500) {
        lastBlink = now;
        ledState = !ledState;
        hal_led_set(ledState);
    }
}
