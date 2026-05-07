# Krish Sahni Lab Notebook
 
**Project:** ECE 445 Smart Mirror Hand Tracking / Career Match System
**Team:** Keenan Peris, Krish Sahni, Connor Tan — Team 97
**TA:** Argyrios Gerogiannis | **Professor:** Yang Zhao
 
---
 
**Notebook status:** This digital notebook was initialized on 2026-05-06. All entries dated before 2026-05-06 are retrospective reconstructions derived from the repository commit history, source files, the final report, and shared project context. They are written to document the engineering record honestly; the commit history (`git log --all --format="%ad %H %s" --date=short`) remains the timestamped source of truth for when code changes were made.
 
**Repository evidence used:**
- Git commit history from 2026-03-10 through 2026-05-06.
- Source files in `MCU/`, `hand_tracking/`, `VL53L3CX_rasppi/`, and `hand_tracking/UI_Cursor/`.
- Project handoff notes in `LLM_PROJECT_HANDOFF.md`.
- MCU design documentation in `MCU/CLAUDE.md`.
- System diagrams in `notebooks/connor/`.
- Final report (ECE 445, May 2026).
**Collaboration note:** Connor Tan authored the database, face-matching, and most UI subsystems. This notebook covers work where commits were authored by Krish Sahni or where changes touched MCU firmware, UART, ToF, LED, and full-system integration. Hardware design (schematic, PCB placement) was individual work by Krish and is recorded in the pre-Git entries below. Shared integration commits are included where they affect the MCU/Pi interface.
 
---
 
## Figures
 
[Figure 1. System block diagram](block_diagram.png)

[Figure 2. Two-way mirror optical principle](optical_principle.png)

[Figure 3. Power distribution chain (STM32 PCB)](power_circuit.png)

[Figure 4. STM32F401 core schematic (decoupling, reset, boot, SWD, USB)](stm32_core_schematic.png)

[Figure 5. System finite state machine](fsm.png)

[Figure 6. Three-screen UI flow (career selection → matching → profile display)](3_screen_ui_flow.png)

[Figure 7. Routed PCB layout](routed_pcb_layout.png)

[Figure 8. UART integration test terminal log](uart_integration_terminal_log.png)

[Figure 9. Full STM32F401 schematic](full_schematic.png)

[Figure 10. Software architecture overview](../connor/ece445_software_architecture.png)

[Figure 11. Face matching subsystem diagram](../connor/software_face_matching_diagram_simplified_v3.png)

[Figure 12. Hand cursor UI subsystem diagram](../connor/software_cursor_ui_diagram_fixed_v3.png)

[Figure 13. Database schema](../connor/database_schema.png)
 
---
 
## Bibliographic References
 
1. **STM32F401xB/xC Datasheet**, STMicroelectronics, 2023. Used for decoupling requirements, core regulator VCAP, brown-out threshold selection, USB OTG_FS, and SWD interface design.
2. **VL53L3CX Datasheet and Application Notes**, STMicroelectronics, 2022. Local references: `VL53L3CX_rasppi/doc/UM2778.pdf`, `VL53L3CX_rasppi/doc/AN5561.pdf`. Used for I2C pull-up sizing, XSHUT control, and Pi-side C SDK integration.
3. **AP2112 600 mA CMOS LDO Regulator Datasheet**, Diodes Incorporated, 2022. Used for LDO output capacitor sizing and current limit verification.
4. **USBLC6-2SC6 Datasheet**, STMicroelectronics, 2014. Used for ESD protection design on USB D+/D− lines.
5. **CX2016SA Crystal Datasheet**, Kyocera AVX, 2025. Used for HSE crystal load capacitor calculation.
6. **Arduino Serial / SoftwareSerial / FastLED documentation** — used for MCU firmware development in `MCU/hal.cpp` and `MCU/MCU.ino`.
7. **pyserial** — UART communication between Raspberry Pi and Arduino/STM32; used in `MCU/uart_bridge.py` and `hand_tracking/live_match_demo.py`.
8. **MediaPipe Hand Landmark Model documentation** — used for index-fingertip cursor tracking in `hand_tracking/UI_Cursor/hand_tracker.py`.
9. **InsightFace / buffalo_sc ONNX model** — used for face embedding and identity matching in `hand_tracking/matching/embedder.py`.
10. **OpenCV (cv2)** — camera capture, frame rotation, image drawing, and display window management throughout `hand_tracking/`.
11. **SQLite / Python sqlite3** — local profile and face-embedding database in `hand_tracking/database/`.
---
 
