from ultralytics import YOLO
import cv2
import time
from datetime import datetime
import csv
import os
import sys
import json
import subprocess
import shutil
import gc


# ============================================================
# VisionEdge AI
# Memory-Optimized YOLO Video Detection
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "yolov8n.pt"
)

INPUT_DEFAULT = os.path.join(
    BASE_DIR,
    "input_videos",
    "test.mp4"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "output"
)

LOG_FOLDER = os.path.join(
    BASE_DIR,
    "logs"
)

SCREENSHOT_FOLDER = os.path.join(
    BASE_DIR,
    "screenshots"
)


# ============================================================
# MEMORY OPTIMIZATION SETTINGS
# ============================================================

# Maximum width/height used for YOLO processing
MAX_SIZE = 640

# Smaller YOLO input = lower RAM usage
YOLO_IMAGE_SIZE = 416

# Confidence threshold
CONFIDENCE_THRESHOLD = 0.50

# Maximum number of detections per frame
MAX_DETECTIONS = 20

# Process garbage collection periodically
GC_INTERVAL = 100


# ============================================================
# CREATE FOLDERS
# ============================================================

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)

os.makedirs(
    LOG_FOLDER,
    exist_ok=True
)

os.makedirs(
    SCREENSHOT_FOLDER,
    exist_ok=True
)


# ============================================================
# INPUT VIDEO
# ============================================================

if len(sys.argv) > 1:

    input_video = sys.argv[1]

else:

    input_video = INPUT_DEFAULT


print("========================================")
print("VisionEdge AI")
print("Smart Object Detection")
print("========================================")
print("Input video:", input_video)


# ============================================================
# CHECK INPUT VIDEO
# ============================================================

if not os.path.exists(input_video):

    print(
        "ERROR: Input video not found:",
        input_video
    )

    sys.exit(1)


# ============================================================
# CHECK MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):

    print(
        "ERROR: YOLO model not found:",
        MODEL_PATH
    )

    sys.exit(1)


# ============================================================
# LOAD YOLO MODEL
# ============================================================

print("Loading YOLO model...")

try:

    model = YOLO(
        MODEL_PATH
    )

    print(
        "YOLO model loaded successfully."
    )

except Exception as e:

    print(
        "ERROR loading YOLO model:",
        e
    )

    sys.exit(1)


# ============================================================
# OPEN VIDEO
# ============================================================

camera = cv2.VideoCapture(
    input_video
)

if not camera.isOpened():

    print(
        "ERROR: Could not open video."
    )

    sys.exit(1)


# ============================================================
# VIDEO INFORMATION
# ============================================================

original_width = int(
    camera.get(
        cv2.CAP_PROP_FRAME_WIDTH
    )
)

original_height = int(
    camera.get(
        cv2.CAP_PROP_FRAME_HEIGHT
    )
)

input_fps = camera.get(
    cv2.CAP_PROP_FPS
)

if input_fps <= 0:

    input_fps = 20.0


total_frames = int(
    camera.get(
        cv2.CAP_PROP_FRAME_COUNT
    )
)


print(
    "Original resolution:",
    original_width,
    "x",
    original_height
)

print(
    "Input FPS:",
    input_fps
)

print(
    "Total frames:",
    total_frames
)


# ============================================================
# RESIZE VIDEO FOR MEMORY SAVING
# ============================================================

scale = min(
    1.0,
    MAX_SIZE / max(
        original_width,
        original_height
    )
)


output_width = int(
    original_width * scale
)

output_height = int(
    original_height * scale
)


# Make dimensions even for video codecs
output_width = output_width - (
    output_width % 2
)

output_height = output_height - (
    output_height % 2
)


print(
    "Processing resolution:",
    output_width,
    "x",
    output_height
)


# ============================================================
# OUTPUT PATHS
# ============================================================

temp_output_path = os.path.join(
    OUTPUT_FOLDER,
    "output_temp.mp4"
)

final_output_path = os.path.join(
    OUTPUT_FOLDER,
    "output.mp4"
)

stats_path = os.path.join(
    OUTPUT_FOLDER,
    "stats.json"
)


# ============================================================
# DELETE OLD OUTPUT FILES
# ============================================================

for old_file in [
    temp_output_path,
    final_output_path,
    stats_path
]:

    if os.path.exists(old_file):

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


# ============================================================
# CREATE OUTPUT VIDEO
# ============================================================

fourcc = cv2.VideoWriter_fourcc(
    *"mp4v"
)

