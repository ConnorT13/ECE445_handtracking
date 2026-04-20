// ToF stub: HAL_PRESENCE_BTN_PIN substitutes for VL53L0X during development.
// To restore real sensor: replace hal_tof_init() and hal_tof_read_mm() implementations only.
#include "hal.h"
#include <SoftwareSerial.h>
#include <FastLED.h>

static CRGB leds[HAL_NUM_LEDS];

// SoftwareSerial for Pi link: RX=10, TX=11 (keeps pins 0/1 free for USB uploads)
static SoftwareSerial piSerial(10, 11);

// Configures the presence-button pin, starts SoftwareSerial, and initializes
// the WS2812B strip. Only one HAL init entry point exists so all setup lives here.
void hal_tof_init() {
    pinMode(HAL_PRESENCE_BTN_PIN, INPUT_PULLUP);
    piSerial.begin(9600);
    FastLED.addLeds<WS2812B, HAL_LED_PIN, GRB>(leds, HAL_NUM_LEDS);
    FastLED.setBrightness(30);
    hal_led_set(false);
}

// Returns 200 mm (presence) when button is pressed, 2000 mm (empty) when released.
// Button wired to GND — pressed reads LOW due to INPUT_PULLUP.
int16_t hal_tof_read_mm() {
    return digitalRead(HAL_PRESENCE_BTN_PIN) == LOW ? 200 : 2000;
}

// Fills the strip white (on=true) or black/off (on=false) and pushes to hardware.
void hal_led_set(bool on) {
    fill_solid(leds, HAL_NUM_LEDS, on ? CRGB::White : CRGB::Black);
    FastLED.show();
}

// Writes msg over SoftwareSerial to the Pi. Caller is responsible for
// including any required terminator (e.g. "PRESENCE\n").
void hal_uart_send(const char* msg) {
    piSerial.print(msg);
}

// Reads up to one byte per call from the SoftwareSerial RX buffer.
// Accumulates bytes in a static internal buffer until '\n' is received,
// then copies the line (without '\n') into buf, resets the internal buffer,
// and returns true. Returns false on all other calls.
bool hal_uart_readline(char* buf, size_t maxlen) {
    static char ibuf[64];
    static size_t pos = 0;

    while (piSerial.available()) {
        char c = (char)piSerial.read();
        if (c == '\n') {
            ibuf[pos] = '\0';
            strncpy(buf, ibuf, maxlen);
            buf[maxlen - 1] = '\0';
            pos = 0;
            return true;
        }
        // Silently drop bytes that would overflow; keep reading so '\n' still
        // flushes the internal buffer correctly.
        if (pos < sizeof(ibuf) - 1) {
            ibuf[pos++] = c;
        }
    }
    return false;
}
