// =========================================================
// ELEMENTS
// =========================================================

const videoInput =
    document.getElementById("videoInput");

const startBtn =
    document.getElementById("startBtn");

const detectionStatus =
    document.getElementById("detectionStatus");

const lastDetection =
    document.getElementById("lastDetection");

const outputVideo =
    document.getElementById("outputVideo");

const videoPlaceholder =
    document.getElementById("videoPlaceholder");


// =========================================================
// MODE BUTTONS
// =========================================================

const uploadModeBtn =
    document.getElementById("uploadModeBtn");

const cameraModeBtn =
    document.getElementById("cameraModeBtn");

const uploadPanel =
    document.getElementById("uploadPanel");

const cameraPanel =
    document.getElementById("cameraPanel");


// =========================================================
// CAMERA ELEMENTS
// =========================================================

const cameraVideo =
    document.getElementById("cameraVideo");

const cameraCanvas =
    document.getElementById("cameraCanvas");

const startCameraBtn =
    document.getElementById("startCameraBtn");

const stopCameraBtn =
    document.getElementById("stopCameraBtn");

const cameraMessage =
    document.getElementById("cameraMessage");


// =========================================================
// CAMERA VARIABLES
// =========================================================

let cameraStream = null;

let cameraRunning = false;

let cameraProcessing = false;

let cameraInterval = null;


// =========================================================
// UPDATE STATISTICS
// =========================================================

function updateStatistics(stats) {

    console.log(
        "Received statistics:",
        stats
    );


    document.getElementById("persons").textContent =
        stats.persons ?? 0;


    document.getElementById("phones").textContent =
        stats.phones ?? 0;


    document.getElementById("cars").textContent =
        stats.cars ?? 0;


    document.getElementById("buses").textContent =
        stats.buses ?? 0;


    document.getElementById("trucks").textContent =
        stats.trucks ?? 0;


    document.getElementById("motorcycles").textContent =
        stats.motorcycles ?? 0;


    document.getElementById("totalObjects").textContent =
        stats.total_objects ?? 0;


    document.getElementById("fps").textContent =
        stats.fps ?? 0;
}


// =========================================================
// RESET STATISTICS
// =========================================================

function resetStatistics() {

    updateStatistics({

        persons: 0,

        phones: 0,

        cars: 0,

        buses: 0,

        trucks: 0,

        motorcycles: 0,

        total_objects: 0,

        fps: 0

    });
}


// =========================================================
// UPLOAD MODE
// =========================================================

uploadModeBtn.addEventListener(
    "click",
    function () {

        uploadModeBtn.classList.add(
            "active"
        );

        cameraModeBtn.classList.remove(
            "active"
        );


        uploadPanel.style.display =
            "block";

        cameraPanel.style.display =
            "none";


        stopCamera();

    }
);


// =========================================================
// CAMERA MODE
// =========================================================

cameraModeBtn.addEventListener(
    "click",
    function () {

        cameraModeBtn.classList.add(
            "active"
        );

        uploadModeBtn.classList.remove(
            "active"
        );


        uploadPanel.style.display =
            "none";

        cameraPanel.style.display =
            "block";


        detectionStatus.textContent =
            "READY";

        lastDetection.textContent =
            "Ready to start live camera.";

    }
);


// =========================================================
// START UPLOADED VIDEO DETECTION
// =========================================================

