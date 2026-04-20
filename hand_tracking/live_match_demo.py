import os
import time

import cv2
import numpy as np

from hand_tracking.UI_Cursor.hand_tracker import HandTracker
from hand_tracking.UI_Cursor.user_interface import HoverSelectUI
from hand_tracking.database.db_init import initialize_database
from hand_tracking.database.db_operations import (
    get_all_professionals,
    get_professionals_by_quantum_area,
)
from hand_tracking.matching.embedder import create_embedder
from hand_tracking.matching.match import find_best_database_matches


WINDOW_TITLE = "Smart Mirror Career Match Demo"
MATCH_BACKEND = "insightface"
MATCH_INTERVAL_SECONDS = 1.5
TOP_K_MATCHES = 3
INTRO_DURATION_SECONDS = 7.0
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
MATCHING_PANEL_MARGIN_X = 0.05
MATCHING_PANEL_MARGIN_Y = 0.04
INTRO_TITLE_SCALE = 0.78
INTRO_SUBTITLE_SCALE = 0.60
PROFILE_TITLE_SCALE = 0.78
PROFILE_NAME_SCALE = 0.74
TORSO_GUIDE_WIDTH_RATIO = 0.42
TORSO_GUIDE_HEIGHT_RATIO = 0.74
TORSO_GUIDE_X_OFFSET_RATIO = -0.08
TORSO_GUIDE_Y_OFFSET_RATIO = 0.18
TORSO_GUIDE_MENU_CLEARANCE_PX = 36
FEATURED_CAREERS = [
    "Quantum Hardware",
    "Quantum Software",
    "Quantum Algorithms",
    "Quantum Chemistry",
    "Quantum Education",
]

STATE_INTRO = "intro"
STATE_SELECT_CAREER = "select_career"
STATE_MATCHING = "matching"
STATE_PROFILE = "profile"


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


