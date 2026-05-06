# Connor Tan Lab Notebook

Project: ECE 445 Smart Mirror Hand Tracking / Career Match System

Notebook status: This digital notebook was initialized on 2026-01-29. Entries before 2026-05-06 are retrospective reconstructions from repository commits, source files, diagrams, and remembered design work. They are written to document the engineering record honestly; the commit history remains the timestamped source of truth for when code changes were made.

Repository evidence used:
- Pre-Git meeting notes provided from 2026-01-29, 2026-02-10, 2026-02-13, and 2026-03-04.
- Git commit history from 2026-03-10 through 2026-04-27.
- Source files in `hand_tracking/`, `MCU/`, and `VL53L3CX_rasppi/`.
- System diagrams in `docs/`.
- Project handoff notes in `LLM_PROJECT_HANDOFF.md`.

Collaboration note: Some integration work was done with Krish Sahni, especially during Raspberry Pi, MCU/UART, ToF sensor, LED behavior, and full-system demo testing. These entries describe my notebook record of the work and include collaborator context where relevant.

Git authorship note: Early database, matching, and UI commits were mostly authored by Connor Tan in Git. Many MCU, UART, ToF, LED, and late integration commits were authored by Krish Sahni in Git, with Connor-authored commits mixed into the UI/database portions. Where entries describe Git-authored work by Krish, they are included because the work affected the shared integrated system and my design/testing record, not to claim sole authorship.

## Figures
Figure 1. Project Diagram: [ECE445ProjectDiagram.pdf](ECE 445 Project Diagram.pdf)

Figure 2. Software Architecture: [ece445_software_architecture.png](ece445_software_architecture.png)

Figure 3. Database Schema: [database_schema.png](database_schema.png)

Figure 4. Face matching subsystem: [software_face_matching_diagram.png](software_face_matching_diagram_simplified_v3.png)

Figure 5. Hand cursor UI subsystem: [software_cursor_ui_diagram.png](software_cursor_ui_diagram_fixed_v3.png)


## Bibliographic References

1. OpenCV documentation, camera capture and image processing APIs, used for webcam input, frame transforms, drawing, and display.
2. MediaPipe hand tracking / hand landmark model documentation, used for the index-fingertip cursor and hover-selection interaction.
3. InsightFace model documentation and ONNX face-recognition model files, used for face embeddings and identity matching.
4. STMicroelectronics VL53L3CX documentation, including local references `VL53L3CX_rasppi/doc/UM2778.pdf` and `VL53L3CX_rasppi/doc/AN5561.pdf`, used for ToF sensor integration.
5. SQLite documentation, used for the local profile database and face-embedding storage.
6. Arduino serial and timing documentation, used for UART messaging and finite-state-machine timing.

## 2026-01-29

Objective: Discuss the initial smart mirror project idea with Professor Kwiat and determine whether it was a reasonable direction for ECE 445.

Record: Had the first project meeting with Professor Kwiat to discuss the mirror concept. The main idea was to build an interactive mirror-style installation that could detect when a user was present, display content through a partially reflective surface, and support a career-exploration interaction around quantum professionals.

Design notes: The early design questions were whether the mirror illusion would be convincing, what type of display would work behind the reflective film, how to sense a user standing in front of the mirror, and how much interaction could be done reliably in a public/demo setting.

Result: Project direction was considered worth pursuing, with the next step being to turn the concept into a more concrete sensing, display, and interaction architecture.

Evidence: Pre-Git meeting record provided by Connor.

## 2026-02-10

Objective: Meet with the TA to review early project feasibility and identify the highest-risk technical unknowns.

Record: Met with the TA and wrote down action items for the next week. The most important risks were presence detection, display/mirror feasibility, camera/frame-capture stability, face-detection frame rate, and making the system block diagram more specific.

TODO for next week:
- Build a proof of presence detection.
- Work on the display and check whether the mirror illusion works.
- Verify whether two-way film looks like a mirror in the intended setup.
- Determine whether Kinect can actually do stable frame capture.
- Measure or estimate FPS for face detection.
- Figure out how to build presence detection independently without relying on Kinect.
- Make the block diagram more specific.

Design notes: This meeting clarified that the project should not depend too heavily on Kinect unless the frame capture and latency were stable. It also made presence detection a standalone design problem rather than only a side effect of camera-based tracking.

Testing/debugging plan: Test the optical setup separately from the software stack. Test sensing separately from matching/UI. This separation should make it easier to identify whether future failures are due to mirror visibility, camera input, presence sensing, or software latency.

Result: Established near-term prototype tasks and identified presence detection and display feasibility as early critical risks.

Evidence: Pre-Git TA meeting notes provided by Connor.

## 2026-02-13

Objective: Meet with the machine shop to discuss the physical enclosure design.

Record: Met with the machine shop about the enclosure around the screen and mechanical support for the ToF sensor. The goal was to make sure the display, reflective surface, and sensor mounting could be physically integrated in a way that would survive demo use and keep the sensor aimed correctly.

Design notes: The ToF sensor needs a stable and repeatable mounting position because small shifts could change the detection area. The screen enclosure also affects the mirror illusion because the display, film, viewing angle, and ambient lighting all interact.

Result: Physical enclosure and ToF mounting became part of the project design constraints, not just finishing details.

Evidence: Pre-Git machine shop meeting record provided by Connor.

## 2026-03-04

Objective: Start UI prototyping before this repository became the main project record.

Record: Began working on the user interface in a separate private repository. This work preceded the public/current Git history in this repository. The UI direction was to create a mirror-friendly interaction that could be controlled without touching the screen.

Design notes: The UI needed to be readable through the mirror/display setup and usable from a distance. This pushed the design toward large targets, simple selection states, and eventually hand-tracking hover selection rather than mouse/keyboard interaction.

Result: UI work started before the first commits in this repository. Later UI work was moved into this repo and connected to the camera, database, matching, and display flow.

Evidence: Pre-current-repo private UI work record provided by Connor.

## 2026-03-10

Objective: Start the project repository and prove that the microcontroller side could drive a basic output.

Record: Created the initial repository. Krish authored the Arduino LED test commit. This was the first hardware bring-up step before the project had a complete software stack. The practical purpose was to confirm that the development environment could compile and load firmware and that a visible actuator could be controlled.

Design notes: I treated the LED as a stand-in for later user feedback hardware. The eventual mirror system needs visible state feedback for standby, scanning, match found, and reset states, so even a simple LED test was useful.

Result: Initial repository and Arduino LED baseline committed.

Evidence: commit `fb338a9` authored by Connor; commit `2d6f52a` authored by Krish.

## 2026-03-15

Objective: Build the first software foundation for the smart mirror: database storage and camera/UI prototype work.

