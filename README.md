---
title: VeloScan — Vehicle Speed Estimator
emoji: 🚗
colorFrom: orange
colorTo: red
sdk: docker
pinned: false
---

# 🚗 VeloScan — Vehicle Speed Intelligence

Real-time vehicle speed estimation and overspeed detection from traffic video.

## How to Use

1. **Upload** a traffic video (MP4, AVI, MOV)
2. **Define the measurement zone** — click 4 points on the road in the first frame
3. **Set your speed limit** and hit Analyze
4. Watch the pipeline process your video — every vehicle tracked, every speeder flagged in red
5. **Review results** — violation count, snapshots of every speeding vehicle

## Tech Stack

- **Detection**: YOLOv8n (Ultralytics)
- **Tracking**: SORT with Kalman Filter
- **Speed Estimation**: Perspective transform to real-world coordinates
- **Backend**: FastAPI + Server-Sent Events for live streaming
- **Frontend**: Vanilla JS + HTML5 Canvas

## Local Setup

```bash
pip install -r requirements.txt
python app.py
# Open http://localhost:7860
```
