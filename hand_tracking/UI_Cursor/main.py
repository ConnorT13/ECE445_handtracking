import cv2
from hand_tracker import HandTracker
from user_interface import HoverSelectUI
from send_data import ArduinoController


def main():
    # cap = cv2.VideoCapture(0, cv2.CAP_DCAPSHOW) # WINDOWS Videocapture
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION) # MAC Videocapture

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return

    tracker = HandTracker(max_num_hands=1)
    ui = HoverSelectUI(dwell_seconds=1.5, smoothing_alpha=0.25, cursor_radius=10)
    arduino = ArduinoController(port='COM5')

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            # mirror view
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Hand tracking -> cursor update
            tip_norm = tracker.get_index_tip_norm(frame)
            ui.update_cursor_from_norm(tip_norm, w, h)

            # UI update + draw
            events = ui.update_and_draw(frame)
            for e in events:
                print(e)

                # Map UI events to Arduino commands
                if e == "selected:Toggle Overlay":
                    arduino.send_cmd(0x01)
                elif e == "selected:Start Demo Mode":
                    arduino.send_cmd(0x02)
                elif e == "selected:Reset / Clear":
                    arduino.send_cmd(0x03)

            cv2.imshow("Hand UI Hover Select (Modular)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                break

    finally:
        tracker.close()
        arduino.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()