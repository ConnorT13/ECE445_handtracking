## MCU (Arduino Uno / STM32F401 target)

### Hardware
- Arduino Uno (stand-in for STM32F401 custom PCB)
- VL53L0X ToF sensor on I2C (address 0x29)
- LED on pin X (active HIGH)
- UART to Pi: Serial (pins 0/1 on Uno, 9600 baud)

### FSM States
- IDLE: poll ToF every 100ms, light off, wait for presence
- SCANNING: light on, waiting for Pi UART response, 15s timeout
- MATCH_PENDING: light off, 10s delay after receiving MATCH before turning light on
- MATCH_DISPLAYED: light on, 10s display timer, then RESET

### UART Protocol
MCU → Pi: "PRESENCE\n", "RESET\n"
Pi → MCU: "MATCH\n", "NO_MATCH\n", "PRESENCE\n" (when Pi's VL53L3CX ToF triggers first)

### HAL abstraction
All hardware access goes through hal.h / hal.cpp so Arduino → STM32
migration is a drop-in swap. No direct register/library calls in
fsm.cpp — only HAL functions.
