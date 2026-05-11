# Trigger: UART PRESENCE from Arduino FSM *or* Pi-side VL53L3CX ToF sensor
# Protocol: receives PRESENCE -> runs match -> sends MATCH -> waits for RESET
#           Pi ToF trigger also sends PRESENCE to MCU so FSM progresses normally
import logging
import os
import queue
import re
import signal
import subprocess
import threading
import time
from collections import OrderedDict, namedtuple

import cv2
import numpy as np

try:
    import serial
except ImportError:
    serial = None

from hand_tracking.UI_Cursor.hand_tracker import HandTracker
from hand_tracking.UI_Cursor.user_interface import HoverSelectUI, layout_menu_items
from hand_tracking.database.db_init import initialize_database
from hand_tracking.database.db_operations import (
    get_all_career_areas,
    close_connection,
    get_all_professionals,
    get_professionals_by_quantum_area,
)
from hand_tracking.matching.embedder import create_embedder
from hand_tracking.matching.match import find_best_database_matches


# Primary local switch for laptop vs final Raspberry Pi deployment.
# Leave as "laptop" for local development; change to "rpi" on the Pi.
DEFAULT_HARDWARE_TARGET = "laptop"

# Optional runtime override:
#   SMART_MIRROR_TARGET=laptop python -m hand_tracking.live_match_demo
#   SMART_MIRROR_TARGET=rpi python -m hand_tracking.live_match_demo
ENV_HARDWARE_TARGET = "SMART_MIRROR_TARGET"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the compiled VL53L3CX binary (run `make example` in VL53L3CX_rasppi/).
DEFAULT_TOF_BINARY_PATH = os.path.join(REPO_ROOT, "VL53L3CX_rasppi", "bin", "main")
# Distance in mm below which the Pi-side ToF sensor counts as a person present.
TOF_PRESENCE_THRESHOLD_MM = 500
# Minimum Signal (Mcps) a valid reading must have — filters noise and tiny objects.
TOF_MIN_SIGNAL_MCPS = 0.05
# Maximum sigma (mm) for a reading to be considered reliable even at status=0.
TOF_MAX_SIGMA_MM = 50.0

TofReading = namedtuple("TofReading", ["distance", "signal", "sigma_mm"])
EmbedJob = namedtuple("EmbedJob", ["frame_region", "allowed_professional_ids"])
EmbedResult = namedtuple("EmbedResult", ["matches", "error"])
HardwareProfile = namedtuple(
    "HardwareProfile",
    [
        "name",
        "enable_tof",
        "enable_uart",
        "camera_candidates",
        "fullscreen_window",
        "uart_device",
        "tof_binary_path",
    ],
)
CameraCandidate = namedtuple("CameraCandidate", ["label", "backend", "configure_mjpg"])

WINDOW_TITLE = "Smart Mirror Career Match Demo"
MATCH_BACKEND = "insightface"
MATCH_INTERVAL_SECONDS = 0.35
TOP_K_MATCHES = 3
CAMERA_ROTATION = None
WINDOW_OUTPUT_ROTATION = cv2.ROTATE_90_COUNTERCLOCKWISE
OLD_SCREEN_HEIGHT_CM = 71.0
OLD_SCREEN_WIDTH_CM = 40.0
NEW_VISIBLE_HEIGHT_CM = 58.0
NEW_VISIBLE_WIDTH_CM = 36.5
DISPLAY_CANVAS_WIDTH_PX = 720
DISPLAY_CANVAS_HEIGHT_PX = 1280

UI_SCALE = 0.82
UI_LEFT_MARGIN = 0.06
UI_TOP_MARGIN = 0.10
UI_ITEM_SPACING = 0.032
FONT_SCALE = 0.60
HEADER_SCALE = 0.58
FPS_SCALE = 0.62
BUTTON_WIDTH_RATIO = 0.44
BUTTON_HEIGHT_RATIO = 0.07
CAREER_GRID_WIDTH_RATIO = 0.84
CAREER_GRID_HEIGHT_RATIO = 0.30
CAREER_GRID_BOTTOM_MARGIN_RATIO = 0.03
CAREER_GRID_HEADER_X_RATIO = 0.12
CAREER_GRID_HEADER_Y_RATIO = 0.60
MATCHING_PANEL_MARGIN_X = 0.05
MATCHING_PANEL_MARGIN_Y = 0.04
PROFILE_TITLE_SCALE = 0.78
PROFILE_NAME_SCALE = 0.74
TORSO_GUIDE_WIDTH_RATIO = 0.42
TORSO_GUIDE_HEIGHT_RATIO = 0.46
TORSO_GUIDE_X_OFFSET_RATIO = 0.0
TORSO_GUIDE_Y_OFFSET_RATIO = -0.10
TORSO_GUIDE_TOP_PADDING_PX = 88
TORSO_GUIDE_BOTTOM_CLEARANCE_PX = 28
MATCH_GUIDE_WIDTH_RATIO = 0.82
MATCH_GUIDE_HEIGHT_RATIO = 0.82
MATCH_GUIDE_TOP_PADDING_PX = 28
MATCH_GUIDE_BOTTOM_PADDING_PX = 24
QUANTUM_BUILDER_CAREER = "Quantum Builder"
FEATURED_CAREERS = [
    "Quantum Scientist",
    QUANTUM_BUILDER_CAREER,
    "Quantum Entrepreneur",
    "Quantum Student",
]

STATE_WAIT_FOR_START = "wait_for_start"
STATE_SELECT_CAREER = "select_career"
STATE_MATCHING = "matching"
STATE_PROFILE = "profile"

PRESENCE_CHECK_INTERVAL_SECONDS = 0.20
ACTIVE_PRESENCE_CHECK_INTERVAL_SECONDS = 1.00
PRESENCE_CONFIRMATION_SECONDS = 0.40
PRESENCE_LOSS_TIMEOUT_SECONDS = 2.00
MATCHING_SCREEN_LOSS_TIMEOUT_SECONDS = 5.00
WAKE_DISTANCE_CM = 85.0
SLEEP_DISTANCE_CM = 100.0
REFERENCE_DISTANCE_CM = 60.0
REFERENCE_FACE_WIDTH_PX = 220.0
SHOW_PRESENCE_DEBUG_TEXT = True
PRESENCE_MEASUREMENT_MAX_WIDTH_PX = 320
HAND_TRACKING_MAX_WIDTH_PX = 320
MATCH_USE_FULL_FRAME = True