startBtn.addEventListener(
    "click",
    async function () {

        if (
            !videoInput.files ||
            videoInput.files.length === 0
        ) {

            alert(
                "Please select a video first."
            );

            return;
        }


        const videoFile =
            videoInput.files[0];


        const formData =
            new FormData();


        formData.append(
            "video",
            videoFile
        );


        detectionStatus.textContent =
            "PROCESSING...";


        lastDetection.textContent =
            "YOLO detection is running...";


        startBtn.disabled =
            true;


        startBtn.textContent =
            "⏳ Processing...";


        try {

            const response =
                await fetch(
                    "/detect",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Server error: " +
                    response.status
                );

            }


            const data =
                await response.json();


            console.log(
                "Flask response:",
                data
            );


            if (data.success) {

                detectionStatus.textContent =
                    "COMPLETED";


                lastDetection.textContent =
                    data.message;


                if (data.stats) {

                    updateStatistics(
                        data.stats
                    );

                }


                if (data.output) {

                    videoPlaceholder.style.display =
                        "none";


                    outputVideo.style.display =
                        "block";


                    outputVideo.src =
                        data.output +
                        "?t=" +
                        Date.now();


                    outputVideo.load();

                }

            }

            else {

                detectionStatus.textContent =
                    "ERROR";


                lastDetection.textContent =
                    data.message ||
                    "Detection failed.";


                alert(
                    data.message ||
                    "Detection failed."
                );

            }

        }

        catch (error) {

            console.error(
                "Detection error:",
                error
            );


            detectionStatus.textContent =
                "ERROR";


            lastDetection.textContent =
                "Connection failed.";


            alert(
                "Could not connect to Flask server."
            );

        }

        finally {

            startBtn.disabled =
                false;


            startBtn.textContent =
                "▶ Start Detection";

        }

    }
);


// =========================================================
// START CAMERA
// =========================================================

startCameraBtn.addEventListener(
    "click",
    startCamera
);


// =========================================================
// START CAMERA FUNCTION
// =========================================================

async function startCamera() {

    if (cameraRunning) {

        return;

    }


    try {

        detectionStatus.textContent =
            "STARTING...";


        lastDetection.textContent =
            "Requesting camera permission...";


        cameraMessage.textContent =
            "Starting camera...";


        cameraStream =
            await navigator.mediaDevices.getUserMedia({

                video: {
                    width: {
                        ideal: 640
                    },

                    height: {
                        ideal: 480
                    },

                    facingMode: "user"
                },

                audio: false

            });


        cameraVideo.srcObject =
            cameraStream;


        await cameraVideo.play();


        cameraRunning =
            true;


        startCameraBtn.disabled =
            true;


        stopCameraBtn.disabled =
            false;


        detectionStatus.textContent =
            "LIVE";


        lastDetection.textContent =
            "Live YOLO detection is running.";


        cameraMessage.textContent =
            "🟢 Camera active — YOLO detecting objects";


        // Set canvas size

        cameraCanvas.width =
            cameraVideo.videoWidth ||
            640;


        cameraCanvas.height =
            cameraVideo.videoHeight ||
            480;


        // Start detection loop

        processCameraFrame();

    }

    catch (error) {

        console.error(
            "Camera error:",
            error
        );


        detectionStatus.textContent =
            "ERROR";


        cameraMessage.textContent =
            "❌ Camera could not be started.";


        lastDetection.textContent =
            "Please allow camera permission.";


        alert(
            "Camera access failed. Please allow camera permission in your browser."
        );

    }

}


// =========================================================
// PROCESS CAMERA FRAME
// =========================================================

