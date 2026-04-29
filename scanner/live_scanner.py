"""
scanner/live_scanner.py
-----------------------
Standalone camera app for the entrance station.
Run this on the PC connected to the entrance webcam.

Controls:
    Q — quit
    R — register a new member using the current camera frame
    S — print today's attendance to terminal
"""

import cv2
import time
from loguru import logger

from engine.face_engine import FaceEngine
from config.settings import SCAN_INTERVAL, ORG_NAME

# ── Config ────────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0  # change to 1 if default camera doesn't open

# ── Colors (BGR) ──────────────────────────────────────────────────────────────
GREEN = (0, 220, 80)
RED = (0, 60, 220)
WHITE = (255, 255, 255)
YELLOW = (0, 200, 255)
DARK = (20, 20, 20)
LIGHT = (180, 180, 180)


def draw_face_box(frame, result: dict):
    """Draw bounding box and label around detected face."""
    if not result.get("location"):
        return frame

    top, right, bottom, left = result["location"]

    color = GREEN if result.get("recognized") else RED

    # Face rectangle
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

    # Label
    label = result.get("full_name") or "Unknown"

    if result.get("confidence"):
        label += f"  {int(result['confidence'] * 100)}%"

    (tw, th), _ = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_DUPLEX,
        0.65,
        1
    )

    cv2.rectangle(
        frame,
        (left, bottom - th - 10),
        (left + tw + 8, bottom),
        color,
        -1
    )

    cv2.putText(
        frame,
        label,
        (left + 4, bottom - 4),
        cv2.FONT_HERSHEY_DUPLEX,
        0.65,
        WHITE,
        1
    )

    return frame


def draw_status_bar(frame, status: str, count: int):
    """Top status bar."""
    h, w = frame.shape[:2]

    cv2.rectangle(frame, (0, 0), (w, 50), DARK, -1)

    cv2.putText(
        frame,
        f"{ORG_NAME} — Attendance System",
        (12, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        LIGHT,
        1
    )

    cv2.putText(
        frame,
        f"Present Today: {count}",
        (12, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        GREEN,
        1
    )

    (tw, _), _ = cv2.getTextSize(
        status,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        1
    )

    cv2.putText(
        frame,
        status,
        (w - tw - 12, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        YELLOW,
        1
    )

    return frame


def draw_controls_bar(frame):
    """Bottom controls/help bar."""
    h, w = frame.shape[:2]

    controls = "Q = Quit    R = Register    S = Show Attendance"

    (tw, th), _ = cv2.getTextSize(
        controls,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        1
    )

    cv2.rectangle(
        frame,
        (0, h - th - 18),
        (w, h),
        DARK,
        -1
    )

    cv2.putText(
        frame,
        controls,
        (w // 2 - tw // 2, h - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        LIGHT,
        1
    )

    return frame


def print_attendance(engine: FaceEngine):
    """Print today's attendance in terminal."""
    records = engine.get_today_attendance()

    print(f"\n{'=' * 60}")
    print(f" TODAY'S ATTENDANCE ({len(records)} present)")
    print(f"{'=' * 60}")

    if not records:
        print(" No attendance marked yet.")

    for r in records:
        print(
            f" {r['time_in']}  "
            f"{r['full_name']:<25} "
            f"[{r['group_label']}]"
        )

    print(f"{'=' * 60}\n")


def register_mode(engine: FaceEngine, frame):
    """Register a new member using current frame."""

    print("\n── REGISTER NEW MEMBER ──")

    member_id = input("Member ID (e.g. STU042): ").strip()
    full_name = input("Full Name: ").strip()
    group_label = input("Group (e.g. Grade 11): ").strip()

    result = engine.register_member(
        member_id=member_id,
        full_name=full_name,
        group_label=group_label,
        frame=frame.copy()
    )

    print(f"\n→ {result['message']}\n")


def main():
    print(f"\n {ORG_NAME} — FACE ATTENDANCE SCANNER")
    print(" Q = Quit")
    print(" R = Register Member")
    print(" S = Show Today's Attendance\n")

    engine = FaceEngine()

    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        logger.error(
            f"Could not open camera index {CAMERA_INDEX}."
        )
        return

    last_scan = 0

    last_result = {
        "recognized": False,
        "message": "Scanning...",
        "location": None
    }

    status = "Ready"

    count = len(engine.get_today_attendance())

    while True:

        ret, frame = cap.read()

        if not ret:
            logger.error("Failed to read camera frame.")
            break

        # Mirror camera for natural experience
        frame = cv2.flip(frame, 1)

        now = time.time()

        # Scan every X seconds
        if now - last_scan >= SCAN_INTERVAL:

            last_result = engine.recognize_and_mark(frame)

            last_scan = now

            count = len(engine.get_today_attendance())

            if last_result.get("recognized"):

                attendance = last_result.get("attendance", {})

                if attendance.get("already_marked"):
                    status = (
                        f"Already marked — "
                        f"{last_result['full_name']}"
                    )
                else:
                    status = (
                        f"Marked — "
                        f"{last_result['full_name']}"
                    )

            else:
                status = last_result.get(
                    "message",
                    "No face detected"
                )

        # UI
        draw_face_box(frame, last_result)
        draw_status_bar(frame, status, count)
        draw_controls_bar(frame)

        cv2.imshow(
            "Facemark — Attendance Scanner",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord("r"):
            register_mode(engine, frame)

        elif key == ord("s"):
            print_attendance(engine)

    cap.release()
    cv2.destroyAllWindows()
    engine.close()

    print("Scanner closed.")


if __name__ == "__main__":
    main()