def get_torso_guide_geometry(frame_w, frame_h, min_left_x=None):
    guide_h = int(frame_h * TORSO_GUIDE_HEIGHT_RATIO)
    guide_w = int(frame_w * TORSO_GUIDE_WIDTH_RATIO)
    center_x = frame_w // 2 + int(frame_w * TORSO_GUIDE_X_OFFSET_RATIO)
    center_y = frame_h // 2 + int(frame_h * TORSO_GUIDE_Y_OFFSET_RATIO)
    top_y = max(120, center_y - guide_h // 2)
    left_x = center_x - guide_w // 2
    right_x = left_x + guide_w
    bottom_y = top_y + guide_h

    if left_x < 0:
        left_x = 0
        right_x = guide_w
        center_x = guide_w // 2
    elif right_x > frame_w:
        right_x = frame_w
        left_x = frame_w - guide_w
        center_x = left_x + guide_w // 2
    if bottom_y > frame_h - 20:
        bottom_y = frame_h - 20
        top_y = bottom_y - guide_h

    if min_left_x is not None and left_x < min_left_x:
        shift = min_left_x - left_x
        left_x += shift
        right_x += shift
        center_x += shift
        if right_x > frame_w - 20:
            overshoot = right_x - (frame_w - 20)
            left_x -= overshoot
            right_x -= overshoot
            center_x -= overshoot

    head_radius_x = int(guide_w * 0.14)
    head_radius_y = int(guide_h * 0.155)
    head_center = (center_x, top_y + head_radius_y + 10)

    neck_top_y = head_center[1] + head_radius_y - int(guide_h * 0.02)
    neck_base_y = top_y + int(guide_h * 0.30)
    shoulder_y = top_y + int(guide_h * 0.38)
    chest_y = top_y + int(guide_h * 0.48)
    waist_y = top_y + int(guide_h * 0.73)
    hip_y = bottom_y - int(guide_h * 0.02)
    neck_half_w = int(guide_w * 0.10)
    shoulder_half_w = int(guide_w * 0.41)
    chest_half_w = int(guide_w * 0.46)
    waist_half_w = int(guide_w * 0.42)
    arm_outer_half_w = int(guide_w * 0.54)
    wrist_outer_half_w = int(guide_w * 0.52)
    wrist_inner_half_w = int(guide_w * 0.37)
    ear_radius_x = int(guide_w * 0.035)
    ear_radius_y = int(guide_h * 0.055)
    ear_y = head_center[1] + int(guide_h * 0.005)

    roi_pad_x = int(guide_w * 0.08)
    roi_pad_y = int(guide_h * 0.04)
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
        "ear_radius_x": ear_radius_x,
        "ear_radius_y": ear_radius_y,
        "ear_y": ear_y,
        "neck_top_y": neck_top_y,
        "neck_base_y": neck_base_y,
        "shoulder_y": shoulder_y,
        "chest_y": chest_y,
        "waist_y": waist_y,
        "hip_y": hip_y,
        "waist_half_w": waist_half_w,
        "shoulder_half_w": shoulder_half_w,
        "neck_half_w": neck_half_w,
        "chest_half_w": chest_half_w,
        "arm_outer_half_w": arm_outer_half_w,
        "wrist_outer_half_w": wrist_outer_half_w,
        "wrist_inner_half_w": wrist_inner_half_w,
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
    left_ear_center = (
        center_x - guide_geometry["head_radius_x"] - guide_geometry["ear_radius_x"] + 6,
        guide_geometry["ear_y"],
    )
    right_ear_center = (
        center_x + guide_geometry["head_radius_x"] + guide_geometry["ear_radius_x"] - 6,
        guide_geometry["ear_y"],
    )
    cv2.ellipse(
        frame,
        left_ear_center,
        (guide_geometry["ear_radius_x"], guide_geometry["ear_radius_y"]),
        0,
        80,
        280,
        (240, 240, 240),
        3,
        cv2.LINE_AA,
    )
    cv2.ellipse(
        frame,
        right_ear_center,
        (guide_geometry["ear_radius_x"], guide_geometry["ear_radius_y"]),
        0,
        -100,
        100,
        (240, 240, 240),
        3,
        cv2.LINE_AA,
    )

    left_outline = np.array(
        [
            (center_x - guide_geometry["neck_half_w"], guide_geometry["neck_top_y"]),
            (center_x - guide_geometry["neck_half_w"], guide_geometry["neck_base_y"]),
            (center_x - int(guide_geometry["shoulder_half_w"] * 0.64), guide_geometry["shoulder_y"] - 14),
            (center_x - guide_geometry["shoulder_half_w"], guide_geometry["shoulder_y"]),
            (center_x - guide_geometry["chest_half_w"], guide_geometry["chest_y"]),
            (center_x - guide_geometry["arm_outer_half_w"], guide_geometry["waist_y"] - 40),
            (center_x - guide_geometry["arm_outer_half_w"], guide_geometry["waist_y"] + 28),
            (center_x - guide_geometry["wrist_outer_half_w"], guide_geometry["hip_y"]),
            (center_x - guide_geometry["wrist_inner_half_w"], guide_geometry["hip_y"]),
            (center_x - guide_geometry["waist_half_w"], guide_geometry["waist_y"]),
            (center_x - int(guide_geometry["chest_half_w"] * 0.94), guide_geometry["chest_y"] + 42),
            (center_x - int(guide_geometry["shoulder_half_w"] * 0.58), guide_geometry["shoulder_y"] + 6),
            (center_x - guide_geometry["neck_half_w"], guide_geometry["neck_base_y"]),
        ],
        dtype=np.int32,
    )
    right_outline = np.array(
        [(2 * center_x - x, y) for x, y in left_outline[::-1]],
        dtype=np.int32,
    )
    cv2.polylines(frame, [left_outline], isClosed=False, color=(240, 240, 240), thickness=3, lineType=cv2.LINE_AA)
    cv2.polylines(frame, [right_outline], isClosed=False, color=(240, 240, 240), thickness=3, lineType=cv2.LINE_AA)
    cv2.line(
        frame,
        (center_x - guide_geometry["wrist_inner_half_w"], guide_geometry["hip_y"]),
        (center_x + guide_geometry["wrist_inner_half_w"], guide_geometry["hip_y"]),
        (240, 240, 240),
        3,
        cv2.LINE_AA,
    )

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


_image_cache = {}


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
        else:
            image_h, image_w, _ = raw.shape
            scale = min(width / image_w, height / image_h)
            resized = cv2.resize(raw, (int(image_w * scale), int(image_h * scale)))
            canvas = np.full((height, width, 3), 30, dtype=np.uint8)
            offset_y = (height - resized.shape[0]) // 2
            offset_x = (width - resized.shape[1]) // 2
            canvas[offset_y:offset_y + resized.shape[0], offset_x:offset_x + resized.shape[1]] = resized
            _image_cache[image_path] = canvas

    cached = _image_cache.get(image_path)
    if cached is None:
        cv2.rectangle(frame, (x, y), (x + width, y + height), (55, 55, 55), thickness=-1)
    else:
        frame[y:y + height, x:x + width] = cached
    cv2.rectangle(frame, (x, y), (x + width, y + height), (210, 210, 210), thickness=2)


def get_available_careers():
    professionals = {row[4] for row in get_all_professionals() if row[4]}
    return [career for career in FEATURED_CAREERS if career in professionals]


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
    x1, y1, x2, y2 = guide_geometry["match_roi"]
    return frame[y1:y2, x1:x2]


def draw_intro_screen(frame_shape, seconds_remaining):
    frame = np.full(frame_shape, 22, dtype=np.uint8)
    h, w, _ = frame_shape
    seconds_display = max(0, int(seconds_remaining + 0.999))

    cv2.rectangle(frame, (70, 70), (w - 70, h - 70), (28, 28, 28), thickness=-1)
    cv2.rectangle(frame, (70, 70), (w - 70, h - 70), (220, 220, 220), thickness=2)

    cv2.putText(
        frame,
        f"Starts in: {seconds_display}",
        (w - 260, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )

    draw_text_block(
        frame,
        "Welcome to the Quantum Career Smart Mirror",
        110,
        145,
        max_chars=28,
        line_height=34,
        color=(255, 255, 255),
        max_lines=2,
        scale=INTRO_TITLE_SCALE,
        thickness=2,
    )

    draw_text_block(
        frame,
        "This device lets you explore quantum careers using hand gestures and live face matching.",
        110,
        216,
        max_chars=42,
        line_height=26,
        color=(220, 220, 220),
        max_lines=4,
        scale=INTRO_SUBTITLE_SCALE,
        thickness=1,
    )

    cv2.putText(
        frame,
        "How to Use It",
        (110, 320),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    draw_text_block(
        frame,
        "1. Wait for the career selection screen.\n2. Use your hand to move the cursor.\n3. Hover over a quantum career for about 1.5 seconds.\n4. Look at the camera so the system can match your face.\n5. Read the matched professional profile on screen.",
        110,
        352,
        max_chars=43,
        line_height=23,
        color=(220, 220, 220),
        max_lines=8,
        scale=0.52,
        thickness=1,
    )

    draw_text_block(
        frame,
        "Career selection will begin automatically after the countdown.",
        110,
        h - 110,
        max_chars=44,
        line_height=22,
        color=(220, 220, 220),
        max_lines=2,
        scale=0.50,
        thickness=1,
    )

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


def main():
    initialize_database()
    visible_ratios = compute_visible_ratios()
    ui_layout_config = build_ui_layout_config(visible_ratios)
    window_w, window_h = get_window_size()
    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_TITLE, window_w, window_h)

    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return

    tracker = HandTracker(max_num_hands=1)
    careers = get_available_careers()
    ui = HoverSelectUI(
        dwell_seconds=1.5,
        smoothing_alpha=0.25,
        cursor_radius=10,
        button_labels=careers,
        header_text="Choose a quantum career to begin",
        layout_config=ui_layout_config,
    )

    try:
        embedder = create_embedder(MATCH_BACKEND)
    except Exception as exc:
        print(f"ERROR: Could not initialize embedding backend: {exc}")
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()
        return

    state = STATE_SELECT_CAREER
    intro_start_t = time.time()
    state = STATE_INTRO
    selected_career = None
    matching_status = "Waiting to start matching."
    matched_professional = None
    matched_test_name = None
    last_match_t = 0.0
    allowed_professional_ids = []

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)
            display_frame = prepare_camera_frame(frame, visible_ratios)
            h, w, _ = display_frame.shape

            if state == STATE_INTRO:
                seconds_remaining = max(0.0, INTRO_DURATION_SECONDS - (time.time() - intro_start_t))
                intro_frame = draw_intro_screen(display_frame.shape, seconds_remaining)
                cv2.imshow(WINDOW_TITLE, rotate_output_frame(intro_frame))
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    break
                if seconds_remaining <= 0.0:
                    state = STATE_SELECT_CAREER
                continue

            if state == STATE_PROFILE:
                profile_frame = draw_profile_screen(display_frame.shape, matched_professional, selected_career, matched_test_name)
                cv2.imshow(WINDOW_TITLE, rotate_output_frame(profile_frame))
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    break
                if key == ord("r"):
                    state = STATE_SELECT_CAREER
                    selected_career = None
                    matched_professional = None
                    matched_test_name = None
                    ui.set_buttons(careers, "Choose a quantum career to begin")
                    ui.set_layout_config(ui_layout_config)
                continue

            if state == STATE_SELECT_CAREER:
                tip_norm = tracker.get_index_tip_norm(display_frame)
                ui.update_cursor_from_norm(tip_norm, w, h)
                events = ui.update_and_draw(display_frame)
                menu_right_edge = get_menu_right_edge(ui)
                min_left_x = None if menu_right_edge is None else menu_right_edge + TORSO_GUIDE_MENU_CLEARANCE_PX
                guide_geometry = get_torso_guide_geometry(w, h, min_left_x=min_left_x)
                draw_torso_guide(display_frame, guide_geometry)
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
                        state_changed = True
                        break

                if state_changed:
                    draw_matching_overlay(display_frame, selected_career, matching_status, visible_ratios)
            elif state == STATE_MATCHING:
                menu_right_edge = get_menu_right_edge(ui)
                min_left_x = None if menu_right_edge is None else menu_right_edge + TORSO_GUIDE_MENU_CLEARANCE_PX
                guide_geometry = get_torso_guide_geometry(w, h, min_left_x=min_left_x)
                draw_torso_guide(display_frame, guide_geometry, "Keep your face and torso inside the guide")
                now = time.time()
                if now - last_match_t >= MATCH_INTERVAL_SECONDS:
                    last_match_t = now
                    try:
                        match_region = extract_match_region(display_frame, guide_geometry)
                        result = embedder.embed_bgr_image(match_region)
                        matches = find_best_database_matches(
                            result.embedding,
                            result.model_name,
                            top_k=TOP_K_MATCHES,
                            allowed_professional_ids=allowed_professional_ids,
                        )
                        if matches:
                            source_professional = matches[0]["professional"]
                            matched_professional = source_professional
                            matched_test_name = source_professional[1]
                            state = STATE_PROFILE
                        else:
                            matching_status = (
                                f"No enrolled face matches are available for {selected_career}. "
                                "Choose a career that has an enrolled profile."
                            )
                    except Exception as exc:
                        matching_status = f"Looking for a face... ({exc})"
                draw_matching_overlay(display_frame, selected_career, matching_status, visible_ratios)

            cv2.imshow(WINDOW_TITLE, rotate_output_frame(display_frame))
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if state == STATE_MATCHING and key == ord("r"):
                state = STATE_SELECT_CAREER
                selected_career = None
                ui.set_layout_config(ui_layout_config)
                ui.set_buttons(careers, "Choose a quantum career to begin")

    finally:
        embedder.close()
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