Record: Added database code and updated the main camera script to support camera use across MacOS and Windows. Also saved additional testing code. The database work established that the mirror would store professional profiles locally instead of hardcoding all profile content in the UI.

Design notes: The project needs to display career/profile information after a match, so I began with a structured database layer. The database schema later grew to include professionals, tags, interaction logs, and face embeddings.

Testing/debugging: Verified that the code path could initialize and access the database and that camera access was possible on the development machines. Cross-platform camera APIs were a concern because development and deployment environments differed.

Evidence: commits `e57df0c` and `f4d1c73`.

## 2026-03-31

Objective: Complete the first version of the database.

Record: Wrote the database implementation for profile records. This included functions for adding and querying professionals and related profile data.

Design notes: A database is better than a flat file for this project because profile records have multiple related fields: name, title, organization, quantum area, bio text, image path, fun fact, video URL, and tags. Later matching also required storing one or more face embeddings per professional.

Result: Database layer committed as the basis for later UI and matching integration.

Evidence: commit `6608e06`.

## 2026-04-05

Objective: Add a smart mirror face matching demo and clarify deployment risks.

Record: Added a live smart mirror face-matching demo. The system flow at this point was: open a camera, capture a user image, compare that image against enrolled profiles, and display the best match. I also documented that Raspberry Pi deployment was not yet fully validated.

Design notes: The matching layer uses cosine similarity:

```text
similarity(A, B) = (A dot B) / (||A|| * ||B||)
```

This was selected because face embedding models output vectors where angular closeness is a standard way to compare identity similarity. See Figure 3 for the matching subsystem.

Testing/debugging: Matching was acceptable on the development machine, but there was a deployment concern: InsightFace may be too computationally heavy for responsive real-time operation on Raspberry Pi 4 without optimization.

Result: Smart mirror matching demo existed, with Pi performance risk noted.

Evidence: commits `5e2fa08` and `04f183c`; files `hand_tracking/live_match_demo.py`, `hand_tracking/matching/match.py`, and `LLM_PROJECT_HANDOFF.md`.

## 2026-04-06

Objective: Prepare a progress-demo version and test on Raspberry Pi.

Record: Krish authored the progress-demo commit that worked on the Pi. This moved the project closer to the intended kiosk/mirror setup rather than only running on a laptop. Some Pi bring-up and integration discussion was done with Krish as we worked toward getting the software stack running on the target hardware.

Design notes: Pi testing exposed the importance of avoiding assumptions tied to a Mac camera backend. The deployment path needed Linux camera capture and lower processing cost.

Result: Progress demo version committed and noted as working on Pi.

Evidence: commit `d577664`, authored by Krish.

## 2026-04-19

Objective: Set up MCU firmware and define the first state-machine behavior.

Record: Krish authored the MCU setup and early FSM phase commits. The microcontroller firmware was separated into `MCU.ino`, `fsm.cpp`, `fsm.h`, `hal.cpp`, and `hal.h`. This split kept hardware-specific code in the HAL and state behavior in the FSM.

Design notes: The intended hardware states were:

```text
IDLE -> SCANNING -> MATCH_PENDING -> MATCH_DISPLAYED -> IDLE
```

The MCU polls a ToF sensor, drives LED feedback, and communicates with the Raspberry Pi over UART. See Figure 5 for the firmware architecture.

Testing/debugging: Iterated on LED behavior several times because the output state needed to be visible and match the demo story. Several small commits adjusted when the LED turns on or off during initialization and idle/scanning transitions.

Result: MCU state-machine structure created by Krish and ready for UART integration testing by the team.

Evidence: commits `e4cef14`, `6c1d9cb`, `db88bcc`, `b79c891`, `456aff8`, `4272736`, and `3a933f1`, authored by Krish; files `MCU/MCU.ino`, `MCU/fsm.cpp`, `MCU/hal.cpp`, and `MCU/CLAUDE.md`.

## 2026-04-20

Objective: Integrate Pi-to-MCU UART communication, LED strip behavior, and mirror display layout.

Record: Worked with Krish on integration tasks including UART debugging, baud-rate testing, reset behavior, and connecting the Pi live demo with the MCU. Most MCU/UART/LED commits this day were authored by Krish. I authored UI/display-related commits that refined the mirror portrait layout, fit the UI to the mirror screen, and added Keenan into the database.

Design notes: UART protocol:

```text
MCU -> Pi: PRESENCE, RESET
Pi -> MCU: MATCH, NO_MATCH, PRESENCE
```

This protocol allows either the MCU ToF sensor or the Pi-side presence system to initiate the scan flow. `RESET` returns both sides to a known idle state.

Testing/debugging: UART was a major debugging target. Krish and I worked through serial behavior, reset timing, and the interaction between the Pi process and MCU firmware. Krish authored most of the serial, reset, and LED strip changes, while I worked on UI/display behavior and database/profile integration for the demo screen.

Result: Pi/MCU integration path established by the team, with Krish driving most MCU/UART/LED commits and me contributing display/UI/database changes.

Evidence: Connor-authored commits `8498ad3` and `e4a4a7d`; most other 2026-04-20 integration commits authored by Krish; files `MCU/fsm.cpp`, `MCU/hal.cpp`, `hand_tracking/live_match_demo.py`, and Figure 2.

## 2026-04-24

Objective: Integrate the VL53L3CX ToF sensor on the Raspberry Pi side and reduce latency.

Record: Krish authored the VL53L3CX Raspberry Pi sensor repository addition, integration fixes, Pi path updates, timed logging, and latency work. Krish and I worked together on parts of the physical integration and sensor/demo behavior because this work depended on the Pi setup, MCU state machine, and hardware wiring all agreeing.

Design notes: The Pi-side ToF reader runs the compiled VL53L3CX binary and parses distance readings. A reading counts as valid human presence only if it passes distance, signal, and sigma filters:

```text
distance < 500 mm
signal >= 0.05 Mcps
sigma < 50 mm
```

These filters reduce false triggers from noisy or low-confidence readings.

Testing/debugging: Main debug concerns were executable path correctness on the Pi, sensor process startup, serial coordination with the MCU, and whether presence detection triggered the correct state change. Collaboration with Krish was useful here because failures could come from either software assumptions or physical setup details.

Result: ToF integration was underway and instrumented with logging, with the Git commits authored by Krish.

Evidence: commits `bcd5f90`, `1cb750a`, `faede84`, `e82a91c`, `b53b98f`, `31fa128`, and `8014e44`, authored by Krish; files `VL53L3CX_rasppi/` and `hand_tracking/live_match_demo.py`.

## 2026-04-25

Objective: Improve ToF behavior, matching latency, computer-vision pipeline speed, database performance, and reliability.

