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
import subprocess
import sys
import json
import cv2
import numpy as np
import io
import time


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================================================
# FOLDERS
# =========================================================

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "input_videos"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "output"
)


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# =========================================================
# YOLO MODEL
# =========================================================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "yolov8n.pt"
)


live_model = None


def get_live_model():

    global live_model

    if live_model is None:

        print("")
        print("========================================")
        print("Loading YOLO model for LIVE CAMERA...")
        print("========================================")

        live_model = YOLO(
            MODEL_PATH
        )

        print(
            "Live YOLO model loaded successfully."
        )

    return live_model


# =========================================================
# LIVE FPS
# =========================================================

last_live_time = None

live_fps = 0.0


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# SERVE OUTPUT FILES
# =========================================================

@app.route(
    "/output/<path:filename>"
)
def output_file(filename):

    return send_from_directory(
        OUTPUT_FOLDER,
        filename
    )


# =========================================================
# GET STATISTICS
# =========================================================

@app.route("/stats")
def get_stats():

    stats_path = os.path.join(
        OUTPUT_FOLDER,
        "stats.json"
    )


    default_stats = {

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


    if not os.path.exists(
        stats_path
    ):

        return jsonify(
            default_stats
        )


    try:

        with open(
            stats_path,
            "r",
            encoding="utf-8"
        ) as f:

            stats = json.load(f)


        return jsonify(
            stats
        )


    except Exception as e:

        print(
            "Stats error:",
            e
        )


        return jsonify(
            default_stats
        )


# =========================================================
# UPLOADED VIDEO DETECTION
# =========================================================

@app.route(
    "/detect",
    methods=["POST"]
)
def detect():

    # -----------------------------------------------------
    # CHECK VIDEO
    # -----------------------------------------------------

    if "video" not in request.files:

        return jsonify({

            "success": False,

            "message":
                "No video uploaded"

        })


    video = request.files[
        "video"
    ]


    if video.filename == "":

        return jsonify({

            "success": False,

            "message":
                "Please select a video"

        })


    # -----------------------------------------------------
    # SAVE VIDEO
    # -----------------------------------------------------

    filename = secure_filename(
        video.filename
    )


    input_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    video.save(
        input_path
    )


    print("")
    print(
        "Uploaded video:",
        input_path
    )


    # -----------------------------------------------------
    # OUTPUT FILES
    # -----------------------------------------------------

    stats_path = os.path.join(
        OUTPUT_FOLDER,
        "stats.json"
    )


    output_video = os.path.join(
        OUTPUT_FOLDER,
        "output.mp4"
    )


    temp_video = os.path.join(
        OUTPUT_FOLDER,
        "output_temp.mp4"
    )


    # -----------------------------------------------------
    # DELETE OLD FILES
    # -----------------------------------------------------

    for old_file in [

        stats_path,

        output_video,

        temp_video

    ]:

        if os.path.exists(
            old_file
        ):

            try:

                os.remove(
                    old_file
                )

            except Exception as e:

                print(
                    "Could not delete:",
                    old_file,
                    e
                )


    # =====================================================
    # RUN YOLO
    # =====================================================

    try:

        print("")
        print(
            "========================================"
        )

        print(
            "Starting YOLO video detection..."
        )

        print(
            "========================================"
        )


        yolo_path = os.path.join(
            BASE_DIR,
            "yolo.py"
        )


        subprocess.run(

            [

                sys.executable,

                yolo_path,

                input_path

            ],

            check=True

        )


        print(
            "YOLO finished successfully."
        )


        # =================================================
        # CHECK STATS
        # =================================================

        if not os.path.exists(
            stats_path
        ):

            return jsonify({

                "success": False,

                "message":
                    "YOLO finished but stats.json was not created."

            })


        # =================================================
        # CHECK OUTPUT VIDEO
        # =================================================

        if not os.path.exists(
            output_video
        ):

            return jsonify({

                "success": False,

                "message":
                    "YOLO finished but output.mp4 was not created."

            })


        # =================================================
        # READ STATISTICS
        # =================================================

        with open(

            stats_path,

            "r",

            encoding="utf-8"

        ) as f:

            stats = json.load(
                f
            )


        print("")
        print(
            "========================================"
        )

        print(
            "FINAL STATISTICS"
        )

        print(
            "========================================"
        )

        print(
            stats
        )

        print(
            "========================================"
        )


        # =================================================
        # RETURN DATA
        # =================================================

        return jsonify({

            "success": True,

            "message":
                "Detection completed",

            "output":
                "/output/output.mp4",

            "stats":
                stats

        })


    except subprocess.CalledProcessError as e:

        print("")
        print(
            "YOLO ERROR:"
        )

        print(
            e
        )


        return jsonify({

            "success": False,

            "message":
                "YOLO detection failed. Check terminal."

        })


    except Exception as e:

        print("")
        print(
            "APPLICATION ERROR:"
        )

        print(
            e
        )


        return jsonify({

            "success": False,

            "message":
                str(e)

        })


# =========================================================
# LIVE CAMERA YOLO DETECTION
# =========================================================

@app.route(
    "/live_detect",
    methods=["POST"]
)
def live_detect():

    global last_live_time
    global live_fps


    start_time = time.perf_counter()


    # -----------------------------------------------------
    # CHECK FRAME
    # -----------------------------------------------------

    if "frame" not in request.files:

        return jsonify({

            "success": False,

            "message":
                "No camera frame received"

        }), 400


    frame_file = request.files[
        "frame"
    ]


    # -----------------------------------------------------
    # READ IMAGE
    # -----------------------------------------------------

    image_bytes = frame_file.read()


    if not image_bytes:

        return jsonify({

            "success": False,

            "message":
                "Empty camera frame"

        }), 400


    # -----------------------------------------------------
    # CONVERT JPEG TO OPENCV IMAGE
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # LOAD MODEL
    # -----------------------------------------------------

    model = get_live_model()


    # -----------------------------------------------------
    # YOLO DETECTION
    # -----------------------------------------------------

    results = model.predict(

        source=frame,

        conf=0.35,

        verbose=False

    )


    result = results[0]


    # -----------------------------------------------------
    # COUNTERS
    # -----------------------------------------------------

    person_count = 0

    phone_count = 0

    car_count = 0

    bus_count = 0

    truck_count = 0

    motorcycle_count = 0

    total_objects = 0


    # -----------------------------------------------------
    # DETECTION
    # -----------------------------------------------------

    if result.boxes is not None:

        for box in result.boxes:

            cls = int(
                box.cls[0]
            )


            confidence = float(
                box.conf[0]
            )


            # =============================================
            # PERSON
            # =============================================

            if cls == 0:

                person_count += 1

                object_name = "person"

                color = (
                    0,
                    255,
                    0
                )


            # =============================================
            # PHONE
            # =============================================

            elif cls == 67:

                phone_count += 1

                object_name = "cell phone"

                color = (
                    0,
                    255,
                    255
                )


            # =============================================
            # CAR
            # =============================================

            elif cls == 2:

                car_count += 1

                object_name = "car"

                color = (
                    255,
                    0,
                    0
                )


            # =============================================
            # BUS
            # =============================================

            elif cls == 5:

                bus_count += 1

                object_name = "bus"

                color = (
                    0,
                    0,
                    255
                )


            # =============================================
            # TRUCK
            # =============================================

            elif cls == 7:

                truck_count += 1

                object_name = "truck"

                color = (
                    255,
                    0,
                    255
                )


            # =============================================
            # MOTORCYCLE
            # =============================================

            elif cls == 3:

                motorcycle_count += 1

                object_name = "motorcycle"

                color = (
                    0,
                    165,
                    255
                )


            # =============================================
            # BICYCLE
            # =============================================

            elif cls == 1:

                object_name = "bicycle"

                color = (
                    255,
                    255,
                    255
                )


            # =============================================
            # OTHER OBJECTS
            # =============================================

            else:

                continue


            total_objects += 1


            # -------------------------------------------------
            # BOUNDING BOX
            # -------------------------------------------------

            x1, y1, x2, y2 = map(

                int,

                box.xyxy[0]

            )


            # -------------------------------------------------
            # LABEL
            # -------------------------------------------------

            label = (

                f"{object_name} "

                f"{confidence:.2f}"

            )


            # -------------------------------------------------
            # DRAW BOX
            # -------------------------------------------------

            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                color,

                2

            )


            # -------------------------------------------------
            # DRAW LABEL
            # -------------------------------------------------

            cv2.putText(

                frame,

                label,

                (
                    x1,
                    max(
                        y1 - 10,
                        20
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                color,

                2

            )


    # =====================================================
    # CALCULATE FPS
    # =====================================================

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
        max(
            0,
            live_fps
        )
    )


    # =====================================================
    # DRAW DASHBOARD ON CAMERA
    # =====================================================

    cv2.rectangle(

        frame,

        (10, 10),

        (270, 170),

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

        0.6,

        (255, 255, 255),

        2

    )


    cv2.putText(

        frame,

        f"Persons: {person_count}",

        (20, 90),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (0, 255, 0),

        2

    )


    cv2.putText(

        frame,

        f"Cars: {car_count}",

        (20, 115),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (255, 0, 0),

        2

    )


    cv2.putText(

        frame,

        f"Phones: {phone_count}",

        (20, 140),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (0, 255, 255),

        2

    )


    cv2.putText(

        frame,

        f"Total: {total_objects}",

        (20, 165),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (255, 255, 255),

        2

    )


    # =====================================================
    # ENCODE IMAGE
    # =====================================================

    success, encoded_image = cv2.imencode(

        ".jpg",

        frame,

        [
            int(
                cv2.IMWRITE_JPEG_QUALITY
            ),
            80
        ]

    )


    if not success:

        return jsonify({

            "success": False,

            "message":
                "Could not encode detection frame"

        }), 500


    # =====================================================
    # RETURN IMAGE
    # =====================================================

    response = send_file(

        io.BytesIO(
            encoded_image.tobytes()
        ),

        mimetype="image/jpeg"

    )


    # =====================================================
    # SEND LIVE STATISTICS
    # =====================================================

    response.headers[
        "X-Persons"
    ] = str(
        person_count
    )


    response.headers[
        "X-Phones"
    ] = str(
        phone_count
    )


    response.headers[
        "X-Cars"
    ] = str(
        car_count
    )


    response.headers[
        "X-Buses"
    ] = str(
        bus_count
    )


    response.headers[
        "X-Trucks"
    ] = str(
        truck_count
    )


    response.headers[
        "X-Motorcycles"
    ] = str(
        motorcycle_count
    )


    response.headers[
        "X-Total-Objects"
    ] = str(
        total_objects
    )


    response.headers[
        "X-FPS"
    ] = str(
        display_fps
    )


    return response


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )