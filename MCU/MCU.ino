#include "hal.h"
#include "fsm.h"

void setup() {
    Serial.begin(9600);
    pinMode(HAL_LED_PIN, OUTPUT);
    hal_tof_init();
    fsm_init();
}

void loop() {
    // fsm_tick();
    hal_uart_send("CHECK\n");
    delay(100);
}