async function processCameraFrame() {

    if (!cameraRunning) {

        return;

    }


    if (
        cameraVideo.readyState <
        2
    ) {

        requestAnimationFrame(
            processCameraFrame
        );

        return;

    }


    // Don't send another frame while
    // previous frame is processing

    if (cameraProcessing) {

        setTimeout(
            processCameraFrame,
            30
        );

        return;

    }


    cameraProcessing =
        true;


    try {

        const canvas =
            document.createElement(
                "canvas"
            );


        canvas.width =
            cameraVideo.videoWidth;


        canvas.height =
            cameraVideo.videoHeight;


        const context =
            canvas.getContext(
                "2d"
            );


        context.drawImage(
            cameraVideo,
            0,
            0,
            canvas.width,
            canvas.height
        );


        canvas.toBlob(
            async function (blob) {

                if (!blob) {

                    cameraProcessing =
                        false;

                    processCameraFrame();

                    return;

                }


                try {

                    const formData =
                        new FormData();


                    formData.append(
                        "frame",
                        blob,
                        "camera.jpg"
                    );


                    const response =
                        await fetch(
                            "/live_detect",
                            {
                                method: "POST",
                                body: formData
                            }
                        );


                    if (
                        !response.ok
                    ) {

                        throw new Error(
                            "Live detection server error"
                        );

                    }


                    // Read statistics
                    // from response headers

                    const stats = {

                        persons:
                            Number(
                                response.headers.get(
                                    "X-Persons"
                                ) || 0
                            ),

                        phones:
                            Number(
                                response.headers.get(
                                    "X-Phones"
                                ) || 0
                            ),

                        cars:
                            Number(
                                response.headers.get(
                                    "X-Cars"
                                ) || 0
                            ),

                        buses:
                            Number(
                                response.headers.get(
                                    "X-Buses"
                                ) || 0
                            ),

                        trucks:
                            Number(
                                response.headers.get(
                                    "X-Trucks"
                                ) || 0
                            ),

                        motorcycles:
                            Number(
                                response.headers.get(
                                    "X-Motorcycles"
                                ) || 0
                            ),

                        total_objects:
                            Number(
                                response.headers.get(
                                    "X-Total-Objects"
                                ) || 0
                            ),

                        fps:
                            Number(
                                response.headers.get(
                                    "X-FPS"
                                ) || 0
                            )

                    };


                    updateStatistics(
                        stats
                    );


                    // Get processed image

                    const imageBlob =
                        await response.blob();


                    const imageURL =
                        URL.createObjectURL(
                            imageBlob
                        );


                    const image =
                        new Image();


                    image.onload =
                        function () {

                            cameraCanvas.width =
                                image.width;

                            cameraCanvas.height =
                                image.height;


                            const ctx =
                                cameraCanvas.getContext(
                                    "2d"
                                );


                            ctx.drawImage(
                                image,
                                0,
                                0
                            );


                            URL.revokeObjectURL(
                                imageURL
                            );

                        };


                    image.src =
                        imageURL;


                    detectionStatus.textContent =
                        "LIVE";


                    lastDetection.textContent =
                        stats.total_objects > 0
                            ? "Objects detected in live camera."
                            : "No supported objects detected.";

                }

                catch (error) {

                    console.error(
                        "Live detection error:",
                        error
                    );

                }

                finally {

                    cameraProcessing =
                        false;


                    if (cameraRunning) {

                        setTimeout(
                            processCameraFrame,
                            50
                        );

                    }

                }

            },

            "image/jpeg",

            0.75
        );

    }

    catch (error) {

        console.error(
            "Frame error:",
            error
        );


        cameraProcessing =
            false;


        if (cameraRunning) {

            setTimeout(
                processCameraFrame,
                100
            );

        }

    }

}


// =========================================================
// STOP CAMERA
// =========================================================

stopCameraBtn.addEventListener(
    "click",
    stopCamera
);


// =========================================================
// STOP CAMERA FUNCTION
// =========================================================

function stopCamera() {

    cameraRunning =
        false;


    cameraProcessing =
        false;


    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach(
                function (track) {

                    track.stop();

                }
            );

        cameraStream =
            null;

    }


    cameraVideo.srcObject =
        null;


    startCameraBtn.disabled =
        false;


    stopCameraBtn.disabled =
        true;


    cameraMessage.textContent =
        "Camera is stopped";


    detectionStatus.textContent =
        "READY";


    lastDetection.textContent =
        "Live camera stopped.";


    resetStatistics();


    const ctx =
        cameraCanvas.getContext(
            "2d"
        );


    ctx.clearRect(
        0,
        0,
        cameraCanvas.width,
        cameraCanvas.height
    );

}


// =========================================================
// PAGE CLOSE
// =========================================================

window.addEventListener(
    "beforeunload",
    function () {

        stopCamera();

    }
);