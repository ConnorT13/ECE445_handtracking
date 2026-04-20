#ifndef HAL_H
#define HAL_H

#include <Arduino.h>
#include <stddef.h>

// LED on pin 8, active HIGH — change here if hardware moves
#define HAL_LED_PIN 8

// Stub: button on pin 7 simulates ToF presence during development (active LOW via INPUT_PULLUP)
#define HAL_PRESENCE_BTN_PIN 7

// Initializes the VL53L0X ToF sensor over I2C; halts on failure.
void hal_tof_init();

// Performs a single ranging measurement. Returns distance in mm,
// or -1 if the sensor reports an out-of-range / error status.
int16_t hal_tof_read_mm();

// Drives the LED on HAL_LED_PIN HIGH (on=true) or LOW (on=false).
void hal_led_set(bool on);

// Sends a null-terminated string over the SoftwareSerial UART to the Pi.
void hal_uart_send(const char* msg);

// Non-blocking line reader on the SoftwareSerial UART.
// Accumulates bytes internally one at a time; copies the complete line
// (without the '\n') into buf and returns true the moment '\n' arrives.
// Returns false on every call where a full line is not yet available.
bool hal_uart_readline(char* buf, size_t maxlen);

#endif // HAL_H
