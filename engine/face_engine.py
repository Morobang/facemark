"""
engine/face_engine.py
---------------------
Core face recognition engine for Facemark.
Handles registration, recognition, and attendance marking.

All other modules (API, scanner) import from here.
Never put web framework or camera code in this file.
"""

import face_recognition
import cv2
import numpy as np
import pickle
import os
from datetime import datetime, date
from loguru import logger

from config.settings import (
    FACE_TOLERANCE,
    FACE_MODEL,
    ENCODINGS_PATH,
    DB_PATH,
)
from database.init_db import init_db


class FaceEngine:
    """
    The core engine. One instance is created and shared across
    the entire application — whether that's the API or the scanner.
    """

    def __init__(self):
        self.conn = init_db()
        self.known_encodings: dict[str, np.ndarray] = {}
        self.known_ids:       list[str]             = []
        self.known_vecs:      list[np.ndarray]      = []
        self._load_encodings()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load_encodings(self):
        """Load face vectors from disk into memory."""
        if os.path.exists(ENCODINGS_PATH):
            with open(ENCODINGS_PATH, "rb") as f:
                data = pickle.load(f)
            self.known_encodings = data.get("encodings", {})
            self._rebuild_lists()
            logger.info(f"Loaded {len(self.known_encodings)} face encodings.")
        else:
            logger.info("No encodings file found — starting fresh.")

    def _save_encodings(self):
        """Persist face vectors to disk."""
        os.makedirs(os.path.dirname(ENCODINGS_PATH), exist_ok=True)
        with open(ENCODINGS_PATH, "wb") as f:
            pickle.dump({"encodings": self.known_encodings}, f)
        logger.info(f"Saved {len(self.known_encodings)} encodings to disk.")

    def _rebuild_lists(self):
        """Rebuild parallel lists used for fast batch comparison."""
        self.known_ids  = list(self.known_encodings.keys())
        self.known_vecs = list(self.known_encodings.values())

    # ── Registration ──────────────────────────────────────────────────────────

    def register_member(
        self,
        member_id:   str,
        full_name:   str,
        group_label: str = "",
        image_path:  str = None,
        frame:       np.ndarray = None,
    ) -> dict:
        """
        Register a new member. Provide either image_path or frame.

        Returns:
            {"success": bool, "message": str}
        """
        # 1. Load image
        if image_path:
            img_bgr = cv2.imread(image_path)
            if img_bgr is None:
                return {"success": False, "message": f"Cannot read image: {image_path}"}
        elif frame is not None:
            img_bgr = frame
        else:
            return {"success": False, "message": "Provide image_path or frame."}

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # 2. Detect face
        locations = face_recognition.face_locations(img_rgb, model=FACE_MODEL)
        if not locations:
            return {"success": False, "message": "No face detected in the image."}
        if len(locations) > 1:
            return {"success": False, "message": "Multiple faces detected — use a photo with only the member."}

        # 3. Generate encoding
        encoding = face_recognition.face_encodings(img_rgb, locations)[0]

        # 4. Check for duplicate
        if member_id in self.known_encodings:
            return {"success": False, "message": f"{member_id} is already registered."}

        # 5. Save encoding to memory and disk
        self.known_encodings[member_id] = encoding
        self._rebuild_lists()
        self._save_encodings()

        # 6. Save member record to database
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO members (member_id, full_name, group_label, photo_path)
            VALUES (?, ?, ?, ?)
            """,
            (member_id, full_name, group_label, image_path or "")
        )
        self.conn.commit()

        logger.info(f"Registered: {full_name} ({member_id})")
        return {"success": True, "message": f"{full_name} registered successfully."}

    # ── Recognition ───────────────────────────────────────────────────────────

    def recognize_face(self, frame: np.ndarray) -> dict:
        """
        Identify a face in a camera frame.

        Returns:
            {
              "recognized": bool,
              "member_id":  str | None,
              "full_name":  str | None,
              "confidence": float | None,
              "location":   tuple | None,
              "message":    str
            }
        """
        if not self.known_vecs:
            return {
                "recognized": False, "member_id": None,
                "full_name":  None,  "confidence": None,
                "location":   None,  "message": "No members registered yet."
            }

        img_rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(img_rgb, model=FACE_MODEL)

        if not locations:
            return {
                "recognized": False, "member_id": None,
                "full_name":  None,  "confidence": None,
                "location":   None,  "message": "No face detected."
            }

        loc      = locations[0]
        encoding = face_recognition.face_encodings(img_rgb, [loc])[0]

        # Compare against all known encodings
        distances = face_recognition.face_distance(self.known_vecs, encoding)
        best_idx  = int(np.argmin(distances))
        best_dist = float(distances[best_idx])

        if best_dist > FACE_TOLERANCE:
            return {
                "recognized": False, "member_id": None,
                "full_name":  None,  "confidence": round(1 - best_dist, 3),
                "location":   loc,   "message": "Face not recognised."
            }

        member_id  = self.known_ids[best_idx]
        full_name  = self._get_member_name(member_id)
        confidence = round(1 - best_dist, 3)

        logger.info(f"Recognised: {full_name} (confidence={confidence})")
        return {
            "recognized": True,
            "member_id":  member_id,
            "full_name":  full_name,
            "confidence": confidence,
            "location":   loc,
            "message":    f"Welcome, {full_name}!"
        }

    def _get_member_name(self, member_id: str) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT full_name FROM members WHERE member_id = ?", (member_id,))
        row = cur.fetchone()
        return row["full_name"] if row else member_id

    # ── Attendance ────────────────────────────────────────────────────────────

    def mark_attendance(self, member_id: str) -> dict:
        """
        Mark a member as present today.
        Safe to call multiple times — duplicate entries are ignored.
        """
        today    = date.today().isoformat()
        time_now = datetime.now().strftime("%H:%M:%S")
        cur      = self.conn.cursor()

        cur.execute(
            "SELECT time_in FROM attendance WHERE member_id = ? AND date = ?",
            (member_id, today)
        )
        existing = cur.fetchone()

        if existing:
            return {
                "success": True,
                "already_marked": True,
                "message": f"Already marked at {existing['time_in']}."
            }

        cur.execute(
            "INSERT INTO attendance (member_id, date, time_in) VALUES (?, ?, ?)",
            (member_id, today, time_now)
        )
        self.conn.commit()

        logger.info(f"Attendance marked: {member_id} at {time_now}")
        return {
            "success": True,
            "already_marked": False,
            "message": f"Attendance marked at {time_now}."
        }

    def recognize_and_mark(self, frame: np.ndarray) -> dict:
        """One shot — recognise and mark attendance if found."""
        result = self.recognize_face(frame)
        if result["recognized"]:
            result["attendance"] = self.mark_attendance(result["member_id"])
        return result

    # ── Reporting ─────────────────────────────────────────────────────────────

    def get_today_attendance(self) -> list:
        today = date.today().isoformat()
        cur   = self.conn.cursor()
        cur.execute("""
            SELECT m.member_id, m.full_name, m.group_label, a.time_in
            FROM   attendance a
            JOIN   members    m ON m.member_id = a.member_id
            WHERE  a.date = ?
            ORDER  BY a.time_in
        """, (today,))
        return [dict(row) for row in cur.fetchall()]

    def get_all_members(self) -> list:
        cur = self.conn.cursor()
        cur.execute("SELECT member_id, full_name, group_label, registered_at FROM members ORDER BY full_name")
        return [dict(row) for row in cur.fetchall()]

    def close(self):
        self.conn.close()