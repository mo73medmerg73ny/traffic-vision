import os
import cv2 
import numpy as np
from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from core.tracker import VehicleTracker
from api.routes import router as db_router
from db.model import db_init, insert_video_info, insert_tracks_info, update_video_status

db_init()

app = FastAPI()
app.include_router(db_router)

db_init()

UPLOAD_DIR = 'uploaded_videos'
PROCESSED_DIR = 'processed_video'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

tracker = VehicleTracker(model_path='')

def process_video_task(video_path : str, video_id : int):
    update_video_status(video_id, status="processing")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_path = os.path.join(PROCESSED_DIR, f"{video_id}_processed.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    seen_tracks = {}
    frame_number = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = tracker.process_frame(frame)
        for (x1, y1, x2, y2, object_class, conf, track_id) in results:
            if track_id not in seen_tracks:
                first_seen_seconds = frame_number / fps
                seen_tracks[track_id] = (object_class, first_seen_seconds)

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            label = f"{object_class} ID: {track_id}"
            cv2.putText(frame, label, (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        out.write(frame)
        frame_number += 1

    cap.release()
    out.release()

    for track_id, (object_class, first_seen_seconds) in seen_tracks.items():
        insert_tracks_info(video_id, object_class, first_seen_seconds)

    total_vehicles = len(seen_tracks)
    update_video_status(video_id, status="completed", total_vehicles=total_vehicles)

@app.post('/video/upload')
async def upload_video(file : UploadFile, background_tasks : BackgroundTasks):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    video_id = insert_video_info(
        filename=file.filename,
        status="pending",
        total_vehicles=0
    )

    background_tasks.add_task(process_video_task, file_path, video_id)

    return {"video_id": video_id, "status": "pending"}


@app.get("/videos/{video_id}/result")
def get_processed_video(video_id: int):
    file_path = os.path.join(PROCESSED_DIR, f"{video_id}_processed.mp4")

    if not os.path.exists(file_path):
        return {"error": "The video is not yet ready or does not exist."}

    return FileResponse(file_path, media_type="video/mp4")
