#include "hal.h"
#include "fsm.h"

void setup() {
    Serial.begin(9600);
    hal_tof_init();  // also initializes FastLED strip
    fsm_init();
}

void loop() {
    fsm_tick();
}
