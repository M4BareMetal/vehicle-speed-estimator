# 🚗 Vehicle Speed Estimation System

A real-time vehicle speed estimation system that uses a camera feed, YOLOv8 for vehicle detection, SORT for multi-object tracking, and perspective transform to convert pixel motion into real-world speed in km/h.[file:48][file:49][file:51]

## Features

- Real-time vehicle detection using YOLOv8 with configurable model size and classes.[file:48][file:49][file:51]  
- Multi-object tracking with SORT to maintain stable IDs across frames.[file:49][file:51]  
- Perspective-based speed calculation using a calibrated road zone and real-world dimensions.[file:48][file:49][file:51]  
- Overspeed detection with configurable speed limit and per-vehicle violation logging.[file:48][file:49][file:51]  
- Automatic CSV logging and snapshot capture for each violation.[file:48][file:49][file:51]  
- Streamlit dashboard to explore logs, visualize speeds, and review violation images.[file:51]  

## Tech Stack

- Language: Python  
- Computer Vision: OpenCV  
- Detection: YOLOv8 (Ultralytics)  
- Tracking: SORT (Simple Online and Realtime Tracking)  
- Visualization: Streamlit dashboard  
- Config: YAML-based configuration for all modules[file:48][file:51]  

## Project Structure

```text
vehicle_speed_estimator/
├── main.py                    # Main pipeline entry point
├── config.yaml                # Central configuration
├── requirements.txt           # Dependencies list
├── run.bat / run.sh           # One-click pipeline launchers
├── run_dashboard.bat / .sh    # One-click dashboard launchers
│
├── core/
│   ├── video_stream.py        # Frame ingestion + FPS handling
│   ├── detector.py            # YOLOv8 vehicle detection
│   ├── tracker.py             # SORT multi-object tracking
│   ├── speed_estimator.py     # Perspective transform + speed calc
│   ├── alert_engine.py        # Overspeed detection logic
│   └── reporter.py            # CSV logs + violation snapshots
│
├── ui/
│   └── dashboard.py           # Streamlit analytics dashboard
│
├── utils/
│   ├── drawing.py             # Frame annotation helpers
│   ├── calibration.py         # Perspective transform utilities
│   └── zone_picker.py         # Interactive zone calibration tool
│
├── tests/
│   ├── test_calibration.py    # Unit tests for calibration
│   └── test_alert_engine.py   # Unit tests for alerts
│
├── data/                      # Input videos (user-provided)
└── output/                    # Logs and violation snapshots
```

[file:51]

## How It Works

At a high level, the system reads frames from a video source, detects vehicles, tracks them, estimates their speed based on calibrated geometry, checks for violations, and logs results.[file:48][file:49][file:51]

1. `VideoStream` reads frames and timestamps from a video file or webcam.[file:48][file:49]  
2. `VehicleDetector` runs YOLOv8 on each frame to produce bounding boxes for vehicles.[file:48][file:49]  
3. `VehicleTracker` feeds detections into SORT to maintain consistent track IDs.[file:49][file:51]  
4. `SpeedEstimator` converts pixel movement inside a calibrated zone into real-world speed using a perspective transform and known zone dimensions.[file:48][file:49][file:51]  
5. `AlertEngine` compares each vehicle’s speed against a configured limit to flag overspeed violations.[file:48][file:49][file:51]  
6. `ReportManager` logs every observation and violation to CSV and captures frame snapshots for overspeeding vehicles.[file:48][file:49][file:51]  

## Setup

1. Create and activate a virtual environment (recommended).  
2. Install dependencies:

```bash
pip install -r requirements.txt
```

[file:51]

Make sure you have a YOLOv8 model file (for example `yolov8n.pt`) available and referenced in `config.yaml` under `model.yolo_model`.[file:48]

## Configuration

All configuration lives in `config.yaml`.[file:48][file:51] Key sections:

```yaml
source:
  type: video            # "video" or "webcam"
  path: data/sample.mp4  # path to your input video
  webcam_index: 0        # used when type == webcam

model:
  yolo_model: yolov8n.pt
  classes:   # vehicle classes
  confidence_threshold: 0.35

tracking:
  tracker_type: sort
  max_age: 20
  min_hits: 3
  iou_threshold: 0.3

speed:
  speed_limit_kmh: 60
  measurement_zone: [, , , ]
  real_world_zone_meters: [, , , ]

reporting:
  output_csv: output/vehicle_log.csv
  violation_frames_dir: output/violations

ui:
  show_live: true
  window_name: Vehicle Speed Estimator
```

[file:48]

You should adjust:

- `source.path` to point to your own input video.  
- `speed.measurement_zone` to match the four corner points of your road region in the image.  
- `speed.real_world_zone_meters` to reflect the real-world dimensions of that region (in meters).  

## Step 1: Calibrate Measurement Zone

Use the interactive zone picker to define the measurement zone for your video.[file:51]

```bash
python utils/zone_picker.py
```

This script lets you click four points on the video frame to define the road region used for speed estimation and saves them back into the configuration/calibration pipeline.[file:51]

## Step 2: Run the Speed Estimation Pipeline

Run the full pipeline from the command line:

```bash
python main.py
# OR on Windows:
# double-click run.bat
```

[file:51]

During execution:

- A window shows the annotated video with bounding boxes, track IDs, speeds, and basic statistics overlay.[file:49][file:51]  
- Press `Q` to quit early.[file:51]  
- At the end, a summary of total vehicles and violations is printed, and the CSV path is displayed.[file:49]  

Example console output:

```text
Done. Total vehicles: 42 | Violations: 7
Log saved to: output/vehicle_log.csv
```

[file:49]

## Step 3: Explore Data in the Dashboard

To analyze results and visualize violations, run the Streamlit dashboard:

```bash
streamlit run ui/dashboard.py
# OR on Windows:
# double-click run_dashboard.bat
```

[file:51]

In the dashboard:

- Upload `output/vehicle_log.csv` from the sidebar.[file:51]  
- View per-vehicle speed timelines, violation counts, and aggregated statistics.  
- Browse violation snapshots stored under `output/violations`.  

## Outputs

By default, the system produces:

- `output/vehicle_log.csv`  
  - Per-frame/per-vehicle records including track ID, timestamp, estimated speed, and violation flags.[file:48][file:49][file:51]  
- `output/violations/`  
  - Image snapshots of frames where vehicles exceeded the speed limit.[file:48][file:49][file:51]  

These outputs can be used as evidence, for further analytics, or as input to other tools.

## Running Tests

Basic tests are included for critical components:

```bash
python tests/test_calibration.py
python tests/test_alert_engine.py
```

[file:51]

These tests validate that the perspective calibration behaves as expected and that overspeed alerts are triggered correctly for synthetic inputs.[file:51]

## Embedded / Firmware Perspective

This project is structured like a typical embedded sensing pipeline: a sensor (camera) feeds raw data to a processing chain (detection, tracking, speed estimation), which then drives application logic (overspeed alerts) and a user interface (dashboard).[file:48][file:49][file:51]

Future extensions could include:

- Deploying the pipeline to edge hardware such as a Raspberry Pi or NVIDIA Jetson.  
- Rewriting performance-critical parts (detection/tracking) in C++ and integrating with a firmware-level application.  
- Integrating with external sensors or communication interfaces (e.g., sending violations to a central server).  