def _camera_candidate(label, backend_attr_name, configure_mjpg):
    backend = getattr(cv2, backend_attr_name, None)
    if backend is None:
        return None
    return CameraCandidate(label=label, backend=backend, configure_mjpg=configure_mjpg)


def _build_laptop_camera_candidates():
    candidates = [
        _camera_candidate("v4l2+mjpg", "CAP_V4L2", True),
        _camera_candidate("any+mjpg", "CAP_ANY", True),
        _camera_candidate("avfoundation", "CAP_AVFOUNDATION", False),
        _camera_candidate("msmf", "CAP_MSMF", False),
        _camera_candidate("dshow", "CAP_DSHOW", False),
        _camera_candidate("any", "CAP_ANY", False),
    ]
    return [candidate for candidate in candidates if candidate is not None]


def _resolve_hardware_profile():
    target = os.environ.get(ENV_HARDWARE_TARGET, DEFAULT_HARDWARE_TARGET).strip().lower()
    profiles = {
        "laptop": HardwareProfile(
            name="laptop",
            enable_tof=False,
            enable_uart=False,
            camera_candidates=_build_laptop_camera_candidates(),
            fullscreen_window=False,
            uart_device="/dev/serial0",
            tof_binary_path=DEFAULT_TOF_BINARY_PATH,
        ),
        "rpi": HardwareProfile(
            name="rpi",
            enable_tof=True,
            enable_uart=True,
            camera_candidates=[
                CameraCandidate(
                    label="v4l2+mjpg",
                    backend=getattr(cv2, "CAP_V4L2", getattr(cv2, "CAP_ANY", 0)),
                    configure_mjpg=True,
                ),
            ],
            fullscreen_window=True,
            uart_device="/dev/serial0",
            tof_binary_path=DEFAULT_TOF_BINARY_PATH,
        ),
    }
    if target not in profiles:
        valid_targets = ", ".join(sorted(profiles))
        raise ValueError(
            f"Unsupported {ENV_HARDWARE_TARGET}={target!r}. Expected one of: {valid_targets}."
        )
    return profiles[target]


def open_uart_serial(hardware_profile):
    if not hardware_profile.enable_uart:
        logging.info("[UART] Disabled for hardware target '%s'.", hardware_profile.name)
        return None
    if serial is None:
        raise RuntimeError("pyserial is not installed. Run: pip3 install pyserial")

    try:
        ser = serial.Serial(hardware_profile.uart_device, baudrate=9600, timeout=1)
    except serial.SerialException as exc:
        print(f"ERROR: could not open {hardware_profile.uart_device} — {exc}")
        print("Check raspi-config: disable serial login shell, enable hardware serial port.")
        raise

    ser.dtr = False
    time.sleep(0.1)
    return ser


def uart_reader_loop(ser, message_queue):
    if ser is None:
        logging.warning("[UART] ser is None — uart_reader_loop exiting immediately.")
        return
    while True:
        try:
            line = ser.readline().decode("ascii", errors="replace").strip()
        except serial.SerialException as exc:
            print(f"[UART] Serial error: {exc}")
            continue

        if line:
            message_queue.put(line)


def drain_uart_queue(message_queue):
    messages = []
    while True:
        try:
            messages.append(message_queue.get_nowait())
        except queue.Empty:
            break
    return messages


_TOF_LINE_RE = re.compile(
    r"status=(\d+),\s*D=\s*(\d+)mm,\s*S=\s*(\d+)mm,\s*Signal=\s*([\d.]+)\s*Mcps"
)


