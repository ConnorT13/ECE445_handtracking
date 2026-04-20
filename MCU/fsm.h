#ifndef FSM_H
#define FSM_H

// Initializes the FSM to IDLE state.
void fsm_init();

// Advances the FSM by one tick; call every loop iteration.
void fsm_tick();

#endif // FSM_H
