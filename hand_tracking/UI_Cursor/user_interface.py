import cv2
import time


DEFAULT_LAYOUT_CONFIG = {
    "VISIBLE_WIDTH_RATIO": 1.0,
    "VISIBLE_HEIGHT_RATIO": 1.0,
    "UI_SCALE": 1.0,
    "UI_LEFT_MARGIN": 0.04,
    "UI_TOP_MARGIN": 0.06,
    "UI_ITEM_SPACING": 0.025,
    "FONT_SCALE": 0.8,
    "HEADER_SCALE": 0.85,
    "FPS_SCALE": 0.85,
    "BUTTON_WIDTH_RATIO": 0.42,
    "BUTTON_HEIGHT_RATIO": 0.09,
    "BUTTON_TEXT_PADDING_X": 12,
    "BUTTON_TEXT_PADDING_Y": 8,
    "PROGRESS_RADIUS": 38,
    "PROGRESS_THICKNESS": 6,
}


def compute_safe_area(frame_w: int, frame_h: int, visible_width_ratio: float, visible_height_ratio: float):
    safe_w = int(round(frame_w * visible_width_ratio))
    safe_h = int(round(frame_h * visible_height_ratio))
    safe_x = max(0, (frame_w - safe_w) // 2)
    safe_y = max(0, (frame_h - safe_h) // 2)
    return safe_x, safe_y, safe_w, safe_h


def layout_menu_items(frame_w: int, frame_h: int, button_count: int, layout_config: dict):
    safe_x, safe_y, safe_w, safe_h = compute_safe_area(
        frame_w,
        frame_h,
        layout_config["VISIBLE_WIDTH_RATIO"],
        layout_config["VISIBLE_HEIGHT_RATIO"],
    )

    ui_scale = layout_config["UI_SCALE"]
    button_w = int(round(safe_w * layout_config["BUTTON_WIDTH_RATIO"] * ui_scale))
    button_h = int(round(frame_h * layout_config["BUTTON_HEIGHT_RATIO"] * ui_scale))
    button_w = max(180, min(button_w, safe_w - 10))
    button_h = max(52, button_h)

    x0 = safe_x + int(round(safe_w * layout_config["UI_LEFT_MARGIN"]))
    y0 = safe_y + int(round(safe_h * layout_config["UI_TOP_MARGIN"]))
    gap = max(16, int(round(safe_h * layout_config["UI_ITEM_SPACING"] * ui_scale)))

    return {
        "safe_x": safe_x,
        "safe_y": safe_y,
        "safe_w": safe_w,
        "safe_h": safe_h,
        "button_w": button_w,
        "button_h": button_h,
        "x0": x0,
        "y0": y0,
        "gap": gap,
        "button_count": button_count,
    }


class Button:
    def __init__(self, label: str, x: int, y: int, w: int, h: int):
        self.label = label
        self.x, self.y, self.w, self.h = x, y, w, h
        self.toggled = False

    def contains(self, px: int, py: int) -> bool:
        return (self.x <= px <= self.x + self.w) and (self.y <= py <= self.y + self.h)

    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)


class HoverSelectUI:
    """
    Kinect-style hover-to-select UI.
    - Draws buttons
    - Draws cursor
    - If cursor hovers over a button for dwell_seconds, triggers select
    - Shows circular progress meter over hovered button
    """

    def __init__(
        self,
        dwell_seconds: float = 1.5,
        smoothing_alpha: float = 0.25,
        cursor_radius: int = 10,
        button_labels=None,
        header_text="Hover cursor over a button for 1.5s to select",
        layout_config=None,
    ):
        self.dwell_seconds = dwell_seconds
        self.smoothing_alpha = smoothing_alpha
        self.cursor_radius = cursor_radius
        self.button_labels = button_labels or [
            "Toggle Overlay",
            "Start Demo Mode",
            "Reset / Clear",
        ]
        self.header_text = header_text
        self.layout_config = dict(DEFAULT_LAYOUT_CONFIG)
        if layout_config:
            self.layout_config.update(layout_config)

        self.buttons = []
        self.hovered_idx = None
        self.hover_start_t = None

        self.cursor_x = None
        self.cursor_y = None
        self.last_hand_seen_t = None

        self.prev_t = time.time()
        self.fps = 0.0

        self._initialized_layout = False

    def init_layout(self, frame_w: int, frame_h: int):
        """Create buttons based on frame dimensions (call once when you know size)."""
        if self._initialized_layout:
            return

        layout = layout_menu_items(frame_w, frame_h, len(self.button_labels), self.layout_config)
        bw = layout["button_w"]
        bh = layout["button_h"]
        x0 = layout["x0"]
        y0 = layout["y0"]
        gap = layout["gap"]
        self.buttons = []

        for index, label in enumerate(self.button_labels):
            x = x0
            y = y0 + index * (bh + gap)
            self.buttons.append(Button(label, x, y, bw, bh))

        self._initialized_layout = True

    def set_layout_config(self, layout_config):
        self.layout_config = dict(DEFAULT_LAYOUT_CONFIG)
        if layout_config:
            self.layout_config.update(layout_config)
        self.buttons = []
        self.hovered_idx = None
        self.hover_start_t = None
        self._initialized_layout = False

    def set_buttons(self, button_labels, header_text=None):
        self.button_labels = button_labels
        if header_text is not None:
            self.header_text = header_text
        self.buttons = []
        self.hovered_idx = None
        self.hover_start_t = None
        self._initialized_layout = False

    def update_cursor_from_norm(self, tip_norm, frame_w: int, frame_h: int):
        """
        tip_norm: (x_norm, y_norm) or None
        Updates internal smoothed cursor position.
        """
        if tip_norm is None:
            # Hand lost -> stop selection
            self.hovered_idx = None
            self.hover_start_t = None
            return

        self.last_hand_seen_t = time.time()
        tx = int(tip_norm[0] * frame_w)
        ty = int(tip_norm[1] * frame_h)

        if self.cursor_x is None:
            self.cursor_x, self.cursor_y = tx, ty
        else:
            a = self.smoothing_alpha
            self.cursor_x = int((1 - a) * self.cursor_x + a * tx)
            self.cursor_y = int((1 - a) * self.cursor_y + a * ty)

        # Clamp
        self.cursor_x = max(0, min(frame_w - 1, self.cursor_x))
        self.cursor_y = max(0, min(frame_h - 1, self.cursor_y))

    def _draw_button(self, frame, btn: Button, hovered: bool):
        base = (60, 60, 60)
        hover = (90, 90, 90)
        on = (60, 120, 60)

        color = on if btn.toggled else (hover if hovered else base)

        cv2.rectangle(frame, (btn.x, btn.y), (btn.x + btn.w, btn.y + btn.h), color, thickness=-1)
        cv2.rectangle(frame, (btn.x, btn.y), (btn.x + btn.w, btn.y + btn.h), (220, 220, 220), thickness=2)

        text = btn.label + ("  [ON]" if btn.toggled else "")
        cv2.putText(
            frame,
            text,
            (
                btn.x + self.layout_config["BUTTON_TEXT_PADDING_X"],
                btn.y + btn.h // 2 + self.layout_config["BUTTON_TEXT_PADDING_Y"],
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            self.layout_config["FONT_SCALE"],
            (240, 240, 240),
            2,
            cv2.LINE_AA,
        )

    def _draw_cursor(self, frame):
        if self.cursor_x is None or self.cursor_y is None:
            return
        if self.last_hand_seen_t is None or time.time() - self.last_hand_seen_t >= 1.0:
            return
        x, y = self.cursor_x, self.cursor_y
        r = self.cursor_radius
        cv2.circle(frame, (x, y), r, (0, 255, 0), thickness=-1)
        cv2.circle(frame, (x, y), r + 6, (0, 255, 0), thickness=2)

    def _draw_progress_ring(self, frame, center, progress: float, radius: int = 38, thickness: int = 6):
        cx, cy = center
        cv2.circle(frame, (cx, cy), radius, (200, 200, 200), thickness)
        start_angle = -90
        end_angle = int(start_angle + 360 * max(0.0, min(1.0, progress)))
        cv2.ellipse(frame, (cx, cy), (radius, radius), 0, start_angle, end_angle, (0, 255, 255), thickness)
        cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)

    def _compute_hover_target(self):
        if self.cursor_x is None or self.cursor_y is None:
            return None
        for i, btn in enumerate(self.buttons):
            if btn.contains(self.cursor_x, self.cursor_y):
                return i
        return None

    def _handle_selection(self, idx: int):
        btn = self.buttons[idx]
        if btn.label == "Reset / Clear":
            for b in self.buttons:
                b.toggled = False
        else:
            btn.toggled = not btn.toggled

    def update_and_draw(self, frame):
        """
        Main UI call per frame:
        - updates hover timing
        - triggers selection
        - draws everything
        Returns: list of events (strings) if you want to hook actions later
        """
        h, w, _ = frame.shape
        self.init_layout(w, h)

        events = []

        now = time.time()

        # Determine hover target
        new_hovered = self._compute_hover_target()

        if new_hovered is None:
            self.hovered_idx = None
            self.hover_start_t = None
        else:
            if self.hovered_idx != new_hovered:
                self.hovered_idx = new_hovered
                self.hover_start_t = now

        # Draw header
        safe_x, safe_y, safe_w, _ = compute_safe_area(
            w,
            h,
            self.layout_config["VISIBLE_WIDTH_RATIO"],
            self.layout_config["VISIBLE_HEIGHT_RATIO"],
        )
        cv2.putText(
            frame,
            self.header_text,
            (safe_x + int(safe_w * self.layout_config["UI_LEFT_MARGIN"]), max(36, safe_y + 28)),
            cv2.FONT_HERSHEY_SIMPLEX,
            self.layout_config["HEADER_SCALE"],
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # Draw buttons
        for i, btn in enumerate(self.buttons):
            self._draw_button(frame, btn, hovered=(i == self.hovered_idx))

        # Cursor
        self._draw_cursor(frame)

        # Dwell progress + trigger
        if self.hovered_idx is not None and self.hover_start_t is not None:
            elapsed = now - self.hover_start_t
            progress = min(1.0, elapsed / self.dwell_seconds)

            cx, cy = self.buttons[self.hovered_idx].center()
            self._draw_progress_ring(
                frame,
                (cx, cy),
                progress,
                radius=self.layout_config["PROGRESS_RADIUS"],
                thickness=self.layout_config["PROGRESS_THICKNESS"],
            )

            if elapsed >= self.dwell_seconds:
                label = self.buttons[self.hovered_idx].label
                self._handle_selection(self.hovered_idx)
                events.append(f"selected:{label}")

                # reset so it doesn't instantly retrigger
                self.hovered_idx = None
                self.hover_start_t = None

        # FPS
        dt = now - self.prev_t
        self.prev_t = now
        if dt > 0:
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)

        cv2.putText(
            frame,
            f"FPS: {self.fps:.1f}",
            (w - 180, max(36, safe_y + 28)),
            cv2.FONT_HERSHEY_SIMPLEX,
            self.layout_config["FPS_SCALE"],
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        return events
