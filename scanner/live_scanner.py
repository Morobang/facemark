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
CAMERA_INDEX = 0       # change to 1 if default camera doesn't open

# ── Colors (BGR) ──────────────────────────────────────────────────────────────
GREEN  = (0, 220, 80)
RED    = (0, 60, 220)
WHITE  = (255, 255, 255)
YELLOW = (0, 200, 255)


def draw_face_box(frame, result: dict):
    """Draw bounding box and name tag on the frame."""
    if not result.get("location"):
        return frame

    top, right, bottom, left = result["location"]
    color = GREEN if result["recognized"] else RED

    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

    label = result.get("full_name") or "Unknown"
    if result.get("confidence"):
        label += f"  {int(result['confidence'] * 100)}%"

    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.65, 1)
    cv2.rectangle(frame, (left, bottom - th - 10), (left + tw + 8, bottom), color, -1)
    cv2.putText(frame, label, (left + 4, bottom - 4),
                cv2.FONT_HERSHEY_DUPLEX, 0.65, WHITE, 1)

    return frame


def draw_status_bar(frame, status: str, count: int):
    """Top bar showing org name and attendance count."""
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 48), (20, 20, 20), -1)
    cv2.putText(frame, f"{ORG_NAME} — Attendance System",
                (12, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 180, 180), 1)
    cv2.putText(frame, f"Today: {count} present",
                (12, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.52, GREEN, 1)
    (tw, _), _ = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)
    cv2.putText(frame, status, (w - tw - 12, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, YELLOW, 1)
    return frame


def print_attendance(engine: FaceEngine):
    records = engine.get_today_attendance()
    print(f"\n{'='*50}")
    print(f"  TODAY'S ATTENDANCE  ({len(records)} present)")
    print(f"{'='*50}")
    if not records:
        print("  No attendance marked yet.")
    for r in records:
        print(f"  {r['time_in']}  {r['full_name']:<25} [{r['group_label']}]")
    print(f"{'='*50}\n")


def register_mode(engine: FaceEngine, frame):
    """CLI prompt to register the face in the current frame."""
    print("\n─── REGISTER NEW MEMBER ───")
    member_id   = input("Member ID (e.g. STU042): ").strip()
    full_name   = input("Full Name: ").strip()
    group_label = input("Group (e.g. Grade 11): ").strip()
    result = engine.register_member(
        member_id=member_id,
        full_name=full_name,
        group_label=group_label,
        frame=frame.copy()
    )
    print(f"→ {result['message']}\n")


def main():
    print(f"\n  {ORG_NAME} — FACE ATTENDANCE SCANNER")
    print("  Q = Quit  |  R = Register  |  S = Show today\n")

    engine = FaceEngine()
    cap    = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        logger.error(f"Could not open camera {CAMERA_INDEX}. Try changing CAMERA_INDEX.")
        return

    last_scan     = 0
    last_result   = {"recognized": False, "message": "Scanning...", "location": None}
    status        = "Ready"
    count         = len(engine.get_today_attendance())

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to read from camera.")
            break

        now = time.time()

        # Run recognition every SCAN_INTERVAL seconds
        if now - last_scan >= SCAN_INTERVAL:
            last_result = engine.recognize_and_mark(frame)
            last_scan   = now
            count       = len(engine.get_today_attendance())

            if last_result["recognized"]:
                att = last_result.get("attendance", {})
                if att.get("already_marked"):
                    status = f"Already marked — {last_result['full_name']}"
                else:
                    status = f"Marked — {last_result['full_name']}"
            else:
                status = last_result.get("message", "")

        draw_face_box(frame, last_result)
        draw_status_bar(frame, status, count)
        cv2.imshow("Facemark — Attendance Scanner", frame)

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