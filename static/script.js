const videoInput = document.getElementById("videoInput");
const startBtn = document.getElementById("startBtn");

const videoPlaceholder = document.getElementById("videoPlaceholder");
const outputVideo = document.getElementById("outputVideo");

const detectionStatus = document.getElementById("detectionStatus");
const lastDetection = document.getElementById("lastDetection");


videoInput.addEventListener("change", function () {

    if (videoInput.files.length > 0) {

        const file = videoInput.files[0];

        lastDetection.textContent =
            "Selected: " + file.name;

        detectionStatus.textContent = "VIDEO SELECTED";

    } else {

        detectionStatus.textContent = "READY";
        lastDetection.textContent = "No detection yet";
    }
});


startBtn.addEventListener("click", function () {

    if (videoInput.files.length === 0) {

        alert("Please select a video first.");
        return;
    }

    detectionStatus.textContent = "STARTING...";
    lastDetection.textContent = "Detection is being prepared...";

    startBtn.disabled = true;
    startBtn.textContent = "⏳ Processing...";

    /*
     * Backend connection will be added on Day 2.
     * For now this confirms that the frontend is working.
     */

    setTimeout(function () {

        detectionStatus.textContent = "READY";

        lastDetection.textContent =
            "Frontend ready — backend connection coming next.";

        startBtn.disabled = false;
        startBtn.textContent = "▶ Start Detection";

    }, 1500);
});