def tof_reader_loop(distance_queue, stop_event, hardware_profile):
    """Spawns the VL53L3CX binary and streams valid distance readings into distance_queue.
    Restarts automatically on crash with exponential backoff (1s–30s)."""
    backoff = 1.0
    tof_binary_path = hardware_profile.tof_binary_path

    while not stop_event.is_set():
        try:
            proc = subprocess.Popen(
                [tof_binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except FileNotFoundError:
            logging.error("[ToF] Binary not found at %s. Run `make example` in VL53L3CX_rasppi/.", tof_binary_path)
            return
        except Exception as exc:
            logging.error("[ToF] Failed to start sensor binary: %s", exc)
            return

        last_print_time = 0.0
        try:
            for line in proc.stdout:
                if stop_event.is_set():
                    break
                m = _TOF_LINE_RE.search(line)
                if m and int(m.group(1)) == 0:  # status=0 means valid reading
                    dist = int(m.group(2))
                    sigma_mm = int(m.group(3)) / 65536.0
                    sig = float(m.group(4))
                    now = time.time()
                    if now - last_print_time >= 1.0:
                        logging.info("[ToF] D=%dmm Signal=%.2fMcps sigma=%.1fmm", dist, sig, sigma_mm)
                        last_print_time = now
                    distance_queue.put(TofReading(distance=dist, signal=sig, sigma_mm=sigma_mm))
        finally:
            # Send SIGINT so main.c runs VL53LX_StopMeasurement before exiting,
            # leaving the sensor in a clean state for the next run.
            try:
                proc.send_signal(signal.SIGINT)
            except OSError:
                pass
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()

        if stop_event.is_set():
            break

        logging.warning("[ToF] Process exited with code %s. Restarting in %.0fs.", proc.returncode, backoff)
        stop_event.wait(timeout=backoff)
        backoff = min(backoff * 2, 30.0)


def drain_tof_queue(distance_queue):
    readings = []
    while True:
        try:
            readings.append(distance_queue.get_nowait())
        except queue.Empty:
            break
    return readings


def _is_human_presence(readings):
    return any(
        r.distance < TOF_PRESENCE_THRESHOLD_MM
        and r.signal >= TOF_MIN_SIGNAL_MCPS
        and r.sigma_mm < TOF_MAX_SIGMA_MM
        for r in readings
    )


def estimate_face_distance_cm(face_width_px):
    if face_width_px <= 0:
        return None
    return (REFERENCE_DISTANCE_CM * REFERENCE_FACE_WIDTH_PX) / float(face_width_px)


def resize_frame_for_processing(frame, max_width_px):
    frame_h, frame_w = frame.shape[:2]
    if frame_w <= max_width_px:
        return frame

    scale = max_width_px / float(frame_w)
    target_h = max(1, int(round(frame_h * scale)))
    return cv2.resize(frame, (max_width_px, target_h), interpolation=cv2.INTER_LINEAR)


def measure_presence_distance_cm(embedder, frame):
    processing_frame = resize_frame_for_processing(frame, PRESENCE_MEASUREMENT_MAX_WIDTH_PX)
    face_bbox = embedder.get_primary_face_bbox(processing_frame)
    if face_bbox is None:
        return None, None

    x1, _, x2, _ = face_bbox
    face_width_px = max(0, x2 - x1)
    if face_width_px <= 0:
        return None, face_bbox

    return estimate_face_distance_cm(face_width_px), face_bbox


def draw_presence_debug_text(frame, distance_cm, is_in_range):
    if not SHOW_PRESENCE_DEBUG_TEXT:
        return frame

    debug_frame = frame.copy()
    if distance_cm is None:
        text = "Stand in front of the mirror to begin"
        color = (160, 160, 160)
    else:
        state_text = "IN RANGE" if is_in_range else "TOO FAR"
        text = (
            f"Face distance: {distance_cm:.0f} cm | Wake threshold: {WAKE_DISTANCE_CM:.0f} cm | "
            f"{state_text}"
        )
        color = (0, 220, 0) if is_in_range else (0, 180, 255)

    cv2.putText(
        debug_frame,
        text,
        (24, frame.shape[0] - 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        1,
        cv2.LINE_AA,
    )
    return debug_frame


def get_presence_status_text(distance_cm, is_in_range):
    if distance_cm is None:
        return "Step in front of the mirror to begin"
    state_text = "IN RANGE" if is_in_range else "TOO FAR"
    return f"Face distance: {distance_cm:.0f} cm | Wake threshold: {WAKE_DISTANCE_CM:.0f} cm | {state_text}"


def draw_static_career_buttons(frame, careers, layout_config):
    if not careers:
        return

    frame_h, frame_w = frame.shape[:2]
    layout = layout_menu_items(frame_w, frame_h, len(careers), layout_config)
    button_w = layout["button_w"]
    button_h = layout["button_h"]
    gap = layout["gap"]

    if layout["layout_mode"] == "grid":
        grid_x = layout["grid_x"]
        grid_y = layout["grid_y"]
        cols = layout["grid_cols"]
        positions = []
        for index, label in enumerate(careers):
            row = index // cols
            col = index % cols
            x = grid_x + col * (button_w + gap)
            y = grid_y + row * (button_h + gap)
            positions.append((label, x, y))
    else:
        x0 = layout["x0"]
        y0 = layout["y0"]
        positions = [(label, x0, y0 + index * (button_h + gap)) for index, label in enumerate(careers)]

    for label, x, y in positions:
        cv2.rectangle(frame, (x, y), (x + button_w, y + button_h), (38, 38, 38), thickness=-1)
        cv2.rectangle(frame, (x, y), (x + button_w, y + button_h), (130, 130, 130), thickness=2)
        text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, 2)
        text_x = x + max(12, (button_w - text_size[0]) // 2)
        text_y = y + button_h // 2 + 10
        cv2.putText(
            frame,
            label,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            FONT_SCALE,
            (228, 228, 228),
            2,
            cv2.LINE_AA,
        )


def draw_centered_screen_title(frame, title, subtitle_lines=None):
    frame_h, frame_w = frame.shape[:2]
    title_scale = 0.98
    title_lines = title.split("\n")
    title_line_height = 50
    title_start_y = frame_h // 2 - 120 - ((len(title_lines) - 1) * title_line_height) // 2
    for line_index, title_line in enumerate(title_lines):
        title_size, _ = cv2.getTextSize(title_line, cv2.FONT_HERSHEY_SIMPLEX, title_scale, 3)
        title_x = (frame_w - title_size[0]) // 2
        title_y = title_start_y + line_index * title_line_height
        cv2.putText(
            frame,
            title_line,
            (title_x, title_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            title_scale,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )

    if subtitle_lines:
        status_y = title_start_y + len(title_lines) * title_line_height + 12
        for line_index, (line, color) in enumerate(subtitle_lines):
            line_size, _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.66, 2)
            line_x = (frame_w - line_size[0]) // 2
            cv2.putText(
                frame,
                line,
                (line_x, status_y + line_index * 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.66,
                color,
                2,
                cv2.LINE_AA,
            )


def _configure_camera(cap, camera_candidate):
    if camera_candidate.configure_mjpg:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)


def _camera_has_usable_frame(cap, attempts=3):
    for _ in range(attempts):
        ok, frame = cap.read()
        if ok and frame is not None and frame.size > 0:
            return True
    return False


def open_camera(hardware_profile):
    last_candidate = None
    for camera_candidate in hardware_profile.camera_candidates:
        last_candidate = camera_candidate
        logging.info(
            "[Camera] Trying backend '%s' (mjpg=%s).",
            camera_candidate.label,
            camera_candidate.configure_mjpg,
        )
        cap = cv2.VideoCapture(0, camera_candidate.backend)
        if not cap.isOpened():
            logging.warning("[Camera] Backend '%s' could not open camera 0.", camera_candidate.label)
            cap.release()
            continue

        _configure_camera(cap, camera_candidate)
        if _camera_has_usable_frame(cap):
            logging.info("[Camera] Using backend '%s'.", camera_candidate.label)
            return cap

        logging.warning("[Camera] Backend '%s' opened but did not deliver frames.", camera_candidate.label)
        cap.release()

    failed_backend = "none" if last_candidate is None else last_candidate.label
    raise RuntimeError(
        f"Could not get usable frames from any camera backend for target '{hardware_profile.name}'. "
        f"Last attempted backend: {failed_backend}."
    )


def send_uart_line(ser, line):
    if ser is None or not ser.is_open:
        return
    ser.write(f"{line}\n".encode("ascii"))
    ser.flush()


def compute_visible_ratios(
    old_screen_height_cm=OLD_SCREEN_HEIGHT_CM,
    old_screen_width_cm=OLD_SCREEN_WIDTH_CM,
    new_visible_height_cm=NEW_VISIBLE_HEIGHT_CM,
    new_visible_width_cm=NEW_VISIBLE_WIDTH_CM,
):
    return {
        "visible_height_ratio": new_visible_height_cm / old_screen_height_cm,
        "visible_width_ratio": new_visible_width_cm / old_screen_width_cm,
    }


def compute_safe_area(frame_w, frame_h, visible_ratios):
    safe_w = int(round(frame_w * visible_ratios["visible_width_ratio"]))
    safe_h = int(round(frame_h * visible_ratios["visible_height_ratio"]))
    safe_x = max(0, (frame_w - safe_w) // 2)
    safe_y = max(0, (frame_h - safe_h) // 2)
    return {
        "x": safe_x,
        "y": safe_y,
        "w": safe_w,
        "h": safe_h,
    }


def rotate_camera_frame(frame):
    if CAMERA_ROTATION is None:
        return frame
    return cv2.rotate(frame, CAMERA_ROTATION)


def rotate_output_frame(frame):
    if WINDOW_OUTPUT_ROTATION is None:
        return frame
    return cv2.rotate(frame, WINDOW_OUTPUT_ROTATION)


def fit_frame_to_portrait_canvas(frame, target_size):
    target_w, target_h = target_size
    target_aspect = target_w / target_h

    frame_h, frame_w = frame.shape[:2]
    frame_aspect = frame_w / frame_h

    if frame_aspect > target_aspect:
        crop_h = frame_h
        crop_w = int(round(frame_h * target_aspect))
    else:
        crop_w = frame_w
        crop_h = int(round(frame_w / target_aspect))

    crop_x = max(0, (frame_w - crop_w) // 2)
    crop_y = max(0, (frame_h - crop_h) // 2)
    cropped = frame[crop_y:crop_y + crop_h, crop_x:crop_x + crop_w]
    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LINEAR)


def center_crop_frame(frame, visible_ratios, preserve_aspect=True):
    frame_h, frame_w = frame.shape[:2]
    requested_crop_h = max(1, int(round(frame_h * visible_ratios["visible_height_ratio"])))
    requested_crop_w = max(1, int(round(frame_w * visible_ratios["visible_width_ratio"])))

    if preserve_aspect:
        zoom_factor = max(
            1.0 / visible_ratios["visible_height_ratio"],
            1.0 / visible_ratios["visible_width_ratio"],
        )
        crop_h = max(1, int(round(frame_h / zoom_factor)))
        crop_w = max(1, int(round(frame_w / zoom_factor)))
    else:
        crop_h = requested_crop_h
        crop_w = requested_crop_w

    crop_x = max(0, (frame_w - crop_w) // 2)
    crop_y = max(0, (frame_h - crop_h) // 2)
    return frame[crop_y:crop_y + crop_h, crop_x:crop_x + crop_w]


def scale_frame_to_screen(frame, target_size):
    target_w, target_h = target_size
    return cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)


def prepare_camera_frame(frame, visible_ratios):
    oriented = rotate_camera_frame(frame)
    portrait_canvas = fit_frame_to_portrait_canvas(
        oriented,
        (DISPLAY_CANVAS_WIDTH_PX, DISPLAY_CANVAS_HEIGHT_PX),
    )
    cropped = center_crop_frame(portrait_canvas, visible_ratios, preserve_aspect=True)
    return scale_frame_to_screen(cropped, (DISPLAY_CANVAS_WIDTH_PX, DISPLAY_CANVAS_HEIGHT_PX))


def get_window_size():
    if WINDOW_OUTPUT_ROTATION is None:
        return DISPLAY_CANVAS_WIDTH_PX, DISPLAY_CANVAS_HEIGHT_PX
    return DISPLAY_CANVAS_HEIGHT_PX, DISPLAY_CANVAS_WIDTH_PX


def build_ui_layout_config(visible_ratios):
    return {
        "VISIBLE_WIDTH_RATIO": visible_ratios["visible_width_ratio"],
        "VISIBLE_HEIGHT_RATIO": visible_ratios["visible_height_ratio"],
        "LAYOUT_MODE": "grid",
        "GRID_COLUMNS": 2,
        "GRID_ROWS": 2,
        "GRID_WIDTH_RATIO": CAREER_GRID_WIDTH_RATIO,
        "GRID_HEIGHT_RATIO": CAREER_GRID_HEIGHT_RATIO,
        "GRID_BOTTOM_MARGIN_RATIO": CAREER_GRID_BOTTOM_MARGIN_RATIO,
        "HEADER_X_RATIO": CAREER_GRID_HEADER_X_RATIO,
        "HEADER_Y_RATIO": CAREER_GRID_HEADER_Y_RATIO,
        "UI_SCALE": UI_SCALE,
        "UI_LEFT_MARGIN": UI_LEFT_MARGIN,
        "UI_TOP_MARGIN": UI_TOP_MARGIN,
        "UI_ITEM_SPACING": UI_ITEM_SPACING,
        "FONT_SCALE": FONT_SCALE,
        "HEADER_SCALE": HEADER_SCALE,
        "FPS_SCALE": FPS_SCALE,
        "BUTTON_WIDTH_RATIO": BUTTON_WIDTH_RATIO,
        "BUTTON_HEIGHT_RATIO": BUTTON_HEIGHT_RATIO,
        "PROGRESS_RADIUS": 34,
        "PROGRESS_THICKNESS": 5,
    }


def get_torso_guide_geometry(frame_w, frame_h, layout_config=None, mode="selection"):
    if mode == "matching":
        guide_w = int(frame_w * MATCH_GUIDE_WIDTH_RATIO)
        guide_h = int(frame_h * MATCH_GUIDE_HEIGHT_RATIO)
        center_x = frame_w // 2
        top_y = MATCH_GUIDE_TOP_PADDING_PX
        bottom_limit = frame_h - MATCH_GUIDE_BOTTOM_PADDING_PX
        if top_y + guide_h > bottom_limit:
            guide_h = max(120, bottom_limit - top_y)
    else:
        guide_w = int(frame_w * TORSO_GUIDE_WIDTH_RATIO)
        guide_h = int(frame_h * TORSO_GUIDE_HEIGHT_RATIO)
        center_x = frame_w // 2 + int(frame_w * TORSO_GUIDE_X_OFFSET_RATIO)
        if layout_config is not None:
            menu_layout = layout_menu_items(frame_w, frame_h, len(FEATURED_CAREERS), layout_config)
            bottom_limit = menu_layout["grid_y"] - TORSO_GUIDE_BOTTOM_CLEARANCE_PX
        else:
            bottom_limit = int(frame_h * 0.66)
        top_y = max(TORSO_GUIDE_TOP_PADDING_PX, bottom_limit - guide_h)

    bottom_y = top_y + guide_h
    left_x = max(24, center_x - guide_w // 2)
    right_x = min(frame_w - 24, left_x + guide_w)
    left_x = right_x - guide_w
    center_x = left_x + guide_w // 2

    head_radius_x = int(guide_w * (0.19 if mode != "matching" else 0.20))
    head_radius_y = int(guide_h * 0.20)
    head_center = (center_x, top_y + head_radius_y + 10)

    neck_top_y = head_center[1] + head_radius_y - 2
    neck_base_y = top_y + int(guide_h * 0.42)
    shoulder_y = top_y + int(guide_h * 0.54)
    bust_y = top_y + int(guide_h * 0.78)
    neck_half_w = int(guide_w * 0.09)
    shoulder_half_w = int(guide_w * 0.42)
    bust_half_w = int(guide_w * 0.33)
    shoulder_curve_drop = int(guide_h * 0.06)

    roi_pad_x = int(guide_w * 0.08)
    roi_pad_y = int(guide_h * 0.07)
    match_roi = (
        max(0, left_x - roi_pad_x),
        max(0, top_y - roi_pad_y),
        min(frame_w, right_x + roi_pad_x),
        min(frame_h, bottom_y + roi_pad_y),
    )

    return {
        "left_x": left_x,
        "right_x": right_x,
        "top_y": top_y,
        "bottom_y": bottom_y,
        "center_x": center_x,
        "head_center": head_center,
        "head_radius_x": head_radius_x,
        "head_radius_y": head_radius_y,
        "neck_top_y": neck_top_y,
        "neck_base_y": neck_base_y,
        "shoulder_y": shoulder_y,
        "bust_y": bust_y,
        "neck_half_w": neck_half_w,
        "shoulder_half_w": shoulder_half_w,
        "bust_half_w": bust_half_w,
        "shoulder_curve_drop": shoulder_curve_drop,
        "match_roi": match_roi,
    }


def draw_torso_guide(frame, guide_geometry, label_text="Stand inside the guide for matching"):
    overlay = frame.copy()
    x1, y1, x2, y2 = guide_geometry["match_roi"]
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 255, 255), thickness=-1)
    cv2.addWeighted(overlay, 0.06, frame, 0.94, 0, frame)

    head_center = guide_geometry["head_center"]
    cv2.ellipse(
        frame,
        head_center,
        (guide_geometry["head_radius_x"], guide_geometry["head_radius_y"]),
        0,
        0,
        360,
        (240, 240, 240),
        3,
        cv2.LINE_AA,
    )

    center_x = guide_geometry["center_x"]
    cv2.line(
        frame,
        (center_x - guide_geometry["neck_half_w"], guide_geometry["neck_top_y"]),
        (center_x - guide_geometry["neck_half_w"], guide_geometry["neck_base_y"]),
        (240, 240, 240),
        3,
        cv2.LINE_AA,
    )
    cv2.line(
        frame,
        (center_x + guide_geometry["neck_half_w"], guide_geometry["neck_top_y"]),
        (center_x + guide_geometry["neck_half_w"], guide_geometry["neck_base_y"]),
        (240, 240, 240),
        3,
        cv2.LINE_AA,
    )

    shoulder_curve = np.array(
        [
            (center_x - guide_geometry["shoulder_half_w"], guide_geometry["shoulder_y"] + guide_geometry["shoulder_curve_drop"]),
            (center_x - int(guide_geometry["shoulder_half_w"] * 0.66), guide_geometry["shoulder_y"] - 4),
            (center_x - int(guide_geometry["bust_half_w"] * 0.45), guide_geometry["neck_base_y"] + 8),
            (center_x, guide_geometry["neck_base_y"]),
            (center_x + int(guide_geometry["bust_half_w"] * 0.45), guide_geometry["neck_base_y"] + 8),
            (center_x + int(guide_geometry["shoulder_half_w"] * 0.66), guide_geometry["shoulder_y"] - 4),
            (center_x + guide_geometry["shoulder_half_w"], guide_geometry["shoulder_y"] + guide_geometry["shoulder_curve_drop"]),
            (center_x + guide_geometry["bust_half_w"], guide_geometry["bust_y"]),
            (center_x - guide_geometry["bust_half_w"], guide_geometry["bust_y"]),
        ],
        dtype=np.int32,
    )
    cv2.polylines(frame, [shoulder_curve], isClosed=True, color=(240, 240, 240), thickness=3, lineType=cv2.LINE_AA)

    cv2.putText(
        frame,
        label_text,
        (x1 + 12, y1 - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        (240, 240, 240),
        1,
        cv2.LINE_AA,
    )


def get_menu_right_edge(ui):
    if not getattr(ui, "buttons", None):
        return None
    return max(button.x + button.w for button in ui.buttons)


def wrap_text(text, max_chars):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current_line = words[0]
        for word in words[1:]:
            candidate = f"{current_line} {word}"
            if len(candidate) <= max_chars:
                current_line = candidate
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

    return lines


def draw_text_block(frame, text, origin_x, origin_y, max_chars, line_height, color, max_lines=None, scale=0.55, thickness=1):
    lines = wrap_text(text, max_chars)
    if max_lines is not None and len(lines) > max_lines:
        visible_lines = lines[:max_lines]
        last_line = visible_lines[-1]
        if len(last_line) > max_chars - 3:
            last_line = last_line[:max_chars - 3].rstrip()
        visible_lines[-1] = f"{last_line}..."
        lines = visible_lines

    for line_index, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (origin_x, origin_y + line_index * line_height),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )


def draw_labeled_text_section(
    frame,
    title,
    text,
    x,
    y,
    width,
    height,
    max_chars,
    line_height,
    body_scale=0.48,
    body_thickness=1,
    title_scale=0.56,
):
    cv2.rectangle(frame, (x, y), (x + width, y + height), (36, 36, 36), thickness=-1)
    cv2.rectangle(frame, (x, y), (x + width, y + height), (110, 110, 110), thickness=1)

    title_y = y + 28
    cv2.putText(
        frame,
        title,
        (x + 16, title_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        title_scale,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    body_start_y = y + 58
    bottom_padding = 16
    usable_height = max(0, height - (body_start_y - y) - bottom_padding)
    max_lines = max(1, usable_height // line_height)
    draw_text_block(
        frame,
        text,
        x + 16,
        body_start_y,
        max_chars=max_chars,
        line_height=line_height,
        color=(220, 220, 220),
        max_lines=max_lines,
        scale=body_scale,
        thickness=body_thickness,
    )


_image_cache = OrderedDict()


def draw_profile_image(frame, image_path, x, y, width, height):
    if not image_path or not os.path.exists(image_path):
        cv2.rectangle(frame, (x, y), (x + width, y + height), (55, 55, 55), thickness=-1)
        cv2.rectangle(frame, (x, y), (x + width, y + height), (210, 210, 210), thickness=2)
        cv2.putText(
            frame,
            "No Image",
            (x + 36, y + height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (220, 220, 220),
            2,
            cv2.LINE_AA,
        )
        return

    if image_path not in _image_cache:
        raw = cv2.imread(image_path)
        if raw is None:
            _image_cache[image_path] = None
            if len(_image_cache) > 20:
                _image_cache.popitem(last=False)
        else:
            image_h, image_w, _ = raw.shape
            scale = min(width / image_w, height / image_h)
            resized = cv2.resize(raw, (int(image_w * scale), int(image_h * scale)))
            canvas = np.full((height, width, 3), 30, dtype=np.uint8)
            offset_y = (height - resized.shape[0]) // 2
            offset_x = (width - resized.shape[1]) // 2
            canvas[offset_y:offset_y + resized.shape[0], offset_x:offset_x + resized.shape[1]] = resized
            _image_cache[image_path] = canvas
            if len(_image_cache) > 20:
                _image_cache.popitem(last=False)

    cached = _image_cache.get(image_path)
    if cached is None:
        cv2.rectangle(frame, (x, y), (x + width, y + height), (55, 55, 55), thickness=-1)
    else:
        frame[y:y + height, x:x + width] = cached
    cv2.rectangle(frame, (x, y), (x + width, y + height), (210, 210, 210), thickness=2)


def get_available_careers():
    all_areas = get_all_career_areas()
    return [career for career in FEATURED_CAREERS if career in all_areas]


def resolve_target_professional(quantum_area):
    professionals = get_professionals_by_quantum_area(quantum_area)
    return professionals[0] if professionals else None


def get_allowed_professional_ids(quantum_area):
    professionals = get_professionals_by_quantum_area(quantum_area)
    return [row[0] for row in professionals]


def draw_matching_overlay(frame, selected_career, status_text, visible_ratios):
    h, w, _ = frame.shape
    safe_area = compute_safe_area(w, h, visible_ratios)
    panel_margin_x = int(safe_area["w"] * MATCHING_PANEL_MARGIN_X)
    panel_margin_y = int(safe_area["h"] * MATCHING_PANEL_MARGIN_Y)
    panel_w = min(440, safe_area["w"] - 2 * panel_margin_x)
    panel_h = 220
    panel_x = safe_area["x"] + panel_margin_x
    panel_y = safe_area["y"] + safe_area["h"] - panel_h - panel_margin_y

    cv2.rectangle(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (20, 20, 20), thickness=-1)
    cv2.rectangle(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (220, 220, 220), thickness=2)

    cv2.putText(
        frame,
        "Matching In Progress",
        (panel_x + 20, panel_y + 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.66,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    draw_text_block(
        frame,
        f"Selected career: {selected_career}",
        panel_x + 20,
        panel_y + 70,
        max_chars=32,
        line_height=20,
        color=(0, 255, 255),
        max_lines=2,
        scale=0.50,
        thickness=1,
    )
    draw_text_block(
        frame,
        "Look at the camera. Once a face is matched, the full professional profile will replace this screen.",
        panel_x + 20,
        panel_y + 104,
        max_chars=34,
        line_height=19,
        color=(215, 215, 215),
        max_lines=4,
        scale=0.46,
        thickness=1,
    )
    draw_text_block(
        frame,
        status_text,
        panel_x + 20,
        panel_y + 180,
        max_chars=36,
        line_height=18,
        color=(215, 215, 215),
        max_lines=1,
        scale=0.44,
        thickness=1,
    )

    cv2.putText(
        frame,
        "Press 'r' to return to career selection.",
        (panel_x + 20, panel_y + panel_h - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )


def extract_match_region(frame, guide_geometry):
    if MATCH_USE_FULL_FRAME:
        return frame
    x1, y1, x2, y2 = guide_geometry["match_roi"]
    return frame[y1:y2, x1:x2]


def draw_wait_for_start_screen(frame_shape, careers, layout_config, distance_cm=None, is_in_range=False):
    frame = np.zeros(frame_shape, dtype=np.uint8)
    status_text = get_presence_status_text(distance_cm, is_in_range)
    status_lines = wrap_text(status_text, 40)
    status_color = (0, 220, 0) if is_in_range else (200, 200, 200) if distance_cm is None else (0, 180, 255)
    draw_centered_screen_title(
        frame,
        "Select your quantum future",
        [(line, status_color) for line in status_lines[:2]],
    )
    draw_static_career_buttons(frame, careers, layout_config)
    return frame


def draw_profile_screen(frame_shape, professional, selected_career, matched_test_name):
    frame = np.full(frame_shape, 18, dtype=np.uint8)
    h, w, _ = frame_shape

    cv2.rectangle(frame, (40, 40), (w - 40, h - 40), (30, 30, 30), thickness=-1)
    cv2.rectangle(frame, (40, 40), (w - 40, h - 40), (220, 220, 220), thickness=2)

    cv2.putText(
        frame,
        "Matched Quantum Professional",
        (70, 88),
        cv2.FONT_HERSHEY_SIMPLEX,
        PROFILE_TITLE_SCALE,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    draw_text_block(
        frame,
        f"Career selected: {selected_career} | Face matched to: {matched_test_name}",
        70,
        120,
        max_chars=52,
        line_height=20,
        color=(215, 215, 215),
        max_lines=3,
        scale=0.46,
        thickness=1,
    )

    image_x = 70
    image_y = 160
    image_w = 300
    image_h = 340
    draw_profile_image(frame, professional[7], image_x, image_y, image_w, image_h)

    text_x = 410
    cv2.putText(
        frame,
        professional[1],
        (text_x, 190),
        cv2.FONT_HERSHEY_SIMPLEX,
        PROFILE_NAME_SCALE,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    draw_text_block(
        frame,
        professional[2] or "Unknown title",
        text_x,
        228,
        max_chars=28,
        line_height=22,
        color=(225, 225, 225),
        max_lines=2,
        scale=0.58,
        thickness=1,
    )
    draw_text_block(
        frame,
        professional[3] or "Unknown organization",
        text_x,
        288,
        max_chars=30,
        line_height=20,
        color=(205, 205, 205),
        max_lines=2,
        scale=0.50,
        thickness=1,
    )
    draw_text_block(
        frame,
        f"Quantum Area: {professional[4] or 'Unknown'}",
        text_x,
        338,
        max_chars=30,
        line_height=20,
        color=(0, 255, 255),
        max_lines=2,
        scale=0.48,
        thickness=1,
    )

    draw_labeled_text_section(
        frame,
        "Short Bio",
        professional[5] or "No short bio available.",
        x=70,
        y=530,
        width=300,
        height=150,
        max_chars=34,
        line_height=20,
        body_scale=0.46,
        title_scale=0.54,
    )

    draw_labeled_text_section(
        frame,
        "Longer Description",
        professional[6] or "No long bio available.",
        x=410,
        y=390,
        width=260,
        height=170,
        max_chars=28,
        line_height=18,
        body_scale=0.44,
        title_scale=0.52,
    )

    draw_labeled_text_section(
        frame,
        "Fun Fact",
        professional[8] or "No fun fact available.",
        x=410,
        y=590,
        width=260,
        height=110,
        max_chars=28,
        line_height=18,
        body_scale=0.44,
        title_scale=0.52,
    )

    cv2.putText(
        frame,
        "Press 'r' to return to career selection. Press 'q' to quit.",
        (70, h - 52),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (205, 205, 205),
        1,
        cv2.LINE_AA,
    )

    return frame


def embedding_worker(embedder, input_q, output_q, stop_event):
    while not stop_event.is_set():
        try:
            job = input_q.get(timeout=0.1)
        except queue.Empty:
            continue
        try:
            result = embedder.embed_bgr_image(job.frame_region)
            matches = find_best_database_matches(
                result.embedding,
                result.model_name,
                top_k=TOP_K_MATCHES,
                allowed_professional_ids=job.allowed_professional_ids,
            )
            output_q.put(EmbedResult(matches=matches, error=None))
        except Exception as exc:
            output_q.put(EmbedResult(matches=None, error=str(exc)))


def main():
    hardware_profile = _resolve_hardware_profile()
    initialize_database()
    visible_ratios = compute_visible_ratios()
    ui_layout_config = build_ui_layout_config(visible_ratios)
    window_w, window_h = get_window_size()
    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    if hardware_profile.fullscreen_window:
        cv2.setWindowProperty(WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.resizeWindow(WINDOW_TITLE, window_w, window_h)
    tracker = HandTracker(max_num_hands=1)
    careers = get_available_careers()
    uart_queue = queue.Queue()
    tof_queue = queue.Queue()
    tof_stop_event = threading.Event()
    embed_input_q = queue.Queue(maxsize=1)
    embed_output_q = queue.Queue()
    embed_stop_event = threading.Event()
    ser = None

    logging.basicConfig(
        level=logging.INFO,
        # format="%(asctime)s %(levelname)s %(message)s",
        force=True  # overrides any existing handler configuration
    )
    logging.info(
        "Hardware target '%s' active (UART=%s, ToF=%s, fullscreen=%s, camera_candidates=%s).",
        hardware_profile.name,
        hardware_profile.enable_uart,
        hardware_profile.enable_tof,
        hardware_profile.fullscreen_window,
        [candidate.label for candidate in hardware_profile.camera_candidates],
    )
    if hardware_profile.enable_tof:
        tof_thread = threading.Thread(
            target=tof_reader_loop,
            args=(tof_queue, tof_stop_event, hardware_profile),
            daemon=True,
        )
        tof_thread.start()

    try:
        ser = open_uart_serial(hardware_profile)
        if ser is not None and ser.is_open:
            uart_thread = threading.Thread(target=uart_reader_loop, args=(ser, uart_queue), daemon=True)
            uart_thread.start()
        embedder = create_embedder(MATCH_BACKEND)
        embed_thread = threading.Thread(
            target=embedding_worker,
            args=(embedder, embed_input_q, embed_output_q, embed_stop_event),
            daemon=True,
        )
        embed_thread.start()
    except Exception as exc:
        if serial is not None and isinstance(exc, serial.SerialException):
            tracker.close()
            cv2.destroyAllWindows()
            return
        if isinstance(exc, RuntimeError):
            print(f"ERROR: {exc}")
            tracker.close()
            cv2.destroyAllWindows()
            return
        print(f"ERROR: Could not initialize embedding backend: {exc}")
        tracker.close()
        if ser is not None and ser.is_open:
            ser.close()
        cv2.destroyAllWindows()
        return

    try:
        cap = open_camera(hardware_profile)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        tof_stop_event.set()
        embed_stop_event.set()
        embedder.close()
        tracker.close()
        if ser is not None and ser.is_open:
            ser.close()
        cv2.destroyAllWindows()
        return

    ui = HoverSelectUI(
        dwell_seconds=1.5,
        smoothing_alpha=0.25,
        cursor_radius=10,
        button_labels=careers,
        header_text="",
        layout_config=ui_layout_config,
    )

    state = STATE_WAIT_FOR_START
    selected_career = None
    matching_status = "Waiting to start matching."
    matched_professional = None
    matched_test_name = None
    last_match_t = 0.0
    allowed_professional_ids = []
    match_sent = False
    reset_requested = False
    last_presence_check_t = 0.0
    last_measured_distance_cm = None
    presence_in_range_since_t = None
    last_in_range_t = None

    def reset_to_wait_for_start():
        nonlocal state
        nonlocal selected_career
        nonlocal matching_status
        nonlocal matched_professional
        nonlocal matched_test_name
        nonlocal last_match_t
        nonlocal allowed_professional_ids
        nonlocal match_sent
        nonlocal reset_requested
        nonlocal presence_in_range_since_t
        nonlocal last_in_range_t

        state = STATE_WAIT_FOR_START
        selected_career = None
        matching_status = "Waiting to start matching."
        matched_professional = None
        matched_test_name = None
        last_match_t = 0.0
        allowed_professional_ids = []
        match_sent = False
        reset_requested = False
        presence_in_range_since_t = None
        last_in_range_t = None
        ui.set_buttons(careers, "")
        ui.set_layout_config(ui_layout_config)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)
            display_frame = prepare_camera_frame(frame, visible_ratios)
            h, w, _ = display_frame.shape
            now = time.time()

            # Drain UART: RESET always resets session; PRESENCE only wakes from wait state.
            for message in drain_uart_queue(uart_queue):
                if message == "RESET":
                    reset_requested = True
                elif message == "PRESENCE" and state == STATE_WAIT_FOR_START:
                    state = STATE_SELECT_CAREER
                    last_in_range_t = now

            if reset_requested:
                reset_to_wait_for_start()
                continue

            should_run_camera_presence_check = state in (
                STATE_WAIT_FOR_START,
                STATE_MATCHING,
                STATE_PROFILE,
            )
            presence_check_interval = (
                PRESENCE_CHECK_INTERVAL_SECONDS
                if state == STATE_WAIT_FOR_START
                else ACTIVE_PRESENCE_CHECK_INTERVAL_SECONDS
            )

            # Camera-based face distance checks are expensive on the Pi. Keep them
            # off the cursor-selection path and run them less often once a session is active.
            if (
                should_run_camera_presence_check
                and now - last_presence_check_t >= presence_check_interval
            ):
                last_presence_check_t = now
                last_measured_distance_cm, _ = measure_presence_distance_cm(embedder, display_frame)

            wake_in_range = (
                last_measured_distance_cm is not None
                and last_measured_distance_cm <= WAKE_DISTANCE_CM
            )
            keep_awake_in_range = (
                last_measured_distance_cm is not None
                and last_measured_distance_cm <= SLEEP_DISTANCE_CM
            )

            # Pi-side ToF trigger: parallel presence path alongside UART and camera.
            if state == STATE_WAIT_FOR_START and _is_human_presence(drain_tof_queue(tof_queue)):
                # Notify MCU so its FSM also progresses to SCANNING.
                send_uart_line(ser, "PRESENCE")
                state = STATE_SELECT_CAREER
                last_in_range_t = now

            if state == STATE_WAIT_FOR_START:
                # Camera-based presence confirmation with hysteresis.
                if wake_in_range:
                    if presence_in_range_since_t is None:
                        presence_in_range_since_t = now
                    elif now - presence_in_range_since_t >= PRESENCE_CONFIRMATION_SECONDS:
                        send_uart_line(ser, "PRESENCE")
                        state = STATE_SELECT_CAREER
                        last_in_range_t = now
                else:
                    presence_in_range_since_t = None

                wait_frame = draw_wait_for_start_screen(
                    display_frame.shape,
                    careers=careers,
                    layout_config=ui_layout_config,
                    distance_cm=last_measured_distance_cm,
                    is_in_range=wake_in_range,
                )
                cv2.imshow(WINDOW_TITLE, rotate_output_frame(wait_frame))
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    break
                if key == 13:
                    send_uart_line(ser, "PRESENCE")
                    state = STATE_SELECT_CAREER
                    last_in_range_t = now
                continue

            active_presence_loss_timeout = (
                MATCHING_SCREEN_LOSS_TIMEOUT_SECONDS
                if state == STATE_MATCHING
                else PRESENCE_LOSS_TIMEOUT_SECONDS
            )

            # For all active states: update presence keep-alive; reset if person has left.
            if keep_awake_in_range:
                last_in_range_t = now
            elif last_in_range_t is not None and now - last_in_range_t >= active_presence_loss_timeout:
                reset_to_wait_for_start()
                continue

            if state == STATE_PROFILE:
                profile_frame = draw_profile_screen(
                    (DISPLAY_CANVAS_HEIGHT_PX, DISPLAY_CANVAS_WIDTH_PX, 3),
                    matched_professional,
                    selected_career,
                    matched_test_name,
                )
                cv2.imshow(WINDOW_TITLE, rotate_output_frame(profile_frame))
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    break
                if key == ord("r"):
                    state = STATE_SELECT_CAREER
                    selected_career = None
                    matched_professional = None
                    matched_test_name = None
                    ui.set_buttons(careers, "")
                    ui.set_layout_config(ui_layout_config)
                continue

            if state == STATE_SELECT_CAREER:
                hand_tracking_frame = resize_frame_for_processing(display_frame, HAND_TRACKING_MAX_WIDTH_PX)
                tip_norm = tracker.get_index_tip_norm(hand_tracking_frame)
                ui.update_cursor_from_norm(tip_norm, w, h)
                events = ui.update_and_draw(display_frame)
                draw_centered_screen_title(display_frame, "Use your finger to\nselect your quantum future")
                state_changed = False
                for event in events:
                    normalized_event = event.lower()
                    if normalized_event.startswith("selected:"):
                        selected_career = event.split(":", 1)[1].strip()
                        target_professional = resolve_target_professional(selected_career)
                        if target_professional is None:
                            continue
                        state = STATE_MATCHING
                        matching_status = f"Career selected: {selected_career}. Looking for a face..."
                        matched_professional = None
                        matched_test_name = None
                        allowed_professional_ids = get_allowed_professional_ids(selected_career)
                        if not allowed_professional_ids:
                            matching_status = f"No professionals exist for {selected_career}."
                        last_match_t = 0.0
                        last_in_range_t = now
                        state_changed = True
                        break

                if state_changed:
                    draw_matching_overlay(display_frame, selected_career, matching_status, visible_ratios)
            elif state == STATE_MATCHING:
                guide_geometry = get_torso_guide_geometry(w, h, ui_layout_config, mode="matching")
                draw_torso_guide(display_frame, guide_geometry, "Keep your face and torso inside the guide")

                # Submit a new embedding job every MATCH_INTERVAL_SECONDS.
                # put_nowait drops the frame if the worker is still busy (queue full).
                if now - last_match_t >= MATCH_INTERVAL_SECONDS:
                    last_match_t = now
                    match_region = extract_match_region(display_frame, guide_geometry)
                    try:
                        embed_input_q.put_nowait(
                            EmbedJob(
                                frame_region=match_region.copy(),
                                allowed_professional_ids=allowed_professional_ids,
                            )
                        )
                    except queue.Full:
                        pass

                # Collect any result the worker has ready this frame.
                try:
                    embed_result = embed_output_q.get_nowait()
                    if embed_result.error is not None:
                        matching_status = f"Looking for a face... ({embed_result.error})"
                    elif embed_result.matches:
                        source_professional = embed_result.matches[0]["professional"]
                        matched_professional = source_professional
                        matched_test_name = source_professional[1]
                        state = STATE_PROFILE
                        if not match_sent:
                            send_uart_line(ser, "MATCH")
                            match_sent = True
                    else:
                        matching_status = (
                            f"No enrolled face matches are available for {selected_career}. "
                            "Choose a career that has an enrolled profile."
                        )
                except queue.Empty:
                    pass

                draw_matching_overlay(display_frame, selected_career, matching_status, visible_ratios)

            cv2.imshow(WINDOW_TITLE, rotate_output_frame(display_frame))
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if state == STATE_MATCHING and key == ord("r"):
                state = STATE_SELECT_CAREER
                selected_career = None
                ui.set_layout_config(ui_layout_config)
                ui.set_buttons(careers, "")
    finally:
        cap.release()
        tof_stop_event.set()
        embed_stop_event.set()
        embedder.close()
        tracker.close()
        if ser is not None and ser.is_open:
            ser.close()
        close_connection()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