Record: Krish authored the commits for compiling ToF binaries, improving ToF usage, adding an embedding worker thread, improving the CV pipeline and caching, optimizing database access, and making reliability/memory changes. Krish and I continued integration work around the demo behavior and hardware/software timing.

Design notes: Matching cannot block the UI loop because the mirror must still draw video frames and update hand cursor state. The worker-thread approach separates embedding work from UI rendering. Database face embeddings are cached with a TTL to avoid repeatedly loading the same embedding rows.

Testing/debugging: Performance was checked through latency-focused changes and logging. The goal was to make the demo responsive enough for a physical mirror interaction, where slow feedback feels broken even if the algorithm is correct.

Result: The integrated demo became more responsive and robust, with these commits Git-authored by Krish.

Evidence: commits `86853f7`, `1e207ed`, `ee69e52`, `541868d`, `613349f`, and `ab5ae3d`, authored by Krish; files `hand_tracking/live_match_demo.py`, `hand_tracking/database/db_operations.py`, and `hand_tracking/matching/match.py`.

## 2026-04-26

Objective: Fix logging/UART issues and improve database feature support.

Record: Krish authored the commits that fixed logging behavior, corrected a UART logging error, and added new database methods/files before merging them into main.

Design notes: Runtime logs matter because this system combines camera input, ToF input, UART messages, database reads, and UI rendering. When behavior is wrong, logs are needed to determine whether the failure is sensing, serial communication, matching, or display.

Testing/debugging: Verified that logging changes should now produce output. Merged feature branches related to database and other improvements.

Result: Better observability and more complete database support, with this day's commits authored by Krish.

Evidence: commits `28d72b8`, `12ca502`, `7fef2aa`, `3570193`, `6fb500f`, `a59ffa2`, and `17bfbf7`, authored by Krish.

## 2026-04-27

Objective: Integrate camera-based distance estimation and adjust database behavior for Pi.

Record: Krish authored the camera distance integration and performance commits. I authored the database changes intended for Pi testing. This was part of the broader integration push with Krish to get the physical mirror behavior closer to a complete end-to-end demo.

Design notes: Camera-based distance estimation uses detected face width as an approximate distance proxy:

```text
distance_cm = reference_distance_cm * reference_face_width_px / observed_face_width_px
```

In the current code:

```text
reference_distance_cm = 60
reference_face_width_px = 220
```

This gives a rough presence/range signal when a face is visible, complementing ToF-based presence detection.

Testing/debugging: The database changes were still marked "yet to test," so the next verification step is to run a full Pi test with camera, database, matching, ToF, UART, and LED behavior enabled together.

Result: Camera-distance logic and Pi database changes were added, but final integrated Pi validation remained open.

Evidence: commits `d04d9c5` and `0b6fef6` authored by Krish; commit `267c164` authored by Connor; file `hand_tracking/live_match_demo.py`.

## 2026-05-06

Objective: Reconstruct and organize the lab notebook for submission while preserving an honest record.

Record: Created this digital Markdown notebook under `notebooks/connor/README.md`. Added dated entries, design decisions, test/debug notes, equations, figure references, and bibliographic references based on repository evidence.

Current project status:
- Working: database helpers, profile data, hand cursor UI, face embedding/matching, live demo structure, MCU FSM, UART protocol, ToF integration code, display layout work.
- Needs final verification: complete end-to-end Pi test with camera, matching, ToF trigger, UART messages, LED strip state transitions, and final reset behavior.
- Known risk: real-time face matching and UI responsiveness on Raspberry Pi under final demo conditions.

Final verification checklist:
- Confirm database initializes and contains expected professional profiles.
- Confirm camera opens on Pi using the Linux/V4L2 backend.
- Confirm ToF binary path is correct on the Pi.
- Confirm ToF readings trigger presence only below threshold with valid signal/sigma.
- Confirm MCU receives `PRESENCE` and enters `SCANNING`.
- Confirm Pi sends `MATCH` or `NO_MATCH` after matching.
- Confirm MCU LED state transitions match the physical demo flow.
- Confirm reset returns both Pi and MCU to idle.

Result: Notebook prepared in the course-approved Git Markdown format. Earlier entries are explicitly marked as reconstructed from evidence rather than falsely presented as contemporaneous.

## Page-Equivalent Expanded Notes

The following notes expand the dated notebook record above. They are written as reconstructed engineering detail rather than new claims of contemporaneous handwritten entries. The goal is to capture the kind of reasoning, debugging context, design alternatives, and verification planning that would normally fill additional pages in a physical computation notebook.

## Expanded Notes: Project Definition and Requirements

Objective: Turn the early mirror concept into a concrete engineering problem with identifiable subsystems.

Record: The first phase of the project was not mainly code. It was deciding what the system actually needed to prove. The mirror needed to do more than display a normal GUI; it needed to convince a user that the interface belonged inside a mirror-like object, detect that a person was present, respond without keyboard or mouse input, and present a career/professional match in a way that made sense for an ECE 445 demo. The most important early system requirement was therefore integration, not any one algorithm. A good face matcher would not be sufficient if the display did not look like a mirror, the sensor did not wake the system at the right distance, or the hardware could not be mounted reliably.

Design notes: I separated the project into five core areas: physical mirror/display, presence detection, user interaction, matching/database software, and microcontroller feedback/control. Each area had different risk. The display and mirror film were optical/mechanical risks. Presence detection was a sensing risk. Hand tracking and face matching were compute/perception risks. The database was a data-modeling risk. UART and LED control were integration risks. This framing helped keep the project from becoming only a computer-vision demo.

The physical system implied several non-obvious software constraints. Because the display is behind a reflective surface, text must be larger and higher contrast than on a normal monitor. Because users stand back from the mirror, small UI targets are not acceptable. Because the interaction is public-facing, the system must recover from partial failures without needing a keyboard. Because the mirror has a physical enclosure, the screen coordinate system, camera coordinate system, and sensor field of view all need to agree well enough that the user experience feels intentional.

Open questions recorded from the early design phase:
- What reflective film gives a convincing mirror effect while still passing enough display light?
- How far should a user stand from the mirror for the system to wake?
- Should the system use Kinect, a ToF sensor, camera-based distance estimation, or some combination?
- Can a Raspberry Pi run the required camera and face-matching pipeline at acceptable latency?
- Should user input be hand-tracked cursor motion, presence-only automation, or a simpler button/demo mode?
- How should the system fail if no face is detected or no match is confident?

Engineering decision: Treat presence detection and face matching as separate functions. Presence detection answers "is someone in front of the mirror?" Face matching answers "which profile should be displayed?" Combining these too early would make debugging harder because a failure to wake the mirror could be caused by face detection latency, lighting, camera framing, or identity model issues. Keeping presence detection separate also allowed the MCU/ToF side to make progress independently from the matching pipeline.

