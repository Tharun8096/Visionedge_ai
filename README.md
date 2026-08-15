# VisionEdge AI 🚀

## Smart Object Detection System

VisionEdge AI is a real-time computer vision application that detects and analyzes objects from uploaded videos and live camera streams using YOLO and OpenCV.

The system provides object detection, live camera detection, statistics, FPS monitoring, detection status, and processed video output through a web-based dashboard.

---

## 📌 Project Overview

VisionEdge AI uses an AI-based object detection model to identify objects in video frames.

The application supports:

- 📹 Video upload and detection
- 📷 Live camera detection
- 🎯 YOLO object detection
- 📊 Detection statistics
- ⚡ FPS monitoring
- 🔢 Total object counting
- 🟢 Live detection status
- 🎥 Processed detection video output
- 📝 Detection logging
- 💻 Web-based dashboard

---

## ✨ Features

### 1. Video Upload

Users can upload a video file through the web dashboard.

The system processes the video frame by frame and performs object detection using YOLO.

### 2. Live Camera Detection

VisionEdge AI can access the device camera and perform object detection in real time.

The detected objects are displayed with bounding boxes and labels.

### 3. Object Detection

The system can detect common objects such as:

- Person
- Phone
- Car
- Bus
- Truck
- Motorcycle

The detected objects are displayed using bounding boxes and confidence scores.

### 4. Detection Statistics

The dashboard displays detection statistics including:

- Persons
- Phones
- Cars
- Buses
- Trucks
- Motorcycles
- Total Objects

### 5. Performance Monitoring

The system displays:

- FPS (Frames Per Second)
- Total detected objects

This helps monitor the performance of the detection system.

### 6. Detection Status

The dashboard displays the current detection state:

- LIVE – when live camera detection is running
- COMPLETED – when uploaded video processing is completed

### 7. Detection Output

After processing an uploaded video, the system generates a detection output video containing:

- Bounding boxes
- Object labels
- Confidence values
- FPS
- Object counts
- Detection information

### 8. Detection Logging

Detection information is stored in log files for later analysis.

---

## 🛠️ Technologies Used

- Python
- Flask
- OpenCV
- YOLOv8
- HTML5
- CSS3
- JavaScript
- JSON
- CSV
- Git & GitHub

---

## 🧠 System Architecture

```text
                 ┌─────────────────────┐
                 │      User           │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Web Dashboard     │
                 │   HTML/CSS/JS       │
                 └──────────┬──────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       ┌──────────────┐           ┌──────────────┐
       │ Upload Video │           │ Live Camera  │
       └──────┬───────┘           └──────┬───────┘
              │                          │
              └────────────┬─────────────┘
                           ▼
                  ┌─────────────────┐
                  │ Flask Backend   │
                  │    app.py       │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ YOLOv8 Model    │
                  │ Object Detection │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    OpenCV       │
                  │ Frame Processing │
                  └────────┬────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌──────────────┐          ┌──────────────┐
       │ Statistics   │          │ Output Video │
       └──────────────┘          └──────────────┘