## Pre-Git: System Design and Schematic Work
 
**Date:** Early Spring 2026 (approximately 2026-01-29 through 2026-03-09)
 
**Objective:** Define the system architecture, draw the block diagram, write the project requirements, and complete the full STM32F401 PCB schematic design before the repository was created.
 
**Record:**
 
The primary individual engineering contribution in this phase was the full STM32F401 schematic design. This included:
 
- **Power regulation subcircuit:** AP2112K-3.3 LDO from USB-C VBUS, with a Schottky diode for reverse-polarity protection and a USBLC6-2SC6 for ESD protection on the USB data pair. Bulk capacitor (4.7 µF) at the LDO output; 100 nF ceramic decoupling at every VDD pin of the STM32, oriented for the shortest return path to the ground plane. A 2.2 µF capacitor on the VCAP pin for the STM32 internal core regulator, per the datasheet recommendation. See Figure 3.
- **HSE crystal network:** 25 MHz Kyocera CX2016SA crystal on OSC_IN/OSC_OUT, with two 10 pF load capacitors and a guard ring to minimize stray capacitance. The HSE is required for generating the precise 48 MHz USB clock via the PLL.
- **Reset and boot configuration:** 10 kΩ pull-up on NRST with 100 nF RC filter for clean power-on reset. BOOT0 held low through a 10 kΩ resistor for normal flash-boot operation. Manual reset button for development. Boot-mode pull-up accessible for DFU activation if needed.
- **SWD programming header:** SWDIO, SWCLK, GND, and 3.3 V exposed for ST-Link access. Placed in an open board area for programmer clip-on access.
- **USB OTG_FS interface:** D+/D− differential pair routed to the USB-C receptacle as a secondary programming path (DFU bootloader). Controlled-impedance differential routing with matched trace lengths.
- **I2C ToF interface:** SDA/SCL with 5.1 kΩ pull-ups to 3.3 V per the VL53L3CX datasheet. Additional GPIO lines for XSHUT shutdown and INT interrupt. See Figure 9.
- **Brown-out detector configuration:** Enabled at the 2.9 V threshold to prevent flash corruption during undervoltage events. This threshold later triggered during bench testing when LED switching caused transient dips on the 3.3 V rail.
**Design decision — LDO over switching regulator:** Total steady-state load on the 3.3 V rail (STM32F401, ToF sensor, LED logic) is well under 300 mA, comfortably inside the AP2112K's 600 mA rating. An LDO was simpler to route, avoids switching noise near the oscillator, and requires fewer external components. The tradeoff is slightly higher thermal dissipation, which was not a concern at this current level.
 
**Design decision — STM32 as brain, Pi as worker:** The perception tasks (MediaPipe, InsightFace, OpenCV) are computationally heavy and require a Linux Python environment. The control tasks (ToF polling, FSM, UART, LED) require deterministic sub-millisecond response. Running both on one processor would either starve the control loop or cap the perception pipeline. The partition also isolates faults: a Python crash on the Pi cannot lock up the state machine.
 
**Design decision — UART over SPI/I2C for Pi-MCU link:** SPI's master/slave model is poorly suited to the bidirectional event-driven traffic in this system. Linux user-space I2C-slave support on the Pi is poor. UART is natively supported on both sides, requires only two signal lines, and the actual bandwidth needed (single-byte command events) is extremely low. Image data is never sent over the link.
 