video = cv2.VideoWriter(
    temp_output_path,
    fourcc,
    input_fps,
    (
        output_width,
        output_height
    )
)


if not video.isOpened():

    print(
        "ERROR: Could not create output video."
    )

    camera.release()

    sys.exit(1)


print(
    "Temporary output:",
    temp_output_path
)


# ============================================================
# CSV LOG
# ============================================================

log_file_path = os.path.join(
    LOG_FOLDER,
    "detection_log.csv"
)


log_file = open(
    log_file_path,
    "a",
    newline="",
    encoding="utf-8"
)


csv_writer = csv.writer(
    log_file
)


if os.path.getsize(
    log_file_path
) == 0:

    csv_writer.writerow([
        "Date",
        "Time",
        "Object",
        "Confidence"
    ])


# ============================================================
# MAXIMUM DETECTION COUNTS
# ============================================================

max_person_count = 0
max_phone_count = 0
max_car_count = 0
max_bus_count = 0
max_truck_count = 0
max_motorcycle_count = 0
max_bicycle_count = 0

max_total_objects = 0
max_fps = 0


# ============================================================
# PREVIOUS LOGGED OBJECT
# ============================================================

previous_logged_object = None


# ============================================================
# PROCESS VIDEO
# ============================================================

frame_number = 0

previous_time = time.time()


print("")
print("Starting video processing...")
print("")


