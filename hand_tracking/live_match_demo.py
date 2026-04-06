import time
import os

import cv2
import numpy as np

from hand_tracking.UI_Cursor.hand_tracker import HandTracker
from hand_tracking.UI_Cursor.user_interface import HoverSelectUI
from hand_tracking.database.db_init import initialize_database
from hand_tracking.matching.embedder import create_embedder
from hand_tracking.matching.match import find_best_database_matches


WINDOW_TITLE = "Smart Mirror Live Match Demo"
MATCH_BACKEND = "insightface"
MATCH_INTERVAL_SECONDS = 1.5
TOP_K_MATCHES = 3


def wrap_text(text, max_chars):
    words = text.split()
    if not words:
        return []

    lines = []
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


def draw_text_block(frame, text, origin_x, origin_y, max_chars, line_height, color, scale=0.55, thickness=1):
    for line_index, line in enumerate(wrap_text(text, max_chars)):
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


def draw_text_block_limited(
    frame,
    text,
    origin_x,
    origin_y,
    max_chars,
    line_height,
    color,
    max_lines,
    scale=0.55,
    thickness=1,
):
    lines = wrap_text(text, max_chars)
    if len(lines) > max_lines:
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


_image_cache = {}

def draw_profile_image(frame, image_path, x, y, width, height):
    if not image_path or not os.path.exists(image_path):
        # ... placeholder drawing unchanged ...
        return

    if image_path not in _image_cache:
        raw = cv2.imread(image_path)
        if raw is None:
            _image_cache[image_path] = None
        else:
            image_h, image_w, _ = raw.shape
            scale = min(width / image_w, height / image_h)
            resized = cv2.resize(raw, (int(image_w * scale), int(image_h * scale)))
            canvas = np.full((height, width, 3), 35, dtype=np.uint8)
            offset_y = (height - resized.shape[0]) // 2
            offset_x = (width - resized.shape[1]) // 2
            canvas[offset_y:offset_y + resized.shape[0], offset_x:offset_x + resized.shape[1]] = resized
            _image_cache[image_path] = canvas

    cached = _image_cache.get(image_path)
    if cached is None:
        cv2.rectangle(frame, (x, y), (x + width, y + height), (70, 70, 70), thickness=-1)
        return

    frame[y:y + height, x:x + width] = cached
    cv2.rectangle(frame, (x, y), (x + width, y + height), (220, 220, 220), thickness=2)