I also authored the system block diagram (Figure 1) and wrote the project high-level requirements:
1. Detect user presence within 3 seconds and activate the display.
2. Match user to a professional from the database and display the profile.
3. Function as a reflective mirror when inactive; transition to display when user detected.
4. Present legible professional profile (name, image, role, biography) while maintaining the mirror illusion.
**PCB component placement:** After schematic completion, I performed the initial component placement on the PCB, grouping decoupling capacitors near their VDD pins, placing the crystal immediately adjacent to OSC_IN/OSC_OUT, and positioning connectors on board edges for cable access. Routing was completed by a teammate. See Figure 7.
 
**Evidence:** Project proposal, system block diagram (Figure 1), full schematic (Figure 9). No git commits; this work predates the repository.
 
---
 
## 2026-03-10 — Repository Init + MCU LED Stub + UI UART Scaffolding
 
**Objective:** Establish the repository and prove that the MCU development environment could compile and load firmware; scaffold the UART data path in the hand-tracking UI module in preparation for Pi-MCU integration.
 
**Record:**
- Created `MCU/MCU.ino` with an Arduino LED blink stub as the first MCU firmware entry point. This confirmed that the toolchain compiled, flashed, and ran, and that a visible actuator could be driven — the minimum proof of hardware bring-up before any sensor or UART work.
- First commit to `hand_tracking/UI_Cursor/`: added `send_data.py` (75 lines) as a UART data-send helper for passing hand-cursor events to downstream consumers; added `hand_landmarker.task` binary model file; extended `main.py` to use the send-data path.
**Design note — why UART scaffolding before MCU firmware was functional:** The Pi-MCU split and the command protocol were agreed on as a system architecture decision before code existed. Adding the UART send path to the UI at this stage was deliberate scaffolding: it established where the protocol boundary would live and allowed the Pi-side UI and the MCU firmware to be developed in parallel against a known interface, with an Arduino as the MCU stand-in. This is the same pattern used later when UART integration was tested with `uart_bridge.py` before the custom PCB was available.
 
**Evidence:** `2d6f52a5b7b2d07b14b66dc0e4c270a7aa343b0b` (arduino led)
 
---
 
## 2026-04-05 – 2026-04-06 — Progress Demo: Pi Bring-up and Display Formatting
 
**Objective:** Get the live demo running on Raspberry Pi for the progress demo milestone; fix display formatting for the portrait mirror layout.
 
**Record:**
- `cd36e5bb` — refactored formatting in `live_match_demo.py`, `UI_Cursor/main.py`, `UI_Cursor/send_data.py`, and `UI_Cursor/user_interface.py` (+93 lines, -58 lines). Added `UI_Cursor/CLAUDE.md` design context document.
- `d577664a` — "Progress Demo version; works on pi" — further revisions to get the pipeline running on the Pi's OpenCV stack and displaying correctly in portrait orientation.
**Pi bring-up issues encountered:** The two main problems when moving from Mac to Pi were the camera backend and display orientation. On macOS, OpenCV uses `CAP_AVFOUNDATION` for webcam access; on Pi/Linux it uses the V4L2 backend. The Pi also had different default capture resolution behavior. Display orientation was the second issue: the mirror is portrait (9:16), but the webcam frame is landscape, requiring explicit frame rotation and coordinate remapping so that UI elements and the hand cursor lined up correctly with what the user saw on screen. A normal laptop UI layout was not automatically appropriate for the physical mirror. The `WINDOW_OUTPUT_ROTATION = cv2.ROTATE_90_COUNTERCLOCKWISE` approach was established at this point.
 
**Evidence:** `cd36e5bbd9cecd2c2387b3252ffe9719b746f4a3`, `d577664a00b9f39deb149c0ffc4a3121e951ed27`
 
---
 
## 2026-04-19 — MCU FSM Phase 1 + Phase 2
 
**Objective:** Design and implement the Arduino finite-state machine for the MCU subsystem; build the HAL abstraction layer; establish LED behavior for state transitions.
 
