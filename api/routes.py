import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List
from api.processing import get_first_frame_b64, run_pipeline, LiveCameraProcessor

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

CONFIG_PATH = "config.yaml"


class ZoneRequest(BaseModel):
    session_id: str
    zone_points: List[List[float]]
    speed_limit: int = 60


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Accept video upload, return session_id + first frame as base64."""
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    video_path = os.path.join(session_dir, "input.mp4")
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        first_frame_b64 = get_first_frame_b64(video_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read video: {e}")

    return JSONResponse({
        "session_id": session_id,
        "first_frame": first_frame_b64,
        "filename": file.filename
    })


@router.post("/process")
async def process_video(req: ZoneRequest):
    """Start pipeline. Returns SSE stream of annotated frames."""
    session_dir = os.path.join(UPLOAD_DIR, req.session_id)
    video_path = os.path.join(session_dir, "input.mp4")

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Session not found. Upload video first.")

    if len(req.zone_points) != 4:
        raise HTTPException(status_code=400, detail="Exactly 4 zone points required.")

    return StreamingResponse(
        run_pipeline(video_path, req.zone_points, req.speed_limit, CONFIG_PATH),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/health")
async def health():
    return {"status": "ok"}


# Store active camera sessions in memory
camera_sessions: dict = {}


class CameraSessionRequest(BaseModel):
    zone_points: List[List[float]]
    speed_limit: int = 60


@router.post("/camera/session")
async def create_camera_session(req: CameraSessionRequest):
    """Create a new live camera processing session, return session_id."""
    if len(req.zone_points) != 4:
        raise HTTPException(status_code=400, detail="Exactly 4 zone points required.")

    session_id = str(uuid.uuid4())
    camera_sessions[session_id] = LiveCameraProcessor(
        req.zone_points, req.speed_limit, CONFIG_PATH
    )
    return JSONResponse({"session_id": session_id})


@router.websocket("/ws/camera/{session_id}")
async def camera_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for live camera frames.
    Browser sends raw JPEG bytes → backend processes → sends back JSON with annotated frame.
    """
    if session_id not in camera_sessions:
        await websocket.close(code=4004)
        return

    processor = camera_sessions[session_id]
    await websocket.accept()

    try:
        while True:
            frame_bytes = await websocket.receive_bytes()
            result = processor.process_frame(frame_bytes)
            await websocket.send_text(result)
    except WebSocketDisconnect:
        # Clean up session when browser disconnects
        camera_sessions.pop(session_id, None)
    except Exception as e:
        camera_sessions.pop(session_id, None)
        await websocket.close()
