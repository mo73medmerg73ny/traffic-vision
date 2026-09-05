# Traffic Vision

An end-to-end vehicle detection and tracking system. Upload a traffic video and get back vehicle counts, class breakdowns, and an annotated video with bounding boxes and persistent tracking IDs.

Built as a full pipeline — from training a custom object detector to serving predictions through a containerized API.

## What it does

1. Upload a traffic video through the API.
2. The video is processed asynchronously: each frame runs through a fine-tuned YOLO11 model for vehicle detection, and DeepSORT for multi-object tracking (so the same vehicle keeps the same ID across frames instead of being re-detected as a new object every frame).
3. Once processing finishes, you get:
   - Total vehicle count and breakdown by class (car, truck, bus, motorcycle...)
   - The timestamp each vehicle first appeared in the video
   - An annotated output video with bounding boxes and track IDs drawn on every frame

## Architecture

```
Client
  │
  ▼
FastAPI (upload, status, results endpoints)
  │
  ├── Background task: video processing pipeline
  │     ├── YOLO11 (fine-tuned) — detection per frame
  │     ├── DeepSORT — tracking (Kalman filter + Hungarian algorithm matching)
  │     └── OpenCV — draws boxes/IDs, writes annotated output video
  │
  ▼
PostgreSQL (videos, tracks)
```

Everything runs in Docker Compose: the API service and the database as separate containers on the same network.

## Model training

The detector is a **YOLO11m** model fine-tuned on a custom traffic dataset (7 vehicle classes), trained on Kaggle with GPU acceleration.

| Metric | Result |
|---|---|
| Precision | 0.931 |
| Recall | 0.930 |
| mAP50 | 0.948 |
| mAP50-95 | 0.789 |

Input resolution was increased from 640×640 to 832×832, which improved mAP50-95 from 0.762 to 0.789 with better localization across several classes. The 832×832 model was selected as final.

Full training notebook: [Traffic Detection Project — Kaggle](https://www.kaggle.com/code/mohamedmerghany/traffic-detection-project)

## Tech stack

- **Detection:** YOLO11 (Ultralytics), fine-tuned via transfer learning
- **Tracking:** DeepSORT (Kalman filter + Hungarian algorithm + appearance embeddings)
- **Backend:** FastAPI (async, background task processing)
- **Database:** PostgreSQL
- **Video processing:** OpenCV
- **Deployment:** Docker, Docker Compose

## API

Interactive docs available at `/docs` once running (Swagger UI).

| Endpoint | Method | Description |
|---|---|---|
| `/videos/upload` | POST | Upload a video, returns `video_id` immediately, processing runs in the background |
| `/videos/{video_id}` | GET | Get video status (`pending` / `processing` / `completed`) and vehicle count |
| `/videos/tracks/{video_id}` | GET | Get detected vehicles: class + first-seen timestamp for each |
| `/videos/{video_id}/result` | GET | Download/stream the annotated output video |

## Running locally

```bash
git clone https://github.com/<your-username>/traffic-vision.git
cd traffic-vision
docker compose up --build
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

To try it: open `/docs`, upload a video through `/videos/upload`, note the `video_id`, then poll `/videos/{video_id}` until `status` is `completed`, and check `/videos/tracks/{video_id}` and `/videos/{video_id}/result` for the results.

## Project structure

```
traffic-vision/
├── app/
│   ├── main.py              # FastAPI app, upload endpoint, background processing task
│   ├── api/
│   │   └── router.py        # read endpoints (video status, tracks)
│   ├── core/
│   │   └── tracker.py       # VehicleTracker: YOLO + DeepSORT pipeline
│   └── db/
│       └── model.py         # database connection and queries
├── models/
│   └── best.pt               # fine-tuned YOLO11 weights
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Design notes

- **Async processing:** video processing can take longer than a typical HTTP timeout, so upload returns immediately with a `video_id` and processing happens in a background task. The client polls for status.
- **Track deduplication:** DeepSORT re-reports the same tracked vehicle on every frame it appears in. Only the first sighting of each track ID is persisted to the database — the rest are used only to draw the annotated video.
- **Environment-based configuration:** database connection details are read from environment variables (with local defaults), so the same code runs both locally and inside Docker Compose without changes.