Verification plan: A complete demo should be verified as a sequence of smaller demonstrations. First, the display and film should be inspected visually. Second, presence detection should be tested without matching. Third, the hand UI should be tested without the MCU. Fourth, face matching should be tested from still images and then from live frames. Fifth, UART should be tested with simple text messages. Finally, the integrated system should be tested with all components running. This staged test plan reduces the chance that an integrated failure is impossible to diagnose.

Result: The project scope became a smart mirror career-match system with hardware, optics, sensing, embedded firmware, UI, database, and computer-vision components. The notebook record should therefore cover design decisions across all of those areas, not only the commits that added source files.

Evidence: 2026-01-29 Professor Kwiat meeting, 2026-02-10 TA meeting notes, later repository architecture.

## Expanded Notes: Mirror Display and Physical Design

Objective: Identify physical and optical constraints for the mirror enclosure, display, and ToF mounting.

Record: The 2026-02-10 TA meeting and 2026-02-13 machine shop meeting pushed the project toward treating the enclosure as a central design element. The mirror is not just a screen with software. It is a physical object where the display, reflective film, camera, ToF sensor, and user position all interact. The enclosure has to hold the screen securely, give the reflective film a usable viewing plane, hide or position electronics, and keep the ToF sensor aimed at the expected detection region.

Design notes: The two-way film question mattered because the software can only compensate so much. If the film is too reflective, the display content becomes hard to see. If the film passes too much display light or is not reflective enough, the object no longer reads as a mirror. Ambient light also changes the perceived result: a brighter room makes the mirror side more convincing but may wash out the display; a darker room makes display content stronger but can reduce the mirror illusion.

The machine shop meeting clarified that ToF mounting is not a final decoration detail. The sensor needs a fixed position and orientation. If it is angled too high, it may miss shorter users or only detect faces/upper body at close range. If it is angled too low, it may trigger from tables, hands, or objects. If the enclosure flexes or the sensor is loosely mounted, the threshold values in software become less meaningful because the detection cone shifts relative to the user.

Design alternatives considered:
- Place ToF sensor near the display centerline to align sensing with the user-facing interaction.
- Place ToF sensor near the edge of the enclosure to simplify wiring and mounting.
- Use Kinect or camera-based tracking for all presence detection.
- Use a dedicated ToF sensor for wake/presence and reserve the camera for hand/face tasks.

Decision direction: Prefer a dedicated ToF presence sensor for wake behavior, while keeping camera-based distance estimation as a complementary or fallback signal. A ToF sensor is simpler and more deterministic for threshold-based presence detection. Camera-based distance can help when a face is already visible, but it depends on lighting, face detection, and framing.

Testing plan for physical mirror:
- Place display behind film and view it under the lighting conditions expected for demo.
- Check whether text remains legible at the intended user distance.
- Check whether dark UI backgrounds improve or reduce the mirror illusion.
- Check whether the ToF sensor sees a person at the expected distance range.
- Check whether sensor readings change when a user stands slightly left or right of center.
- Verify that screen mounting does not block airflow or cable routing.

Potential failure modes:
- Film reflects too strongly and display content is dim.
- Film transmits too strongly and the mirror illusion is weak.
- ToF sensor mount creates a blind spot directly in front of the mirror.
- Display content is cropped or hidden by enclosure edges.
- The camera view does not align with the displayed torso/face guide.

Result: The enclosure and sensor mount requirements informed later software choices, including safe display area calculations, portrait layout work, ToF thresholding, and camera-distance estimation.

Evidence: 2026-02-10 TA TODO list, 2026-02-13 machine shop meeting, later display constants in `hand_tracking/live_match_demo.py`.

## Expanded Notes: Presence Detection Strategy

Objective: Define presence detection independently from face matching and user selection.

Record: Presence detection was identified early as a key deliverable. The TA notes specifically called for a "proof of presence detection" and for figuring out presence detection without relying on Kinect. This became a recurring design theme. The final codebase reflects multiple presence signals: MCU-side ToF polling, Pi-side VL53L3CX readings, and camera-based face distance estimation.

Design notes: Presence detection should be fast, conservative, and easy to debug. It does not need to identify the user; it only needs to wake the system or move it from idle to scanning. For a demo installation, false negatives are annoying because the system appears dead, but false positives are also bad because the system may start scanning when nobody is intentionally using it. Thresholds should therefore include both distance and signal quality when available.

The Pi-side VL53L3CX logic uses a distance threshold and filters based on signal and sigma. The reconstructed criteria in the current code are:

```text
presence = distance < 500 mm
           AND signal >= 0.05 Mcps
           AND sigma < 50 mm
```

This is better than distance alone because ToF sensors can report readings that are technically present but not reliable. The signal threshold filters weak reflections. The sigma threshold filters uncertain distance estimates.

Camera-based distance estimation gives a second approximate signal:

```text
distance_cm = reference_distance_cm * reference_face_width_px / observed_face_width_px
```

The assumption is that apparent face width decreases as distance increases. This is not precision metrology because face sizes vary and camera field of view matters, but it can be useful for determining whether a user is roughly in range.

Debugging plan:
- Log raw ToF readings before applying thresholds.
- Log whether readings pass or fail each filter.
- Compare sensor triggering with actual user position.
- Test at multiple distances, including just inside and just outside the threshold.
- Confirm that the system does not immediately retrigger after reset.
- Confirm that camera-based distance does not wake the system when no face is visible.

Design tradeoff: A lower wake threshold reduces false positives but may require the user to stand too close. A higher threshold feels more responsive but may trigger from nearby motion. The selected threshold should match the physical installation, not just a nominal sensor datasheet range.

Integration consideration: Presence detection affects both Pi and MCU state. If the Pi detects presence first, it can send `PRESENCE` to the MCU so the MCU FSM enters scanning. If the MCU detects presence first, it sends `PRESENCE` to the Pi. This two-direction design prevents the system from depending on exactly one sensor being the first trigger source.

Result: Presence detection became its own subsystem with explicit thresholds, UART coordination, and fallback/complementary camera logic.

Evidence: 2026-02-10 TA notes, `TOF_PRESENCE_THRESHOLD_MM`, `_is_human_presence`, and `estimate_face_distance_cm` in `hand_tracking/live_match_demo.py`.

## Expanded Notes: User Interface Design

Objective: Develop a mirror-friendly interface that can be controlled without touching the display.

Record: UI work began in a separate private repository on 2026-03-04 and later moved into the current project. The interface needed to be legible at distance, robust to imperfect hand tracking, and simple enough for a user to understand quickly during a demo. The current UI uses camera input, MediaPipe hand tracking, an index-fingertip cursor, smoothing, and hover-based selection.

