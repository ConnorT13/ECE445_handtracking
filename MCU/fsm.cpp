#include "fsm.h"
#include "hal.h"
#include <Arduino.h>

enum class State { IDLE, SCANNING, MATCH_DISPLAYED };

static State state;
static uint32_t stateEnteredAt;  // millis() when the current state was entered
static constexpr uint32_t SCANNING_TIMEOUT_MS = 15000UL;
static constexpr uint32_t MATCH_FADE_DURATION_MS = 1500UL;

// Transition helper: prints debug line and records entry time.
static void enter(State next, const char* label) {
    const char* from = (state == State::IDLE)             ? "IDLE"
                     : (state == State::SCANNING)         ? "SCANNING"
                                                          : "MATCH_DISPLAYED";
    Serial.print(F("FSM: "));
    Serial.print(from);
    Serial.print(F(" -> "));
    Serial.println(label);
    state = next;
    stateEnteredAt = millis();
}

// ── IDLE ─────────────────────────────────────────────────────────────────────

static uint32_t lastTofAt = 0;

static void enter_scanning_from_idle(bool send_presence) {
    enter(State::SCANNING, "SCANNING");
    hal_led_set(true);
    if (send_presence) hal_uart_send("PRESENCE\n");
}

static void tick_idle() {
    uint32_t now = millis();
    if (now - lastTofAt < 100) return;
    lastTofAt = now;

    if (hal_tof_read_mm() < 500) {
        enter_scanning_from_idle(true);  // MCU detected — notify Pi
        return;
    }

    // Pi's own ToF may have triggered first and sent us PRESENCE.
    char buf[32];
    if (hal_uart_readline(buf, sizeof(buf)) && strcmp(buf, "PRESENCE") == 0) {
        enter_scanning_from_idle(false);  // Pi already knows — just start SCANNING
    }
}

// ── SCANNING ─────────────────────────────────────────────────────────────────

static void leave_scanning_idle() {
    hal_uart_send("RESET\n");
    hal_led_set(false);
    enter(State::IDLE, "IDLE");
}

static void tick_scanning() {
    // 15-second timeout
    if (millis() - stateEnteredAt >= SCANNING_TIMEOUT_MS) {
        leave_scanning_idle();
        return;
    }

    char buf[32];
    if (!hal_uart_readline(buf, sizeof(buf))) return;

    if (strcmp(buf, "MATCH") == 0) {
        enter(State::MATCH_DISPLAYED, "MATCH_DISPLAYED");
    } else if (strcmp(buf, "NO_MATCH") == 0) {
        leave_scanning_idle();
    } else if (strcmp(buf, "RESET") == 0) {
        leave_scanning_idle();
    }
}

// ── MATCH_DISPLAYED ──────────────────────────────────────────────────────────

static void tick_match_displayed() {
    uint32_t elapsed = millis() - stateEnteredAt;
    if (elapsed < MATCH_FADE_DURATION_MS) {
        uint32_t remaining = MATCH_FADE_DURATION_MS - elapsed;
        uint8_t level = (uint8_t)((remaining * HAL_LED_ON_BRIGHTNESS) / MATCH_FADE_DURATION_MS);
        hal_led_set_level(level);
    } else {
        hal_led_set(false);
    }

    char buf[32];
    if (hal_uart_readline(buf, sizeof(buf)) && strcmp(buf, "RESET") == 0) {
        enter(State::IDLE, "IDLE");
    }
}

// ── Public API ────────────────────────────────────────────────────────────────

void fsm_init() {
    state = State::IDLE;
    stateEnteredAt = millis();
    lastTofAt = 0;
    hal_led_set(false);
    Serial.println(F("FSM: init -> IDLE"));
}

void fsm_tick() {
    switch (state) {
        case State::IDLE:            tick_idle();            break;
        case State::SCANNING:        tick_scanning();        break;
        case State::MATCH_DISPLAYED: tick_match_displayed(); break;
    }
}