def draw_match_panel(frame, demo_active, status_text, matches):
    panel_x = 420
    panel_y = 80
    panel_w = 800
    panel_h = 560

    cv2.rectangle(
        frame,
        (panel_x, panel_y),
        (panel_x + panel_w, panel_y + panel_h),
        (35, 35, 35),
        thickness=-1,
    )
    cv2.rectangle(
        frame,
        (panel_x, panel_y),
        (panel_x + panel_w, panel_y + panel_h),
        (220, 220, 220),
        thickness=2,
    )

    title = "Face Matching Active" if demo_active else "Standby"
    cv2.putText(
        frame,
        title,
        (panel_x + 20, panel_y + 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    draw_text_block_limited(
        frame,
        status_text,
        panel_x + 20,
        panel_y + 68,
        max_chars=68,
        line_height=22,
        color=(210, 210, 210),
        max_lines=2,
        scale=0.58,
        thickness=1,
    )

    if not matches:
        placeholder = "Hover over 'Start Demo Mode' to begin matching."
        if demo_active:
            placeholder = "Waiting for a detectable face."
        cv2.putText(
            frame,
            placeholder,
            (panel_x + 20, panel_y + 125),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (180, 180, 180),
            2,
            cv2.LINE_AA,
        )
        return

    top_match = matches[0]
    professional = top_match["professional"]
    name = professional[1]
    title_text = professional[2]
    organization = professional[3] or "Unknown organization"
    quantum_area = professional[4] or "Unknown quantum area"
    short_bio = professional[5] or "No short bio available."
    fun_fact = professional[8] or "No fun fact available."
    image_path = professional[7]

    image_x = panel_x + 20
    image_y = panel_y + 95
    image_w = 240
    image_h = 240
    draw_profile_image(frame, image_path, image_x, image_y, image_w, image_h)

    text_x = image_x + image_w + 24
    cv2.putText(
        frame,
        name,
        (text_x, image_y + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.95,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    draw_text_block_limited(
        frame,
        title_text,
        text_x,
        image_y + 52,
        max_chars=28,
        line_height=22,
        color=(225, 225, 225),
        max_lines=2,
        scale=0.6,
        thickness=1,
    )
    draw_text_block_limited(
        frame,
        organization,
        text_x,
        image_y + 100,
        max_chars=32,
        line_height=20,
        color=(205, 205, 205),
        max_lines=2,
        scale=0.54,
        thickness=1,
    )
    draw_text_block_limited(
        frame,
        f"Area: {quantum_area}",
        text_x,
        image_y + 140,
        max_chars=32,
        line_height=20,
        color=(205, 205, 205),
        max_lines=2,
        scale=0.54,
        thickness=1,
    )
    cv2.putText(
        frame,
        f"Match score: {top_match['score']:.4f}",
        (text_x, image_y + 186),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "Bio",
        (text_x, image_y + 218),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    draw_text_block_limited(
        frame,
        short_bio,
        text_x,
        image_y + 246,
        max_chars=34,
        line_height=24,
        color=(220, 220, 220),
        max_lines=3,
        scale=0.55,
        thickness=1,
    )

    cv2.putText(
        frame,
        "Fun Fact",
        (panel_x + 20, panel_y + 380),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    draw_text_block_limited(
        frame,
        fun_fact,
        panel_x + 20,
        panel_y + 408,
        max_chars=58,
        line_height=24,
        color=(220, 220, 220),
        max_lines=2,
        scale=0.58,
        thickness=1,
    )

    cv2.putText(
        frame,
        "Top Matches",
        (panel_x + 20, panel_y + 488),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    for index, match in enumerate(matches, start=1):
        ranked_professional = match["professional"]
        row_y = panel_y + 522 + (index - 1) * 24
        draw_text_block_limited(
            frame,
            f"{index}. {ranked_professional[1]} ({match['score']:.4f})",
            panel_x + 20,
            row_y,
            max_chars=54,
            line_height=18,
            color=(210, 210, 210),
            max_lines=1,
            scale=0.5,
            thickness=1,
        )


def main():
    initialize_database()

    # cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

    # wsl videocapture
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return

    tracker = HandTracker(max_num_hands=1)
    ui = HoverSelectUI(dwell_seconds=1.5, smoothing_alpha=0.25, cursor_radius=10)

    try:
        embedder = create_embedder(MATCH_BACKEND)
    except Exception as exc:
        print(f"ERROR: Could not initialize embedding backend: {exc}")
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()
        return

    demo_active = False
    last_match_t = 0.0
    last_status_text = "Hover over Start Demo Mode to begin."
    last_matches = []

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            tip_norm = tracker.get_index_tip_norm(frame)
            ui.update_cursor_from_norm(tip_norm, w, h)

            events = ui.update_and_draw(frame)
            for event in events:
                if event == "Selected: Start Demo Mode":
                    demo_active = not demo_active
                    if demo_active:
                        last_status_text = "Demo started. Looking for a face..."
                    else:
                        last_status_text = "Demo stopped. Hover to start again."
                        last_matches = []
                elif event == "Selected: Reset / Clear":
                    demo_active = False
                    last_status_text = "Reset complete. Standing by."
                    last_matches = []

            now = time.time()
            if demo_active and now - last_match_t >= MATCH_INTERVAL_SECONDS:
                last_match_t = now
                try:
                    result = embedder.embed_bgr_image(frame)
                    matches = find_best_database_matches(
                        result.embedding, result.model_name, top_k=TOP_K_MATCHES
                    )
                    if matches:
                        last_matches = matches
                        last_status_text = "Latest face match results:"
                    else:
                        last_status_text = "No face detected — holding last match."
                except Exception as exc:
                    last_status_text = f"Matching paused: {exc}"

            draw_match_panel(frame, demo_active, last_status_text, last_matches)

            cv2.imshow(WINDOW_TITLE, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break

    finally:
        embedder.close()
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