Design notes: Touch input was not a good fit for the mirror because touching the surface could smudge the film, require capacitive hardware, and break the illusion of interacting naturally with the mirror. A mouse or keyboard would also make the installation feel like a normal computer demo. Hand tracking offered a more natural interaction: the user stands in front of the mirror and points or hovers to select.

The hover-selection design avoids the need to detect pinches or clicks. A dwell timer is easier to explain visually and can be implemented using cursor position over a target for a continuous time interval. The downside is that dwell selection can accidentally trigger if the cursor is noisy or the user rests their hand over a button. To reduce this risk, the UI uses smoothing and relatively large targets.

Important UI parameters from the code:
- `dwell_seconds=1.5` for hover selection in the older modular demo.
- `smoothing_alpha=0.25` to reduce cursor jitter.
- `cursor_radius=10` for visible feedback.
- Large portrait-oriented layout constants in `live_match_demo.py`.

Mirror-specific UI constraints:
- Text must be readable through reflective film.
- Buttons must be large enough for imperfect hand tracking.
- The UI should not cover the face/body region needed for matching.
- Full-screen output should fit the physical visible area of the display.
- The user should be able to reset or return to idle without keyboard input.

Testing/debugging observations:
- A normal laptop UI layout is not automatically appropriate for a portrait mirror.
- Full-screen testing was necessary because the physical screen crop can hide content.
- Hand-tracking jitter can make small buttons frustrating.
- A hover dwell time that is too short feels accidental; too long feels unresponsive.

Design decision: Use a limited number of large actions instead of a dense menu. The older modular UI included actions like `Toggle Overlay`, `Start Demo Mode`, and `Reset / Clear`. The integrated live demo uses a career-selection and match-display flow. This direction fits the public-demo context because users should not need training.

Result: The UI evolved from private-repo prototyping into a mirror-specific hand cursor interface integrated with live camera frames, profile display, and matching state.

Evidence: 2026-03-04 private UI work record, `hand_tracking/UI_Cursor/main.py`, `hand_tracking/UI_Cursor/user_interface.py`, `hand_tracking/live_match_demo.py`, Connor-authored UI commits on 2026-04-20.

## Expanded Notes: Database Design

Objective: Build a local data layer for professional profiles, tags, interaction records, and face embeddings.

Record: The database work began in March and became one of the core parts of the project authored by Connor in Git. The early goal was to avoid hardcoding profile information directly into the UI. The later goal was to support face matching by storing embeddings associated with professional records.

Design notes: The database schema separates profile data from tags and face embeddings. This is useful because a professional may have multiple tags, and a professional may eventually have multiple enrolled images or embeddings. Storing embeddings separately also allows the matching model to change while keeping the profile table stable.

Main database entities:
- `professionals`: core profile record.
- `profile_tags`: multiple tags per profile.
- `interaction_logs`: runtime events and matched profile records.
- `face_embeddings`: model-specific embedding vectors tied to professional IDs.

Important fields in `professionals`:
- Name, title, organization, and quantum area for display.
- Short and long bio fields for different levels of detail.
- Image path for showing the matched profile.
- Fun fact and video URL fields for richer content.

Design choice: Store `image_path` rather than image bytes directly in the database. This keeps the SQLite database smaller and makes it easier to update image assets. The tradeoff is that file paths must be portable across development and Raspberry Pi deployment, which later required path utility work and Pi-specific database changes.

Design choice: Store embeddings as JSON. This is straightforward and easy to inspect, though it may not be the fastest possible representation. For the project scale, readability and ease of debugging were more important than maximum database performance. Later caching reduced the cost of repeatedly loading embeddings.

Testing/debugging plan:
- Initialize the database from a clean state.
- Add a professional and verify the returned ID.
- Add tags and verify tag lookup.
- Insert face embeddings and verify model-name filtering.
- Query all professionals and verify UI display order.
- Test path resolution for images on both development machine and Pi.

Potential failure modes:
- Relative image paths work on one machine but fail on the Pi.
- Embedding vectors are stored with the wrong model name.
- Database mutation tests leave stale test rows.
- Multiple scripts expect different working directories.
- SQLite connection behavior causes threading issues during live matching.

Result: The database became the bridge between the content side of the project and the matching/UI side. It also provided a concrete record of the project goal: the mirror is not just identifying a face, it is presenting a professional profile and career area.

Evidence: commits `e57df0c`, `f4d1c73`, `6608e06`, `267c164`; files `hand_tracking/database/db_init.py`, `hand_tracking/database/db_operations.py`, `hand_tracking/database/path_utils.py`, `hand_tracking/database/mirror.db`.

## Expanded Notes: Face Matching Pipeline

Objective: Implement face matching from live or still images using stored profile embeddings.

Record: The matching layer was added in early April. The main workflow is to enroll professional images, compute embeddings, store them in the database, compute a query embedding from the camera frame, compare the query to stored embeddings, and rank the top matches by cosine similarity.

Design notes: Face matching is split into embedding and ranking. The embedder is responsible for turning an image/face region into a vector. The matcher is responsible for comparing vectors. This separation is important because it allows the identity model to change without rewriting ranking code. The repository includes an InsightFace backend and a MediaPipe-landmark fallback path, with InsightFace being the stronger identity option.

Core matching equation:

```text
cosine_similarity(a, b) = dot(a, b) / (sqrt(sum(a_i^2)) * sqrt(sum(b_i^2)))
```

The value approaches 1 when vectors point in the same direction. It is lower when vectors differ. The top matches are sorted by descending similarity.

Design issue: A high similarity score is only meaningful if the enrolled embeddings and query embeddings were generated by the same model. This is why `model_name` is stored with each embedding and used when fetching candidate embeddings.

Testing/debugging plan:
- Enroll a known image for a profile.
- Query with the same or similar image and verify the correct profile ranks first.
- Query with an unrelated image and verify scores are lower.
- Confirm that no match is returned if the database has no embeddings for the selected model.
- Confirm that top-k ranking returns stable order.
- Test behavior when no face is detected in a frame.

Risk: Face matching may be computationally expensive on Raspberry Pi. A laptop development machine can hide latency that becomes obvious on the final hardware. The design therefore later added a worker thread and frame-size reductions so the UI loop would not block on embedding work.

UI implication: The system should not show a profile immediately on any weak or transient match. A better user experience is to guide the user into position, perform matching at intervals, show ranked candidates if needed, and handle no-match gracefully.

Result: The matching pipeline provided the core "career match" feature, but also introduced one of the largest deployment risks because accurate face embeddings are compute-heavy.

Evidence: commits `5e2fa08`, `04f183c`, files `hand_tracking/matching/embedder.py`, `hand_tracking/matching/match.py`, `hand_tracking/matching/enroll_professional.py`, `hand_tracking/matching/enroll_from_database_paths.py`, and Figure 3.