try:

    while True:

        # ====================================================
        # READ FRAME
        # ====================================================

        success, frame = camera.read()


        if not success or frame is None:

            print(
                "Video processing completed."
            )

            break


        frame_number += 1


        # ====================================================
        # RESIZE FRAME
        # ====================================================

        if (
            frame.shape[1] != output_width
            or
            frame.shape[0] != output_height
        ):

            frame = cv2.resize(
                frame,
                (
                    output_width,
                    output_height
                ),
                interpolation=cv2.INTER_AREA
            )


        # ====================================================
        # FPS
        # ====================================================

        current_time_seconds = time.time()

        time_difference = (
            current_time_seconds
            -
            previous_time
        )


        if time_difference > 0:

            fps = (
                1 /
                time_difference
            )

        else:

            fps = 0


        previous_time = (
            current_time_seconds
        )


        max_fps = max(
            max_fps,
            int(fps)
        )


        # ====================================================
        # DATE AND TIME
        # ====================================================

        now = datetime.now()


        current_date = now.strftime(
            "%d-%m-%Y"
        )


        current_time = now.strftime(
            "%H:%M:%S"
        )


        # ====================================================
        # CURRENT FRAME COUNTERS
        # ====================================================

        person_count = 0
        phone_count = 0
        car_count = 0
        bus_count = 0
        truck_count = 0
        motorcycle_count = 0
        bicycle_count = 0

        total_objects = 0


        # ====================================================
        # YOLO DETECTION
        # ====================================================

        try:

            results = model.predict(
                source=frame,
                imgsz=YOLO_IMAGE_SIZE,
                conf=CONFIDENCE_THRESHOLD,
                max_det=MAX_DETECTIONS,
                device="cpu",
                verbose=False
            )

        except Exception as e:

            print(
                "YOLO detection error:",
                e
            )

            continue


        # ====================================================
        # PROCESS DETECTIONS
        # ====================================================

        for result in results:

            if result.boxes is None:

                continue


            for box in result.boxes:

                try:

                    cls = int(
                        box.cls[0]
                    )

                    confidence = float(
                        box.conf[0]
                    )

                except Exception:

                    continue


                # ============================================
                # CONFIDENCE
                # ============================================

                if (
                    confidence
                    <
                    CONFIDENCE_THRESHOLD
                ):

                    continue


                object_name = (
                    model.names[cls]
                )


                # ============================================
                # OBJECT CLASSIFICATION
                # ============================================

                # Person
                if cls == 0:

                    person_count += 1

                    color = (
                        0,
                        255,
                        0
                    )


                # Bicycle
                elif cls == 1:

                    bicycle_count += 1

                    color = (
                        255,
                        255,
                        255
                    )


                # Car
                elif cls == 2:

                    car_count += 1

                    color = (
                        255,
                        0,
                        0
                    )


                # Motorcycle
                elif cls == 3:

                    motorcycle_count += 1

                    color = (
                        0,
                        165,
                        255
                    )


                # Bus
                elif cls == 5:

                    bus_count += 1

                    color = (
                        0,
                        0,
                        255
                    )


                # Truck
                elif cls == 7:

                    truck_count += 1

                    color = (
                        255,
                        0,
                        255
                    )


                # Cell phone
                elif cls == 67:

                    phone_count += 1

                    color = (
                        0,
                        255,
                        255
                    )


                else:

                    continue


                total_objects += 1


                # ============================================
                # BOUNDING BOX
                # ============================================

                try:

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )

                except Exception:

                    continue


                # ============================================
                # LABEL
                # ============================================

                label = (
                    f"{object_name} "
                    f"{confidence:.2f}"
                )


                # ============================================
                # DRAW RECTANGLE
                # ============================================

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )


                # ============================================
                # DRAW LABEL
                # ============================================

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


                # ============================================
                # CSV LOG
                # ============================================

                if (
                    object_name
                    !=
                    previous_logged_object
                ):

                    csv_writer.writerow([
                        current_date,
                        current_time,
                        object_name,
                        round(
                            confidence,
                            4
                        )
                    ])

                    log_file.flush()

                    previous_logged_object = (
                        object_name
                    )


        # ====================================================
        # DELETE YOLO RESULTS
        # ====================================================

        del results


        # ====================================================
        # UPDATE MAXIMUM COUNTS
        # ====================================================

        max_person_count = max(
            max_person_count,
            person_count
        )


        max_phone_count = max(
            max_phone_count,
            phone_count
        )


        max_car_count = max(
            max_car_count,
            car_count
        )


        max_bus_count = max(
            max_bus_count,
            bus_count
        )


        max_truck_count = max(
            max_truck_count,
            truck_count
        )


        max_motorcycle_count = max(
            max_motorcycle_count,
            motorcycle_count
        )


        max_bicycle_count = max(
            max_bicycle_count,
            bicycle_count
        )


        max_total_objects = max(
            max_total_objects,
            total_objects
        )


        # ====================================================
        # STATUS
        # ====================================================

        if total_objects > 0:

            status = "ACTIVE"

            status_color = (
                0,
                255,
                0
            )

        else:

            status = "NO OBJECT DETECTED"

            status_color = (
                0,
                0,
                255
            )


        # ====================================================
        # PROJECT TITLE
        # ====================================================

        cv2.putText(
            frame,
            "VisionEdge AI - Smart Object Detection",
            (
                20,
                30
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (
                255,
                255,
                255
            ),
            2
        )


        # ====================================================
        # FPS
        # ====================================================

        cv2.putText(
            frame,
            f"FPS : {int(fps)}",
            (
                20,
                70
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                255,
                0,
                0
            ),
            2
        )


        # ====================================================
        # PERSONS
        # ====================================================

        cv2.putText(
            frame,
            f"Persons : {person_count}",
            (
                20,
                110
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                0,
                255,
                0
            ),
            2
        )


        # ====================================================
        # PHONES
        # ====================================================

        cv2.putText(
            frame,
            f"Phones : {phone_count}",
            (
                20,
                150
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                0,
                255,
                255
            ),
            2
        )


        # ====================================================
        # CARS
        # ====================================================

        cv2.putText(
            frame,
            f"Cars : {car_count}",
            (
                20,
                190
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                255,
                0,
                0
            ),
            2
        )


        # ====================================================
        # BUSES
        # ====================================================

        cv2.putText(
            frame,
            f"Buses : {bus_count}",
            (
                20,
                230
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                0,
                0,
                255
            ),
            2
        )


        # ====================================================
        # TRUCKS
        # ====================================================

        cv2.putText(
            frame,
            f"Trucks : {truck_count}",
            (
                20,
                270
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                255,
                0,
                255
            ),
            2
        )


        # ====================================================
        # MOTORCYCLES
        # ====================================================

        cv2.putText(
            frame,
            f"Motorcycles : {motorcycle_count}",
            (
                20,
                310
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                0,
                165,
                255
            ),
            2
        )


        # ====================================================
        # TOTAL OBJECTS
        # ====================================================

        cv2.putText(
            frame,
            f"Total Objects : {total_objects}",
            (
                20,
                350
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                0,
                255,
                255
            ),
            2
        )


        # ====================================================
        # DATE
        # ====================================================

        cv2.putText(
            frame,
            f"Date : {current_date}",
            (
                20,
                390
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                255,
                255,
                255
            ),
            2
        )


        # ====================================================
        # TIME
        # ====================================================

        cv2.putText(
            frame,
            f"Time : {current_time}",
            (
                20,
                430
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                255,
                255,
                255
            ),
            2
        )


        # ====================================================
        # STATUS
        # ====================================================

        cv2.putText(
            frame,
            f"Status : {status}",
            (
                20,
                470
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2
        )


        # ====================================================
        # RECORDING INDICATOR
        # ====================================================

        rec_x = max(
            frame.shape[1] - 130,
            100
        )


        cv2.circle(
            frame,
            (
                rec_x,
                30
            ),
            8,
            (
                0,
                0,
                255
            ),
            -1
        )


        cv2.putText(
            frame,
            "REC",
            (
                rec_x + 20,
                35
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                0,
                0,
                255
            ),
            2
        )


        # ====================================================
        # WRITE FRAME
        # ====================================================

        video.write(
            frame
        )


        # ====================================================
        # PROGRESS
        # ====================================================

        if frame_number % 30 == 0:

            if total_frames > 0:

                progress = (
                    frame_number /
                    total_frames
                ) * 100

                print(
                    f"Processing: "
                    f"{progress:.1f}%"
                )

            else:

                print(
                    f"Processed frame: "
                    f"{frame_number}"
                )


        # ====================================================
        # MEMORY CLEANUP
        # ====================================================

        if (
            frame_number
            %
            GC_INTERVAL
            ==
            0
        ):

            gc.collect()


        # Release current frame reference
        del frame


except Exception as e:

    print("")
    print(
        "ERROR during video processing:",
        e
    )

    import traceback

    traceback.print_exc()


# ============================================================
# RELEASE VIDEO
# ============================================================

camera.release()

video.release()

log_file.close()

gc.collect()


print("")
print("OpenCV processing finished.")


# ============================================================
# FINAL STATISTICS
# ============================================================

stats = {

    "persons":
        max_person_count,

    "phones":
        max_phone_count,

    "cars":
        max_car_count,

    "buses":
        max_bus_count,

    "trucks":
        max_truck_count,

    "motorcycles":
        max_motorcycle_count,

    "bicycles":
        max_bicycle_count,

    "total_objects":
        max_total_objects,

    "fps":
        max_fps
}


# ============================================================
# SAVE stats.json
# ============================================================

with open(
    stats_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        stats,
        f,
        indent=4
    )


print(
    "Statistics saved:",
    stats_path
)


# ============================================================
# CONVERT VIDEO USING FFMPEG
# ============================================================

print("")
print("========================================")
print("Converting video for browser...")
print("========================================")


ffmpeg_path = shutil.which(
    "ffmpeg"
)


if ffmpeg_path is None:

    ffmpeg_path = "ffmpeg"


print(
    "FFmpeg:",
    ffmpeg_path
)


try:

    ffmpeg_command = [

        ffmpeg_path,

        "-y",

        "-i",
        temp_output_path,

        "-c:v",
        "libx264",

        "-preset",
        "fast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        "-an",

        final_output_path
    ]


    subprocess.run(
        ffmpeg_command,
        check=True
    )


    print(
        "Browser-compatible video created."
    )


    # Delete temporary video

    if os.path.exists(
        temp_output_path
    ):

        os.remove(
            temp_output_path
        )


except FileNotFoundError:

    print(
        "ERROR: FFmpeg was not found."
    )

    print(
        "Keeping temporary video."
    )


    if os.path.exists(
        temp_output_path
    ):

        os.replace(
            temp_output_path,
            final_output_path
        )


except subprocess.CalledProcessError as e:

    print(
        "FFmpeg conversion failed:",
        e
    )


    # Keep temporary video as fallback

    if os.path.exists(
        temp_output_path
    ):

        os.replace(
            temp_output_path,
            final_output_path
        )


# ============================================================
# CHECK FINAL OUTPUT
# ============================================================

if os.path.exists(
    final_output_path
):

    print(
        "Output video exists."
    )

else:

    print(
        "WARNING: Output video was not created."
    )


# ============================================================
# FINAL MESSAGE
# ============================================================

print("")
print("========================================")
print("DETECTION COMPLETED")
print("========================================")

print(
    "Output video:"
)

print(
    final_output_path
)

print("")

print(
    "Statistics:"
)

print(
    stats
)

print("")

print(
    "Statistics file:"
)

print(
    stats_path
)

print("")
print("========================================")


# ============================================================
# EXIT
# ============================================================

sys.exit(0)