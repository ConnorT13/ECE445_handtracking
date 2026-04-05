# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Activate virtual environment first
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

python main.py
```

Press `q` or `Esc` to quit.

## Dependencies

Key packages: `opencv-python`, `mediapipe`, `pyserial`. Install via:
```bash
pip install opencv-python mediapipe pyserial
```

The `hand_landmarker.task` model file is bundled in the repo. If missing, `HandTracker` will auto-download it from Google's MediaPipe storage on first run.

## Architecture

The system is a real-time hand-tracking UI that controls an Arduino over serial. Data flows in one direction per frame:

```
Camera → HandTracker → HoverSelectUI → ArduinoController
```

1. **`hand_tracker.py` — `HandTracker`**: Wraps MediaPipe to return the index fingertip position as normalized `(x, y)` in `[0,1]`. Uses `mp.solutions.hands` (lite model, fastest) with a fallback to the `mediapipe.tasks` `HandLandmarker` API if solutions is unavailable.

2. **`user_interface.py` — `HoverSelectUI`**: Manages a hover-to-select button UI drawn on the OpenCV frame. Cursor position is smoothed with an exponential moving average (`smoothing_alpha`). When the cursor dwells over a button for `dwell_seconds` (default 1.5s), it fires a `"selected:<label>"` event and shows a circular progress ring. Layout is lazily initialized on the first frame to accommodate any frame size.

3. **`send_data.py` — `ArduinoController`**: Opens a serial connection and sends single-byte commands. Command mapping: `0x01` = Toggle Overlay, `0x02` = Start Demo Mode, `0x03` = Reset/Clear.

4. **`main.py`**: Wires the three modules together in the main loop. Camera is set to 1280×720 @ 30fps with a mirrored view.

## Platform-Specific Notes

- **Camera backend**: `cv2.VideoCapture(0)` is generic. For Windows use `cv2.CAP_DSHOW`; for macOS use `cv2.CAP_AVFOUNDATION` (commented out in `main.py`).
- **Arduino port**: Hardcoded as `'COM5'` in `main.py`. Change to the appropriate port (`/dev/ttyUSB0` on Linux, `/dev/cu.usbmodem*` on macOS).


## Project Overview

This repository contains the **Raspberry Pi application** for the *Facial Matching Display Mirror* — a smart mirror that detects a user's presence, accepts touchless hand-gesture input, and displays matched STEM role model profiles on the mirror surface.

**System role:** The Pi is the vision and display worker. It runs all computer vision pipelines (face detection, face recognition, hand tracking) and drives the HDMI display. A separate STM32F401 microcontroller acts as the system brain: it owns the state machine, reads the ToF presence sensor over I2C, receives hand landmark coordinates from the Pi over UART, performs dwell-based gesture selection, and controls status LEDs and a buzzer.

**This app's responsibilities:**
- Detect hand landmarks in real time (MediaPipe) and stream normalized fingertip coordinates to the STM32 over UART
- Render the hover-to-select gesture UI overlaid on the camera feed
- Run face detection (MediaPipe) and face recognition (`face_recognition` / dlib ResNet, 128-dim embeddings with cosine similarity) to match a user to a STEM role model profile
- Receive display commands from the STM32 and update the mirror UI accordingly

**Communication:** Bidirectional UART between Pi and STM32. Pi → STM32: fingertip `(x, y)` coordinates each frame. STM32 → Pi: discrete display commands (`Toggle Overlay`, `Start Demo`, `Reset`). The `ArduinoController` in this repo currently targets an Arduino Uno acting as an STM32 stand-in for integration testing; the serial protocol is identical.