**Record:**
- `e4cef144` — "MCU Setup": initial `MCU/MCU.ino`, establishing the two-function Arduino entry point (`setup()` / `loop()`).
- `6c1d9cb7` — "phase 1": created `MCU/hal.h` and `MCU/hal.cpp` defining the HAL interface: `hal_tof_init`, `hal_tof_read_mm`, `hal_led_set`, `hal_uart_send`, `hal_uart_readline`. All hardware access is encapsulated in the HAL so that an Arduino → STM32 migration requires only `hal.cpp` to change, not the FSM logic.
- `db88bcce` — "phase 2 written, yet to test": created `MCU/fsm.h` and `MCU/fsm.cpp` (92 lines) with the four-state FSM. `MCU.ino` reduced to a thin wrapper calling `fsm_init()` / `fsm_tick()`.
- `b79c891d` — LED polarity adjustment (inverted wiring: LED on when `hal_led_set(false)`).
- `456aff8d`, `4272736c` — "led on for init to idle": added LED activation during IDLE→SCANNING transition.
- `3a933f12` — small cleanup.
**FSM design (see Figure 5):**
 
| State | Behavior | Transition |
|---|---|---|
| IDLE | Poll ToF at 100 ms; if distance < 500 mm, send `PRESENCE\n`, enter SCANNING | ToF below threshold |
| SCANNING | LED on; 15 s timeout | `MATCH\n` or `NO_MATCH\n` from Pi |
| MATCH_PENDING | 10 s wait, then LED on; send `RESET\n` | Timer expiry |
| MATCH_DISPLAYED | 10 s display timer | Timer expiry → IDLE |
 
**HAL ToF stub:** The physical VL53L0X was not yet connected at this stage. `hal_tof_read_mm()` used a pushbutton on `HAL_PRESENCE_BTN_PIN` wired to GND via `INPUT_PULLUP` — pressed = 200 mm (presence), released = 2000 mm (empty). This allowed FSM logic to be fully tested without sensor hardware, which is the right approach: verify the state machine behavior independently before introducing sensor noise.
 
**UART:** `SoftwareSerial` on pins 10 (RX) / 11 (TX) at 9600 baud, keeping the hardware UART pins 0/1 free for USB uploads during development.
 
**LED:** WS2812B strip via FastLED. Inverted wiring (noted in code comment) means `hal_led_set(true)` drives the LED off. This is a physical wiring detail that must be noted in the notebook because it is non-obvious from the firmware alone and will cause confusion during future debugging if not recorded.
 
**Design decision — HAL/FSM split:** Keeping hardware access in `hal.cpp` means the FSM code is free of direct register calls and easier to test. The intended migration path was Arduino (for rapid iteration) → STM32F401 (final PCB). With the HAL boundary in place, this migration only required rewriting `hal.cpp`; `fsm.cpp` was unchanged.
 
**Evidence:** `e4cef144`, `6c1d9cb7`, `db88bcce`, `2e6402c5`, `b79c891d`, `456aff8d`, `4272736c`, `3a933f12`
 
---
 
## 2026-04-20 — UART Integration + Full-Screen UI + LED Behavior
 
**Objective:** Wire the Pi-side UART bridge to the MCU FSM; integrate UART event handling into the live match demo loop; test full-screen display; iterate on LED strip behavior.
 
**Record:**
- `8f5d07e3` — created `MCU/uart_bridge.py` (41 lines): standalone Pi-side script simulating face-recognition responses. Listens on `/dev/serial0` at 9600 baud; on receiving `PRESENCE`, sleeps 3 s, sends `MATCH\n`.
- `b87a6235` — baud rate adjustment and documentation update.
- `26ec47ce` — added full-screen display mode to `live_match_demo.py`.
- `751b5c69` — "testing uart integration": major expansion of `live_match_demo.py` (+137 lines net), integrating UART read/write into the camera loop.
- `68f2d695` — "integrating led strip": extended `MCU/hal.cpp` and `MCU/hal.h` with FastLED WS2812B definitions and `hal_led_set()` implementation.
- `578d0977` — "switch led behaviour": adjusted `hal_led_set()` active-low polarity.
- `6f463334` — "adding a 10 sec delay from match to led on": MATCH_PENDING tick waits 10 s before activating LED, so the physical LED feedback is synchronized with the profile display rather than firing immediately when MATCH is received.
- `c6bda78c` — "send reset before 10 sec wait": moved `hal_uart_send("RESET\n")` to fire at MATCH_PENDING entry, before the 10 s LED delay. This ensures the Pi is signaled to return to idle even if the LED timing is adjusted later.
**UART debugging — issues encountered:** The main issues during the debugging commits were:
1. **Path mismatch:** The serial device path on the Pi differed from development expectations (`/dev/serial0` vs `/dev/ttyUSB0` vs `/dev/ttyACM0` depending on whether a hardware UART or USB-serial adapter was used). This caused the bridge to silently fail to open the port.
2. **SoftwareSerial timing sensitivity:** At 9600 baud, `SoftwareSerial` on the Arduino is workable but more sensitive to interrupt latency than hardware UART. Short bursts of FastLED strip updates (which disable interrupts briefly) could cause dropped bytes. This informed the decision to keep LED updates and UART reads in carefully sequenced sections of the loop.
3. **Line ending handling:** `PRESENCE\n` vs `PRESENCE` — the Pi-side bridge had to strip `\r\n` consistently before string comparison, otherwise state transitions silently failed.
**Test setup:** Arduino Uno connected to the Pi via a USB-to-serial adapter (`/dev/ttyUSB0`). This is the same Arduino-as-STM32-stand-in approach that was established from the start. The UART protocol was identical to what the final STM32 firmware would use, so the substitution was transparent to the Pi-side software.
 
**See Figure 8** for a representative terminal log captured during this testing phase.
 
**Evidence:** `8f5d07e3`, `b87a6235`, `26ec47ce`, `751b5c69`, `09df7399`, `c2508a34`, `c6c95e8e`, `2a88b88b`, `68f2d695`, `578d0977`, `6f463334`, `c6bda78c`
 
---
 
## 2026-04-23 — VL53L3CX Arduino Prototype + Pi SDK Submodule
 
**Objective:** Write initial Arduino sketch for VL53L3CX ToF sensor readout; add the STMicroelectronics Pi C library as a git submodule.
 
**Record:**
- `8e9774f7` — "init tof code; yet to test": created `MCU/VL53/VL53.ino` (133 lines) — Arduino sketch for reading VL53L3CX via I2C. Marked untested.
- `00d01685` — revised the sketch, iterating on sensor initialization and read sequence.
- `bcd5f90b` — "adding tof sensor repo": added `VL53L3CX_rasppi` as a git submodule — the STMicroelectronics C SDK for VL53L3CX on Linux/Raspberry Pi.
**Design decision — VL53L3CX over VL53L0X:** The VL53L3CX is a longer-range ToF sensor than the VL53L0X. For a mirror installation where a user may stand 1.5–3.5 m away, the VL53L3CX's extended range is necessary. The VL53L0X is rated to roughly 2 m under good conditions; the VL53L3CX extends to 3 m+ with better reliability across ambient light conditions. The presence threshold used in the final system is 500 mm in the MCU firmware and on the Pi subprocess side, but the sensor's full range is used for the interaction zone definition (1.5–3.5 m) described in the final report.
 
**Design decision — Arduino sketch vs. Pi C SDK:** The Arduino sketch was written first as a bench test to confirm I2C communication with the sensor before committing to the Pi C SDK integration. The Pi-side approach (compiled C binary consumed as a subprocess) was the intended final deployment path; the Arduino sketch served as a hardware validation step.
 
**Evidence:** `8e9774f7`, `00d01685`, `bcd5f90b`
 
---
 
