"""
api/routes/members.py
---------------------
Endpoints for registering and listing members.
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import numpy as np
import cv2
import api.main as state

router = APIRouter(prefix="/members", tags=["Members"])


def upload_to_frame(file: UploadFile) -> np.ndarray:
    contents = file.file.read()
    arr      = np.frombuffer(contents, np.uint8)
    frame    = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    return frame


@router.get("/")
def list_members():
    return {"members": state.engine.get_all_members()}


@router.post("/register")
async def register_member(
    member_id:   str        = Form(...),
    full_name:   str        = Form(...),
    group_label: str        = Form(""),
    photo:       UploadFile = File(...)
):
    frame  = upload_to_frame(photo)
    result = state.engine.register_member(
        member_id=member_id,
        full_name=full_name,
        group_label=group_label,
        frame=frame
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result