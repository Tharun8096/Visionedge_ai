from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import subprocess
import sys
import json


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


# Create folders
os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


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


    # Default statistics
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


    # If stats.json doesn't exist
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


        print(
            "STATS:",
            stats
        )


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
# DETECTION
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
    # SECURE FILE NAME
    # -----------------------------------------------------

    filename = secure_filename(
        video.filename
    )


    input_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    # -----------------------------------------------------
    # SAVE VIDEO
    # -----------------------------------------------------

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
            "Starting YOLO detection..."
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

            stats = json.load(f)


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
        # RETURN DATA TO JAVASCRIPT
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


    # =====================================================
    # YOLO ERROR
    # =====================================================

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


    # =====================================================
    # OTHER ERROR
    # =====================================================

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
# START FLASK
# =========================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )