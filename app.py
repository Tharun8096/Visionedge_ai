from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
    send_file
)

from werkzeug.utils import secure_filename
from ultralytics import YOLO

import os
import json
import cv2
import numpy as np
import io
import time


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "input_videos")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


# =========================================================
# YOLO MODEL
# =========================================================

MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")

model = None
last_live_time = None
live_fps = 0.0


def get_model():
    global model

    if model is None:
        print("Loading YOLO model...")
        model = YOLO(MODEL_PATH)
        print("YOLO model loaded.")

    return model


# =========================================================
# DEFAULT STATISTICS
# =========================================================

def default_stats():
    return {
        "persons": 0,
        "phones": 0,
        "cars": 0,
        "buses": 0,
        "trucks": 0,
        "motorcycles": 0,
        "bicycles": 0,
        "total_objects": 0,
        "fps": 0
    }


def save_stats(stats):
    path = os.path.join(OUTPUT_FOLDER, "stats.json")

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stats, f)
    except Exception as e:
        print("Could not save stats:", e)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# OUTPUT FILE
# =========================================================

@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(
        OUTPUT_FOLDER,
        filename
    )


# =========================================================
# STATISTICS
# =========================================================

@app.route("/stats")
def get_stats():

    stats_path = os.path.join(
        OUTPUT_FOLDER,
        "stats.json"
    )

    if not os.path.exists(stats_path):
        return jsonify(default_stats())

    try:
        with open(
            stats_path,
            "r",
            encoding="utf-8"
        ) as f:
            stats = json.load(f)

        return jsonify(stats)

    except Exception as e:
        print("Stats error:", e)
        return jsonify(default_stats())


# =========================================================
# OBJECT DETECTION HELPER
# =========================================================

def detect_frame(frame, yolo_model):

    results = yolo_model.predict(
        source=frame,
        conf=0.35,
        classes=[0, 1, 2, 3, 5, 7, 67],
        max_det=20,
        imgsz=416,
        verbose=False
    )

    result = results[0]

    stats = {
        "persons": 0,
        "phones": 0,
        "cars": 0,
        "buses": 0,
        "trucks": 0,
        "motorcycles": 0,
        "bicycles": 0,
        "total_objects": 0
    }

    if result.boxes is None:
        return frame, stats

    for box in result.boxes:

        cls = int(box.cls[0])
        confidence = float(box.conf[0])

        if cls == 0:
            name = "person"
            color = (0, 255, 0)
            stats["persons"] += 1

        elif cls == 67:
            name = "cell phone"
            color = (0, 255, 255)
            stats["phones"] += 1

        elif cls == 2:
            name = "car"
            color = (255, 0, 0)
            stats["cars"] += 1

        elif cls == 5:
            name = "bus"
            color = (0, 0, 255)
            stats["buses"] += 1

        elif cls == 7:
            name = "truck"
            color = (255, 0, 255)
            stats["trucks"] += 1

        elif cls == 3:
            name = "motorcycle"
            color = (0, 165, 255)
            stats["motorcycles"] += 1

        elif cls == 1:
            name = "bicycle"
            color = (255, 255, 255)
            stats["bicycles"] += 1

        else:
            continue

        stats["total_objects"] += 1

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        label = f"{name} {confidence:.2f}"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            frame,
            label,
            (
                x1,
                max(y1 - 10, 20)
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2
        )

    return frame, stats


# =========================================================
# UPLOADED VIDEO DETECTION
# =========================================================

@app.route(
    "/detect",
    methods=["POST"]
)
def detect():

    print("Received video detection request.")

    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "No video uploaded"
        }), 400

    video = request.files["video"]

    if video.filename == "":
        return jsonify({
            "success": False,
            "message": "Please select a video"
        }), 400

    filename = secure_filename(video.filename)

    if not filename:
        return jsonify({
            "success": False,
            "message": "Invalid video filename"
        }), 400

    input_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    video.save(input_path)

    print("Video saved:", input_path)

    output_video = os.path.join(
        OUTPUT_FOLDER,
        "output.mp4"
    )

    stats_path = os.path.join(
        OUTPUT_FOLDER,
        "stats.json"
    )

    # Remove previous output
    for old_file in [output_video, stats_path]:

        if os.path.exists(old_file):

            try:
                os.remove(old_file)
            except Exception as e:
                print("Could not remove:", e)

    cap = None
    writer = None

    try:

        # -----------------------------------------------------
        # LOAD MODEL
        # -----------------------------------------------------

        yolo_model = get_model()

        # -----------------------------------------------------
        # OPEN VIDEO
        # -----------------------------------------------------

        cap = cv2.VideoCapture(input_path)

        if not cap.isOpened():
            return jsonify({
                "success": False,
                "message": "Could not open uploaded video"
            }), 400

        original_width = int(
            cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        )

        original_height = int(
            cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        input_fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        if input_fps <= 0:
            input_fps = 20

        total_frames = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        print(
            "Video:",
            original_width,
            "x",
            original_height,
            "FPS:",
            input_fps,
            "Frames:",
            total_frames
        )

        # -----------------------------------------------------
        # RESIZE VIDEO
        # -----------------------------------------------------

        max_width = 640

        if original_width > max_width:

            scale = max_width / original_width

            output_width = max_width
            output_height = int(
                original_height * scale
            )

        else:

            output_width = original_width
            output_height = original_height

        # Make dimensions even
        output_width -= output_width % 2
        output_height -= output_height % 2

        # -----------------------------------------------------
        # VIDEO WRITER
        # -----------------------------------------------------

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        writer = cv2.VideoWriter(
            output_video,
            fourcc,
            input_fps,
            (
                output_width,
                output_height
            )
        )

        if not writer.isOpened():
            return jsonify({
                "success": False,
                "message": "Could not create output video"
            }), 500

        # -----------------------------------------------------
        # STATISTICS
        # -----------------------------------------------------

        final_stats = default_stats()

        processed_frames = 0
        start_time = time.time()

        # Process every frame.
        # YOLO itself receives a small 640px frame.
        while True:

            ret, frame = cap.read()

            if not ret:
                break

            # Resize to reduce RAM/CPU usage
            if (
                frame.shape[1] != output_width
                or frame.shape[0] != output_height
            ):
                frame = cv2.resize(
                    frame,
                    (
                        output_width,
                        output_height
                    ),
                    interpolation=cv2.INTER_AREA
                )

            # -------------------------------------------------
            # YOLO
            # -------------------------------------------------

            processed_frame, frame_stats = detect_frame(
                frame,
                yolo_model
            )

            # -------------------------------------------------
            # UPDATE STATISTICS
            # -------------------------------------------------

            final_stats["persons"] = max(
                final_stats["persons"],
                frame_stats["persons"]
            )

            final_stats["phones"] = max(
                final_stats["phones"],
                frame_stats["phones"]
            )

            final_stats["cars"] = max(
                final_stats["cars"],
                frame_stats["cars"]
            )

            final_stats["buses"] = max(
                final_stats["buses"],
                frame_stats["buses"]
            )

            final_stats["trucks"] = max(
                final_stats["trucks"],
                frame_stats["trucks"]
            )

            final_stats["motorcycles"] = max(
                final_stats["motorcycles"],
                frame_stats["motorcycles"]
            )

            final_stats["bicycles"] = max(
                final_stats["bicycles"],
                frame_stats["bicycles"]
            )

            final_stats["total_objects"] = max(
                final_stats["total_objects"],
                frame_stats["total_objects"]
            )

            processed_frames += 1

            # -------------------------------------------------
            # WRITE FRAME
            # -------------------------------------------------

            writer.write(processed_frame)

            # Release reference
            del processed_frame
            del frame

            # Progress log
            if processed_frames % 30 == 0:

                elapsed = time.time() - start_time

                current_fps = (
                    processed_frames / elapsed
                    if elapsed > 0
                    else 0
                )

                print(
                    f"Processed {processed_frames} frames | "
                    f"FPS: {current_fps:.2f}"
                )

        # -----------------------------------------------------
        # CLEANUP
        # -----------------------------------------------------

        cap.release()
        cap = None

        writer.release()
        writer = None

        elapsed = time.time() - start_time

        final_stats["fps"] = round(
            processed_frames / elapsed,
            2
        ) if elapsed > 0 else 0

        save_stats(final_stats)

        print("Detection completed.")
        print("Output:", output_video)
        print("Stats:", final_stats)

        # -----------------------------------------------------
        # CHECK OUTPUT
        # -----------------------------------------------------

        if not os.path.exists(output_video):

            return jsonify({
                "success": False,
                "message": "Output video was not created"
            }), 500

        output_size = os.path.getsize(
            output_video
        )

        if output_size == 0:

            return jsonify({
                "success": False,
                "message": "Output video is empty"
            }), 500

        # -----------------------------------------------------
        # DELETE INPUT VIDEO
        # -----------------------------------------------------

        try:
            os.remove(input_path)
        except Exception:
            pass

        return jsonify({

            "success": True,

            "message":
                "Detection completed successfully",

            "output":
                "/output/output.mp4",

            "stats":
                final_stats

        })

    except Exception as e:

        print("DETECTION ERROR:")
        print(e)

        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass

        if writer is not None:
            try:
                writer.release()
            except Exception:
                pass

        return jsonify({

            "success": False,

            "message":
                "Detection failed: " + str(e)

        }), 500


# =========================================================
# LIVE CAMERA DETECTION
# =========================================================

@app.route(
    "/live_detect",
    methods=["POST"]
)
def live_detect():

    global last_live_time
    global live_fps

    start_time = time.perf_counter()

    if "frame" not in request.files:

        return jsonify({
            "success": False,
            "message": "No camera frame received"
        }), 400

    frame_file = request.files["frame"]

    image_bytes = frame_file.read()

    if not image_bytes:

        return jsonify({
            "success": False,
            "message": "Empty camera frame"
        }), 400

    np_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    frame = cv2.imdecode(
        np_array,
        cv2.IMREAD_COLOR
    )

    if frame is None:

        return jsonify({
            "success": False,
            "message":
                "Could not decode camera frame"
        }), 400

    try:

        # -----------------------------------------------------
        # REDUCE CAMERA FRAME SIZE
        # -----------------------------------------------------

        max_width = 640

        if frame.shape[1] > max_width:

            scale = max_width / frame.shape[1]

            new_width = max_width
            new_height = int(
                frame.shape[0] * scale
            )

            frame = cv2.resize(
                frame,
                (new_width, new_height),
                interpolation=cv2.INTER_AREA
            )

        # -----------------------------------------------------
        # YOLO
        # -----------------------------------------------------

        yolo_model = get_model()

        processed_frame, stats = detect_frame(
            frame,
            yolo_model
        )

        frame = processed_frame

        # -----------------------------------------------------
        # FPS
        # -----------------------------------------------------

        current_time = time.perf_counter()

        if last_live_time is not None:

            delta = (
                current_time -
                last_live_time
            )

            if delta > 0:

                instant_fps = 1.0 / delta

                if live_fps <= 0:

                    live_fps = instant_fps

                else:

                    live_fps = (
                        0.8 * live_fps
                        +
                        0.2 * instant_fps
                    )

        last_live_time = current_time

        display_fps = int(
            max(0, live_fps)
        )

        # -----------------------------------------------------
        # CAMERA DASHBOARD
        # -----------------------------------------------------

        cv2.rectangle(
            frame,
            (10, 10),
            (280, 175),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            frame,
            "VisionEdge AI",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"FPS: {display_fps}",
            (20, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Persons: {stats['persons']}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Cars: {stats['cars']}",
            (20, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 0, 0),
            2
        )

        cv2.putText(
            frame,
            f"Phones: {stats['phones']}",
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Total: {stats['total_objects']}",
            (20, 165),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )

        # -----------------------------------------------------
        # JPEG
        # -----------------------------------------------------

        success, encoded_image = cv2.imencode(
            ".jpg",
            frame,
            [
                int(
                    cv2.IMWRITE_JPEG_QUALITY
                ),
                70
            ]
        )

        if not success:

            return jsonify({
                "success": False,
                "message":
                    "Could not encode camera frame"
            }), 500

        response = send_file(
            io.BytesIO(
                encoded_image.tobytes()
            ),
            mimetype="image/jpeg"
        )

        # -----------------------------------------------------
        # STATISTICS HEADERS
        # -----------------------------------------------------

        response.headers["X-Persons"] = str(
            stats["persons"]
        )

        response.headers["X-Phones"] = str(
            stats["phones"]
        )

        response.headers["X-Cars"] = str(
            stats["cars"]
        )

        response.headers["X-Buses"] = str(
            stats["buses"]
        )

        response.headers["X-Trucks"] = str(
            stats["trucks"]
        )

        response.headers["X-Motorcycles"] = str(
            stats["motorcycles"]
        )

        response.headers["X-Total-Objects"] = str(
            stats["total_objects"]
        )

        response.headers["X-FPS"] = str(
            display_fps
        )

        return response

    except Exception as e:

        print("LIVE CAMERA ERROR:")
        print(e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )