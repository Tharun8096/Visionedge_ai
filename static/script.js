const videoInput = document.getElementById("videoInput");
const startBtn = document.getElementById("startBtn");

const detectionStatus =
    document.getElementById("detectionStatus");

const lastDetection =
    document.getElementById("lastDetection");

const outputVideo =
    document.getElementById("outputVideo");

const videoPlaceholder =
    document.getElementById("videoPlaceholder");


// =========================================================
// UPDATE STATISTICS
// =========================================================

function updateStatistics(stats) {

    console.log("Received statistics:", stats);

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
// START DETECTION
// =========================================================

startBtn.addEventListener("click", async function () {

    if (
        !videoInput.files ||
        videoInput.files.length === 0
    ) {

        alert("Please select a video first.");

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


    startBtn.disabled = true;

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


        // =================================================
        // SUCCESS
        // =================================================

        if (data.success) {

            detectionStatus.textContent =
                "COMPLETED";


            lastDetection.textContent =
                data.message;


            // ---------------------------------------------
            // UPDATE STATISTICS
            // ---------------------------------------------

            if (data.stats) {

                updateStatistics(
                    data.stats
                );

            }


            // ---------------------------------------------
            // SHOW OUTPUT VIDEO
            // ---------------------------------------------

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


                outputVideo.oncanplay =
                    function () {

                        console.log(
                            "Output video ready."
                        );

                    };


                outputVideo.onerror =
                    function () {

                        console.error(
                            "Video playback failed."
                        );


                        lastDetection.textContent =
                            "Detection completed, but the video could not be played.";

                    };

            }

        }


        // =================================================
        // ERROR
        // =================================================

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

});