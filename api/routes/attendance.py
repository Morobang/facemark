"""
api/routes/attendance.py
------------------------
Endpoints for recognising faces and querying attendance.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from datetime import date
import numpy as np
import cv2
import api.main as state

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def upload_to_frame(file: UploadFile) -> np.ndarray:
    contents = file.file.read()
    arr      = np.frombuffer(contents, np.uint8)
    frame    = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    return frame


@router.post("/recognize")
async def recognize(photo: UploadFile = File(...)):
    """
    Send a webcam snapshot.
    Returns the recognised member and marks their attendance.
    """
    frame  = upload_to_frame(photo)
    result = state.engine.recognize_and_mark(frame)
    return result


@router.get("/today")
def today():
    return {
        "date":    date.today().isoformat(),
        "records": state.engine.get_today_attendance()
    }


@router.get("/range")
def range_report(from_date: str, to_date: str):
    """
    Query: /attendance/range?from_date=2026-01-01&to_date=2026-01-31
    """
    try:
        from database.init_db import init_db
        import sqlite3
        conn = init_db()
        cur  = conn.cursor()
        cur.execute("""
            SELECT m.member_id, m.full_name, m.group_label, a.date, a.time_in
            FROM   attendance a
            JOIN   members    m ON m.member_id = a.member_id
            WHERE  a.date BETWEEN ? AND ?
            ORDER  BY a.date, a.time_in
        """, (from_date, to_date))
        records = [dict(row) for row in cur.fetchall()]
        conn.close()
        return {"from": from_date, "to": to_date, "records": records}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))