## 2026-04-24 — ToF Integration into Pi Pipeline + Latency Reduction
 
**Objective:** Integrate VL53L3CX into the Python live-match pipeline; debug the sensor path on Pi; reduce end-to-end latency.
 
**Record:**
- `faede84c` — "trying to integrate tof sensor": added VL53L3CX subprocess-based reader to `live_match_demo.py` (+73 lines). Spawns `VL53L3CX_rasppi/bin/main` as a child process; reads distance lines from stdout.
- `1cb750a6` — "fixing error".
- `b53b98f1` — "change path for rpi": updated binary path to `/home/ece445/Desktop/ECE445_handtracking/VL53L3CX_rasppi/bin/main`.
- `e82a91cc` — "debugging tof integration": added diagnostic output.
- `31fa1287` — "timed logging; clean end": added per-stage timing instrumentation and clean shutdown.
- `8014e446` — "trying to reduce latency": minor edit to `VL53L3CX_rasppi/example/main.c` to tune the C sensor read loop.
**Design decision — subprocess / stdout pipe approach:** The STMicroelectronics VL53L3CX SDK is a C library with no Python bindings. The choices were: (a) write Python ctypes bindings, (b) compile the C example and consume its output as a subprocess, or (c) rewrite sensor readout in Python using lower-level I2C access. Option (b) was chosen because the compiled binary already existed from the SDK examples and produced clean line-delimited distance output. This minimized the risk of introducing bugs in low-level sensor code and matched the pragmatic approach of the project.
 
**Presence filtering logic (from final code):**
 
```
presence = distance < TOF_PRESENCE_THRESHOLD_MM (500)
           AND signal >= TOF_MIN_SIGNAL_MCPS (0.05)
           AND sigma < TOF_MAX_SIGMA_MM (50.0)
```
 
Distance alone is not sufficient because ToF sensors can return technically valid readings at low confidence. The signal threshold filters weak reflections; the sigma threshold filters high-uncertainty distance estimates. This reduces false triggers from reflective surfaces, ambient IR, or the enclosure itself.
 
**Evidence:** `faede84c`, `1cb750a6`, `b53b98f1`, `e82a91cc`, `31fa1287`, `8014e446`
 
---
 
## 2026-04-25 — VL53L3CX Compiled Binaries + ToF Refinement + Performance Overhaul
 
**Objective:** Commit compiled VL53L3CX binaries for Pi deployment; refine ToF presence logic; improve CV pipeline performance with worker threading and caching.
 