## Expanded Notes: Live Demo State Flow

Objective: Define the user-facing state flow for the smart mirror demo.

Record: The integrated live demo grew into a state machine on the Pi side, with states such as intro, wait for start, career selection, matching, and profile display. The mirror should not continuously perform expensive matching from startup. It should first wait for presence or a start interaction, guide the user, perform matching, then display a profile and reset.

Design notes: The state flow exists to make the demo understandable and to control compute load. If matching runs all the time, the Pi may be overloaded and the user may see confusing output before they intentionally interact. If the mirror has a clear standby/intro state, the user understands that it is waiting for them.

User flow:
1. System starts in idle/intro.
2. Presence or start interaction moves the system toward active demo.
3. User selects or confirms a career/demo mode using hand cursor.
4. System guides the user into the matching region.
5. Matching runs periodically, not every frame.
6. Profile display shows matched professional information.
7. Reset returns system to a known idle state.

Design choice: Use timed intervals for matching. The code uses a match interval instead of embedding every frame. This reduces CPU load and gives the UI loop room to draw frames, update cursor state, and process sensor/UART messages.

Design choice: Draw a torso/standing guide. A visible guide helps users place themselves correctly, which improves both camera framing and face matching. It also makes debugging easier because the expected region of interest is visible.

Potential failure modes:
- User stands outside the guide and matching fails.
- Matching completes but UART/MCU state does not advance.
- Profile display appears but LED/reset timing does not match.
- The mirror remains in an active state after the user leaves.
- The camera backend fails on Pi due to incorrect capture settings.

Debugging notes: The live demo combines many loops: camera capture, hand tracking, ToF reading, UART reading, matching worker jobs, display drawing, and state updates. Any blocking operation can damage the demo experience. This is why the implementation later used queues, worker threads, and lower-resolution processing for some tasks.

Result: The live demo state flow became the main integration surface for the project. It connects the UI, camera, database, matching, presence detection, and MCU protocol.

Evidence: `STATE_INTRO`, `STATE_WAIT_FOR_START`, `STATE_SELECT_CAREER`, `STATE_MATCHING`, `STATE_PROFILE`, and related constants/functions in `hand_tracking/live_match_demo.py`; Figure 2.

## Expanded Notes: MCU Firmware and State Machine

Objective: Use the microcontroller to manage presence-triggered hardware behavior, LED feedback, and UART coordination.

Record: Krish authored most MCU firmware commits. The MCU firmware was structured around a finite state machine and a hardware abstraction layer. This allowed the team to reason about state transitions separately from hardware calls. The Arduino was used as a stand-in target, with the HAL intended to make future STM32 migration easier.

Design notes: The MCU FSM is:

```text
IDLE -> SCANNING -> MATCH_PENDING -> MATCH_DISPLAYED -> IDLE
```

In `IDLE`, the MCU polls the ToF sensor and waits for presence. In `SCANNING`, it notifies or waits for the Pi to run matching. In `MATCH_PENDING`, it delays before final LED behavior so the display and hardware timing feel coordinated. In `MATCH_DISPLAYED`, it holds the visible result state before returning to idle.

Design choice: Keep hardware access in `hal.cpp` and `hal.h`. This avoids mixing direct sensor/LED calls into the state logic. It also makes it easier to swap hardware platforms. The FSM should ask for operations like "read ToF distance," "set LED," or "send UART message" without knowing implementation details.

UART messages:

```text
MCU -> Pi: PRESENCE
MCU -> Pi: RESET
Pi -> MCU: MATCH
Pi -> MCU: NO_MATCH
Pi -> MCU: PRESENCE
```

Timing considerations:
- ToF polling in idle should be frequent enough to feel responsive.
- Scanning timeout should prevent the system from getting stuck forever.
- Match pending delay should align visible hardware feedback with the profile display.
- Match displayed duration should be long enough for the user to see the result.

Debugging observations: LED behavior was iterated repeatedly because physical wiring and user-visible state can be inverted or unintuitive. A code comment notes inverted wiring around LED setting, which is exactly the type of detail that belongs in a lab notebook because it can otherwise cause confusion during later debugging.

Potential failure modes:
- UART line endings mismatch (`\n` vs stripped line).
- MCU enters scanning but Pi never receives presence.
- Pi sends match but MCU is in the wrong state to receive it.
- Timeout constant is incorrect, making the demo wait too long.
- LED wiring inversion makes "on" and "off" appear backward.

Result: The MCU side provided a deterministic hardware state machine for the physical demo and a clear text protocol for coordinating with the Pi.

Evidence: Krish-authored commits on 2026-04-19 and 2026-04-20; files `MCU/MCU.ino`, `MCU/fsm.cpp`, `MCU/hal.cpp`, `MCU/CLAUDE.md`; Figure 5.

## Expanded Notes: UART Integration

Objective: Make the Raspberry Pi and MCU communicate reliably during the demo.

Record: UART integration was a major debugging target around 2026-04-20. The team worked through baud rate, reset behavior, and message timing. Git authorship shows most UART/MCU changes by Krish, with Connor-authored UI/display/database commits during the same integration push.

Design notes: UART was chosen because it is simple and appropriate for Pi-to-microcontroller communication. The protocol is line-oriented ASCII, which is easy to debug with serial monitors and logs. Binary protocols can be more compact, but this project benefits more from readability and quick debugging.

Protocol design:
- `PRESENCE` means one side detected a person and the demo should move out of idle.
- `MATCH` means the Pi found a result and the MCU can proceed to match-display timing.
- `NO_MATCH` means matching failed or should not display a profile.
- `RESET` means return to a known idle state.

Design issue: Both Pi and MCU can potentially detect presence. This creates a synchronization problem. The solution in the current design allows the Pi to send `PRESENCE` to the MCU if the Pi-side ToF triggers first. The MCU can also send `PRESENCE` to the Pi when the MCU-side sensor triggers first. This avoids requiring a single "master" presence sensor.

Debugging plan:
- Test UART with only simple send/receive messages before running camera code.
- Confirm both sides use the same baud rate.
- Log every received UART line with timestamps.
- Strip line endings consistently before comparison.
- Test reset from each state.
- Test unplug/restart behavior so the system recovers after partial failure.

Observed risk: Integrated demos often fail because of timing, not because individual components are wrong. For example, the Pi may send `MATCH` before the MCU has entered `SCANNING`, or the MCU may reset while the Pi still thinks it is matching. State and message logs are therefore essential.

Result: UART became the system boundary between software perception and hardware feedback. Its simplicity was a strength, but it required careful timing and reset behavior.

