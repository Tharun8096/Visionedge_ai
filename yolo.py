from ultralytics import YOLO
import cv2
import time
from datetime import datetime
import csv
import os


# Load YOLO model
model = YOLO("yolov8n.pt")

# Open webcam
camera = cv2.VideoCapture(0)

#get camera resolution
frame_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

# video output folder
os.makedirs("output", exist_ok=True)
# create tiemstamped output video
video_filename = datetime.now().strftime("output_%Y%m%d_%H%M%S.mp4")
video_path = os.path.join("videos", video_filename)

#video codec
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

#create  output video
video = cv2.VideoWriter(video_path, fourcc, 20, (frame_width, frame_height))
print(f"Recording video: {video_path}")

# Previous time for FPS calculation
previous_time = time.time()
# previous logged object for detection log
previous_logged_object = None


# detection log 
os.makedirs("logs", exist_ok=True)
log_file_path = os.path.join("logs", "detection_log.csv")

#csv file 
log_file = open(log_file_path, "a", newline="")
csv_writer = csv.writer(log_file)
if log_file.tell() == 0:
    csv_writer.writerow(["Date", "Time", "Object", "Confidence"])

if log_file.tell() == 0:
    csv_writer.writerow(["Date", "Time", "Object", "Confidence"])


while True:

    # Read frame
    success, frame = camera.read()

    if not success:
        break

    # FPS Calculation
    current_time = time.time()
    fps = 1 / (current_time - previous_time)
    previous_time = current_time

    #time
    current_time = datetime.now()
    current_date = current_time.strftime("%d-%m-%Y")
    current_time = current_time.strftime("%H:%M:%S")


    # Counters
    person_count = 0
    phone_count = 0
    car_count = 0
    bus_count = 0
    truck_count = 0
    motorcycle_count = 0
    bicycle_count = 0
    
    total_objects = 0
    status = "NO OBJECT DETECTED"
    status_color = (0, 0, 255)  # Red

    #Last detection
    last_object = "None"
    last_confidence = 0
    # Run YOLO
    results = model(frame)

    # Process detections
    for result in results:

        for box in result.boxes:

            cls = int(box.cls[0])
            confidence = float(box.conf[0])
            last_object = model.names[cls]
            last_confidence = confidence
            if confidence < 0.50:
                continue

            # Detect only Person and Cell Phone
            if cls in [0,1,2,3,5,7,67]:

                if cls == 0:
                    person_count += 1

                elif cls == 67:
                    phone_count += 1
                elif cls == 2:
                    car_count += 1
                elif cls == 5:
                    bus_count += 1
                elif cls == 7:
                    truck_count += 1
                elif cls == 3:
                    motorcycle_count += 1
                elif cls == 1:
                    bicycle_count += 1

                total_objects += 1

                # Bounding box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])



                # Label
                label = f"{model.names[cls]} {confidence:.2f}"

                # Log detection to CSV
                if model.names[cls] != previous_logged_object:
                    csv_writer.writerow([current_date, current_time, model.names[cls], confidence])
                    log_file.flush()
                    previous_logged_object = model.names[cls]

                # Draw rectangle
                if cls == 0:
                    color = (0,255,0)

                elif cls == 67:
                    color = (0,255,255)

                elif cls == 2:
                    color = (255,0,0)

                elif cls == 5:
                    color = (0,0,255)

                elif cls == 7:
                    color = (255,0,255)

                elif cls == 3:
                    color = (0,165,255)

                else:
                    color = (255,255,255)      

                # Draw label
                cv2.putText(frame,label,(x1, y1 - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)


    #active symbols
            if total_objects> 0:
               status = "ACTIVE"
               status_color = (0, 255, 0)  # Green
            else:
                status = "NO OBJECT DETECTED"
                status_color = (0, 0, 255)  # Red

# project title
    cv2.putText(frame, "VisionEdge AI - Smart Object Detection", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,(255, 255, 255),2)

    # Display FPS
    cv2.putText(frame, f"FPS : {int(fps)}",(20, 70),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)


    # Display Person Count
    cv2.putText(frame, f"Persons : {person_count}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8,(0, 255, 0),2)

    # Display Phone Count
    cv2.putText(frame,f"Phones : {phone_count}", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255),2)

# cars count
    cv2.putText(frame, f"Cars : {car_count}", (20,190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)

# buses count
    cv2.putText(frame, f"Buses : {bus_count}", (20,230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

# trucks count
    cv2.putText(frame, f"Trucks : {truck_count}", (20,270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,255), 2)

# motorcycles count
    cv2.putText(frame, f"Motorcycles : {motorcycle_count}", (20,310), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(0,165,255), 2)

   
    # Display Total Objects
    cv2.putText(frame, f"Total Objects : {total_objects}", (20, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    #display date
    cv2.putText (frame, f"Date : {current_date}", (20, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    #display time
    cv2.putText(frame, f"Time : {current_time}", (20, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    #active status

    cv2.putText(frame, f"Status : {status}", (20, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

    #last detection
    cv2.putText(frame, f"Last Detection : {last_object} ({last_confidence:.2f})", (20, 510), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    #record indicator

    cv2.circle(frame,(900,30),8,(0,0,255),-1)

    cv2.putText(frame,
            "REC",
            (920,35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,0,255),
            2)
    #detected area
    cv2.rectangle(
    frame,
    (150,100),
    (900,600),
    (0,255,0),
    2)        
# video.write(frame)
    video.write(frame)
    # Show output
    cv2.imshow("VisionEdge AI", frame)
    # Exit on pressing 'q'
    key = cv2.waitKey(1) & 0xFF

# Press S to save screenshot
    if key == ord("s"):
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")

            filename = os.path.join("screenshots", datetime.now().strftime("screenshot_%Y-%m%d_%H%M%S.png"))

            cv2.imwrite(filename, frame)
            print("screenshot saved:", filename)


# Press Q to quit
    if key == ord("q"):
       break

# Release resources
camera.release()
video.release()
log_file.close()
cv2.destroyAllWindows()