**Record:**
- `86853f7e` — "tof sensor compiled binaries": added ARM binaries compiled for Raspberry Pi (`libVL53L3CX_rasppi.a` static library and `main` executable to `VL53L3CX_rasppi/bin/`).
- `1e207edf` — "improving tof, test 1": improved ToF reading parsing and presence state logic.
- `ee69e52d` — "embedding worker thread for efficiency": moved InsightFace embedding/matching into a dedicated worker thread using `queue.Queue`, decoupling embedding latency from the camera frame loop.
- `541868d0` — "better cv pipeline and cache": added embedding result caching; tweaked frame processing.
- `613349f9` — "better database performance; yet to test": significant rework of `db_operations.py` — connection reuse, query caching, batch fetch replacing N+1 query loop, index definitions in `db_init.py`.
- `ab5ae3db` — "reliability and memory changes": reliability fixes to `hand_tracker.py`, `live_match_demo.py`, and `embedder.py`; addressed memory leak patterns in long-running loop.
**Why the worker thread was added:** Frame rate on the Pi without threading was approximately 4–6 fps during the matching state, because InsightFace embedding is CPU-heavy and was blocking the main camera loop. Moving embedding to a worker thread with `queue.Queue` allowed the UI loop to continue drawing frames, updating cursor state, and processing UART/ToF messages while the embedding ran concurrently. After threading, the UI remained at ~10 fps (the Pi's practical cap for this pipeline) even during active matching.
 
**N+1 query fix:** The original implementation issued one SQL query per candidate during the match ranking step. With a database of N professionals, a single match request produced N+1 queries. This was replaced with a single batch fetch joined to the ranked results — a standard relational database optimization that eliminated observable per-match latency on the Pi's slower storage.
 
**Per-frame `cv2.imread` fix:** The original render loop called `cv2.imread` on the profile headshot image once per frame during profile display. This caused visible UI hitches because disk reads are not free. The fix was a module-level `_image_cache` dict keyed by path, so each image is read from disk exactly once.
 
**Evidence:** `86853f7e`, `1e207edf`, `ee69e52d`, `541868d0`, `613349f9`, `ab5ae3db`
 
---
 
## 2026-04-26 — UART Logging Fixes + Professional Database Population + PR Merges
 
**Objective:** Fix UART logging errors in the live match loop; populate the database with real professional images; merge Connor's parallel branches.
 
**Record:**
- `28d72b85` — "testing logging change; should log now": added UART-related log output to `live_match_demo.py`.
- `12ca5024` — "uart logging error fix": fixed a logging call causing a runtime error. Root cause: `absl` (pulled in by MediaPipe) hijacks the root logger before `logging.basicConfig` runs, silently swallowing all output. Fix required passing `force=True` to `basicConfig` so it runs after `absl` has already attached its handlers.
- `4203c818` — "testing new database stuff": added 6 real professional JPEG images (Aaron Fluitt, Andrew Conrad, Colin Lualdi, Kristina Meier, Nathan Arnold, Ujaan Purakayastha) to `hand_tracking/database/images/`; created `populate_real_professionals.py` to enroll them.
- `6fb500f0` — added `debug_db.py` (83 lines) for database inspection; finalized population script.
- Merged PRs #13, #14, #15 from Connor's branches.
**Professional image enrollment:** Images were obtained manually and added to the repository. One image per professional was used for the initial enrollment. The enrollment script runs InsightFace offline on each image and writes the embedding into `face_embeddings` under the `buffalo_sc` model name. A diagnostic issue discovered during this phase: image paths stored in the database did not match the actual file locations on disk, causing several enrollments to silently fail. `debug_db.py` was written specifically to list professionals whose `image_path` does not resolve, making this class of bug immediately visible. After the path fix, the script returned an empty list and all enrollments succeeded.
 
**`absl` logger hijack (detail):** MediaPipe imports `absl-py` as a dependency. `absl` calls `logging.basicConfig` internally during import, attaching its own handlers to the root logger. If the project code then calls `logging.basicConfig` without `force=True`, Python silently ignores it (the standard library skips `basicConfig` if handlers are already attached). The symptom was that all log output disappeared. Fix: `logging.basicConfig(..., force=True)` ensures our configuration takes effect regardless of import order.
 
**Evidence:** `28d72b85`, `12ca5024`, `4203c818`, `6fb500f0`, `7fef2aa3`, `35701938`, `17bfbf7f`
 
---
 
## 2026-04-27 — Camera-Based Presence Detection + Final Performance Pass
 
**Objective:** Integrate camera-based distance estimation as a second presence-detection modality; apply final performance improvements to the main demo loop.
 
**Record:**
- `d04d9c53` — "camera dist integration on branch main": major restructuring of `live_match_demo.py` (+354 lines, -188 lines) and `matching/embedder.py`. Introduced camera-based distance estimation alongside the VL53L3CX subprocess path.
- `0b6fef62` — "codex changes for improved performance": applied Codex-suggested performance changes.
- `c3efd4a8` — "mirror_db_update": updated `hand_tracking/database/mirror.db`.
**Camera-based distance estimation — approach and rationale:**
 
The approach uses face bounding-box pixel width as a proxy for distance. As a user moves farther from the camera, their apparent face width in pixels decreases proportionally. The formula used:
 
```
distance_cm = reference_distance_cm × reference_face_width_px / observed_face_width_px
```
 
With `reference_distance_cm = 60` and `reference_face_width_px = 220` as empirically measured constants. Presence is confirmed when the estimated distance falls within the interaction zone.
 
This was added because the VL53L3CX, despite signal and sigma filtering, produced false positives in certain lighting conditions and with certain enclosure geometries. The camera path serves as a complementary check: it requires an actual face to be visible, which is a stronger presence signal than a raw distance reading.
 
**Arbitration between the two presence signals:** The two paths run sequentially in the main loop. The first to return a confirmed presence event activates the system. This avoids requiring both sensors to agree simultaneously (which would make the system harder to trigger) while still reducing false positives compared to either sensor alone. No metric distance accuracy is needed from the camera path — raw bounding box pixel width thresholding is sufficient because the goal is binary presence detection, not precise ranging.
 
**Design note:** Metric accuracy from the camera would require known focal length and known face size, which varies across users. The pixel-width threshold approach sidesteps both calibration requirements by using a single empirically tuned threshold. If the threshold is wrong for a given deployment, it is adjusted by measuring the pixel width of a face at the desired activation distance.
 
**Evidence:** `d04d9c53`, `0b6fef62`, `c3efd4a8`
 
---
 
## 2026-05-06 — Camera Distance Branch (WIP) + Notebook Initialization
 
**Objective:** Continue camera-based presence detection work on a dedicated branch; initialize this lab notebook.
 
**Record:**
- `eb10522b`, `15446c9c` — stash commits on `cam_distance` branch. Work in progress: merging the camera-bbox presence detection into main, integrating it with the existing state machine and UART signaling, and verifying parallel operation with the ToF-based path.
- Initialized this digital Markdown notebook under `notebooks/krish/README.md`.
**PCB brown-out finding (recorded here for completeness):** During bench testing of the assembled custom STM32F401 PCB, the brown-out reset triggered intermittently during normal operation. An oscilloscope probe on the 3.3 V rail at the moment of reset showed a transient dip below the 2.9 V brown-out threshold coincident with the LED-on switching edge. Root cause: the bulk capacitance at the LDO output and local decoupling were sized for steady-state operation but insufficient to absorb the load step from LED switching. Because the project schedule did not include a second PCB spin, the Arduino Uno used for UART integration testing was promoted to the final demonstration controller. The UART command protocol was unchanged; the substitution was transparent to the Pi-side software. The fix for a second board iteration is straightforward: increase the bulk output capacitor on the AP2112K and add additional local decoupling near high-current switching loads.
 
**Current project status:**
- Working: MCU FSM, UART protocol, ToF integration, LED strip control, hand cursor UI, face embedding and matching, profile database, live demo state flow, camera-based presence detection.
- Open: final integration of camera presence detection branch into main; full end-to-end Pi test with all subsystems active.
- Known hardware issue: STM32 PCB brown-out under LED switching load; addressed by Arduino stand-in for final demo.
**Evidence:** `eb10522b`, `15446c9c`
 
---
 
## Key Equations
 
**ToF distance measurement (Eq. 2.4 in final report):**
 
```
d = (c × t) / 2
```
 
where d is measured distance, c is the speed of light, and t is round-trip pulse time.
 
**Face confidence gate before embedding (Eq. 2.5):**
 
```
C = 0.4·P_d + 0.3·(A_face / A_frame) + 0.3·V_laplacian
```
 
where P_d is detector probability, A_face/A_frame is face-to-frame area ratio, and V_laplacian is a sharpness metric. Threshold: C > 0.65 required before passing frame to InsightFace.
 
**Cosine similarity for face matching (Eq. 2.6):**
 
```
sim(a, b) = (a · b) / (‖a‖ · ‖b‖)
```
 
Measures angle between embedding vectors; approaches 1 for identical faces. Standard comparison metric for normalized embedding vectors.
 
**Camera-based distance estimation:**
 
```
distance_cm = reference_distance_cm × reference_face_width_px / observed_face_width_px
```
 
Empirical constants: `reference_distance_cm = 60`, `reference_face_width_px = 220`.