Evidence: 2026-04-20 commits and messages, `open_uart_serial`, `uart_reader_loop`, `drain_uart_queue` in `hand_tracking/live_match_demo.py`, `hal_uart_send`/`hal_uart_readline` usage in `MCU/fsm.cpp`.

## Expanded Notes: ToF Sensor Integration

Objective: Add a dedicated distance sensor path for presence detection.

Record: The VL53L3CX Raspberry Pi sensor repository was added and integrated in late April, with most commits authored by Krish. The Pi code runs a compiled ToF binary, parses its output, filters readings, and sends valid presence events into the rest of the live demo.

Design notes: Using an external compiled binary is practical because sensor vendor code often comes with C examples and platform-specific drivers. The Python demo can treat the binary as a sensor process and parse lines from stdout. This avoids rewriting low-level sensor code in Python.

Important implementation details:
- The binary path is configured as `TOF_BINARY_PATH`.
- The reader loop starts the binary with `subprocess.Popen`.
- Output lines are parsed using a regular expression.
- Valid readings are pushed into a queue.
- The process is restarted with backoff if it exits unexpectedly.
- On shutdown, the code sends `SIGINT` so the sensor can stop measurement cleanly.

Parsed output includes:
- status code
- distance in millimeters
- sigma
- signal in Mcps

Design choice: Use a queue between the ToF reader and the main loop. This prevents sensor reading from blocking the UI loop. It also means the main loop can drain all recent readings and decide whether any of them indicate presence.

Testing/debugging plan:
- Confirm the binary exists at the configured path on the Pi.
- Run the binary independently before launching the Python demo.
- Capture example output lines and verify the regex matches.
- Confirm invalid status readings are ignored.
- Confirm sigma scaling is correct.
- Test sensor restart behavior by stopping the binary.
- Compare logged distances against measured physical distances.

Potential failure modes:
- Binary path works on one Pi directory but not another.
- Sensor driver requires I2C permissions or setup.
- Regex fails if output format changes.
- Signal threshold filters out real users in poor reflectivity conditions.
- Distance threshold triggers from the enclosure or nearby objects.
- Sensor process exits and leaves the sensor in a bad measurement state.

Result: ToF integration added a more hardware-appropriate presence signal and reduced dependence on camera/Kinect-style sensing for wake behavior.

Evidence: `VL53L3CX_rasppi/`, `tof_reader_loop`, `_TOF_LINE_RE`, `_is_human_presence`, and late-April ToF commits authored by Krish.

## Expanded Notes: Performance and Latency

Objective: Keep the mirror responsive while running camera input, UI drawing, hand tracking, face matching, database access, UART, and ToF sensing.

Record: Performance became a major concern once the system moved from separate demos to an integrated live demo. Late-April commits improved ToF use, added an embedding worker thread, improved the CV pipeline and cache, optimized database access, and made reliability/memory changes.

Design notes: A mirror demo has a low tolerance for lag. If the camera feed freezes, the hand cursor trails far behind the user, or the match result appears too late, the user experience feels broken. This is true even if the individual algorithms are technically correct.

Performance strategies in the codebase:
- Resize frames before expensive processing.
- Do not run matching every frame.
- Use an embedding worker job/result structure.
- Cache database face embeddings for a short TTL.
- Keep UART and ToF reading in separate loops/queues.
- Use reduced-width frames for presence and hand tracking processing.

Tradeoff: Reducing image size improves speed but can reduce detection accuracy. The system therefore uses separate processing sizes for different tasks. Presence measurement and hand tracking can often use smaller frames. Face matching may require better-quality face crops. UI display still needs to look good on the mirror screen.

Database performance: The face embedding cache avoids repeatedly loading the same stored vectors. This is appropriate because the enrolled profile database does not change frequently during a live demo. The cache TTL gives a balance between freshness and speed.

Threading risk: Moving embedding work off the main loop helps responsiveness, but it introduces synchronization concerns. Results can arrive after the UI state has changed. The code must avoid displaying stale matches or using old frames after reset. Queues and explicit job/result objects make this more manageable.

Testing/debugging plan:
- Log frame processing times.
- Log matching start and completion times.
- Compare UI responsiveness with matching enabled and disabled.
- Test on the Pi, not only on the development machine.
- Watch CPU and memory usage during a multi-minute demo.
- Confirm the system returns to idle after repeated user interactions.

Result: The system moved from proof-of-concept behavior toward a more robust live demo architecture that could plausibly run on the target hardware.

Evidence: 2026-04-24 through 2026-04-27 commits, `MATCH_INTERVAL_SECONDS`, `HAND_TRACKING_MAX_WIDTH_PX`, `PRESENCE_MEASUREMENT_MAX_WIDTH_PX`, `EmbedJob`, `EmbedResult`, database cache in `db_operations.py`.

## Expanded Notes: Display Layout and Camera Geometry

Objective: Make the camera feed, UI, and matching guide fit the physical mirror screen.

Record: Connor-authored commits on 2026-04-20 refined the portrait display layout and updated the UI to fit the mirror screen. The current code contains constants describing the old and new visible dimensions of the screen area, display canvas size, output rotation, and UI margins/scales.

Design notes: A normal webcam frame is landscape, but the mirror display is portrait. This creates a geometry problem. The software must orient, crop, and scale frames so the user sees a natural mirror-like display and so UI elements appear within the visible screen area.

Relevant constants:
- `DISPLAY_CANVAS_WIDTH_PX = 720`
- `DISPLAY_CANVAS_HEIGHT_PX = 1280`
- `WINDOW_OUTPUT_ROTATION = cv2.ROTATE_90_COUNTERCLOCKWISE`
- Old screen dimensions and new visible dimensions used to compute visible ratios.

Functions related to geometry:
- `compute_visible_ratios`
- `compute_safe_area`
- `rotate_camera_frame`
- `rotate_output_frame`
- `fit_frame_to_portrait_canvas`
- `center_crop_frame`
- `scale_frame_to_screen`
- `prepare_camera_frame`

Design issue: Cropping can remove important parts of the camera view. If the face or torso guide is cropped incorrectly, matching and user positioning suffer. But scaling without cropping can distort the aspect ratio. The code therefore uses aspect-preserving crop/scale operations.

UI placement issue: Buttons and labels must fit inside the visible area, not just the raw screen resolution. The physical enclosure can hide edges. This is why visible area ratios and margins matter.

Testing/debugging plan:
- Run full-screen output on the actual display.
- Check whether all UI text and buttons are visible.
- Confirm the torso guide is centered where a user naturally stands.
- Confirm rotation matches the physical screen orientation.
- Verify that camera movement appears mirror-like and not flipped incorrectly.
- Test with a person of different heights standing in front of the mirror.

Result: Display layout work connected software coordinates to the physical mirror geometry, which is essential for making the demo feel like a real installation rather than a desktop window.

Evidence: Connor-authored commits `8498ad3` and `e4a4a7d`, display/layout constants and geometry functions in `hand_tracking/live_match_demo.py`.

## Expanded Notes: Profile Content and Career Matching

Objective: Make the match result meaningful by connecting face matching to professional profile information.

Record: The project is framed as a smart mirror for career exploration in the quantum industry. The profile database includes names, titles, organizations, quantum areas, bios, images, and fun facts. UI commits added profile data such as Keenan into the database, and the handoff notes mention real enrolled profiles including Connor and Krish at one stage.

Design notes: The profile display needs enough information to be interesting without overwhelming the user. Name and image establish the matched person. Title, organization, and quantum area explain career context. A short bio and fun fact make the result more human and approachable.

Design alternatives:
- Display only the top match.
- Display top three matches with scores.
- Allow user to choose a career area before matching.
- Display a profile first, then allow follow-up exploration.

Current direction: The code supports ranked matches and career-area filtering. This is useful because face matching alone may not be the final intended user story. The user may be choosing a quantum career area or being matched to professionals within a selected category.

Database/UI dependency: If profile data is incomplete, the match screen looks unfinished even if the algorithm works. Therefore, content seeding and image path verification are part of the technical demo, not just cosmetic work.

Testing/debugging plan:
- Verify every displayed profile has an image path that resolves.
- Verify long text does not overflow the mirror display.
- Verify all featured career areas return profiles.
- Verify ranked matches show the expected names and scores.
- Verify no profile display crashes when optional fields are missing.

Result: The database and display design support the educational/career component of the project, which distinguishes the mirror from a generic face-recognition demo.

Evidence: `professionals` schema, profile display code in `live_match_demo.py`, `get_all_career_areas`, `get_professionals_by_quantum_area`, and database/profile commits.

## Expanded Notes: Final Integrated Test Plan

Objective: Define a complete end-to-end verification procedure for the final demo.

Record: By late April the project had all major pieces represented in code, but the notebook still records final integrated validation as open. A final checkout/demo test should prove the full chain from user presence to displayed result and reset.

End-to-end test sequence:
1. Boot Raspberry Pi and MCU with the mirror hardware connected.
2. Confirm camera opens using the Linux/V4L2 backend.
3. Confirm the mirror display opens full-screen in the correct orientation.
4. Confirm profile database initializes and contains expected entries.
5. Confirm profile images resolve from Pi filesystem paths.
6. Confirm ToF binary runs independently.
7. Start the live demo and verify idle/intro state.
8. Stand outside the presence threshold and verify the system remains idle.
9. Stand inside the threshold and verify presence is detected.
10. Confirm the MCU receives or sends `PRESENCE`.
11. Confirm the MCU enters `SCANNING`.
12. Use hand cursor to interact with the UI if required by the demo state.
13. Stand inside the torso/face guide.
14. Confirm matching runs at the configured interval.
15. Confirm a profile display appears after a valid match.
16. Confirm the Pi sends `MATCH` to the MCU.
17. Confirm LED behavior follows match pending/display timing.
18. Wait for timeout or trigger reset.
19. Confirm both Pi and MCU return to idle.
20. Repeat the full cycle at least three times.

Measurements to record during final testing:
- Approximate user distance when presence triggers.
- ToF distance, signal, and sigma readings for trigger events.
- Time from presence to scanning state.
- Time from matching start to profile display.
- Match score and selected profile.
- Whether UI cursor remains responsive during matching.
- Whether LED state matches the expected FSM state.
- Any camera frame drops or visible freezes.

Acceptance criteria:
- The system wakes when a user stands in the intended area.
- The display remains readable through the mirror.
- The hand cursor or start interaction is usable without a keyboard.
- Matching produces a profile without freezing the UI.
- UART messages are logged and match expected state transitions.
- The LED/physical feedback is synchronized closely enough for demo use.
- Reset reliably returns the system to idle.

Known risks:
- Pi compute load may still be too high for smooth face matching.
- Camera lighting through/around the mirror may reduce face detection quality.
- ToF threshold may require tuning after final enclosure placement.
- UART timing bugs may only appear during repeated cycles.
- Image paths/database paths may differ between development machine and Pi.

Result: This final test plan provides the verification record needed for lab checkout and final documentation. Any final run should add actual observed values next to these checklist items.

Evidence: Current integrated code, late-April commits, and final status notes.

## Expanded Notes: Report and Design Review Material

Objective: Capture information that can be reused in the design review, final paper, and oral presentation.

Record: The lab notebook should make final documentation easier. The main report story should be that the team designed an interactive smart mirror for quantum career exploration, using a physical mirror/display assembly, presence sensing, hand-based interaction, face/profile matching, a local profile database, and MCU-controlled visible feedback.

System block diagram narrative:
- User stands in front of mirror.
- ToF/camera detects presence.
- Pi runs camera processing and UI state machine.
- Hand tracking maps index fingertip to cursor.
- Database provides profile and embedding records.
- Matching pipeline ranks stored profiles by embedding similarity.
- Pi sends state messages to MCU over UART.
- MCU FSM controls ToF/LED/reset behavior.
- Display presents selected or matched professional profile.

Key design decisions to explain:
- Use Markdown/Git notebook because project evidence is software-heavy and commit history provides timestamps.
- Use a local SQLite database for profile content and embeddings.
- Use cosine similarity for embedding comparison.
- Use hand hover selection to avoid touching the mirror.
- Use dedicated ToF presence detection rather than relying only on face detection.
- Use UART text protocol for Pi/MCU communication.
- Use a HAL/FSM split in MCU firmware for portability and clarity.
- Use worker/caching strategies to reduce live-demo latency.

Equations/formulas to include:

```text
cosine_similarity(a, b) = (a dot b) / (||a|| ||b||)
```

```text
distance_cm = reference_distance_cm * reference_face_width_px / observed_face_width_px
```

```text
presence_valid = distance < threshold AND signal >= min_signal AND sigma < max_sigma
```

Testing discussion to include:
- Presence testing with threshold tuning.
- Mirror film/display visibility testing.
- Camera backend testing on Pi.
- Face matching tests with enrolled profile images.
- UART send/receive tests.
- LED state transition tests.
- Integrated reset/repeatability tests.

Limitations to acknowledge:
- Some notebook entries are reconstructed after the fact from evidence.
- Final Pi performance may depend on lighting, camera, and model load.
- Face matching accuracy is limited by the number and quality of enrolled profile images.
- Camera-based distance estimation is approximate.
- Physical enclosure and sensor placement can change the best threshold values.

Result: These notes create a reusable outline for final documentation and help connect individual commits to the larger engineering story.

Evidence: Full notebook record, repository files, system diagrams, and project prompt.
