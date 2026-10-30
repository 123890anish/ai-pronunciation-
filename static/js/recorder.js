/**
 * Audio Recording and Submission Client Engine.
 * Manages MediaRecorder API, timer, audio preview, and multipart blob upload.
 */
document.addEventListener("DOMContentLoaded", () => {
    const recordToggleBtn = document.getElementById("recordToggleBtn");
    const recordIcon = document.getElementById("recordIcon");
    const timerDisplay = document.getElementById("timerDisplay");
    const recordingStatus = document.getElementById("recordingStatus");
    const audioPreviewSection = document.getElementById("audioPreviewSection");
    const audioPlayback = document.getElementById("audioPlayback");
    const discardBtn = document.getElementById("discardBtn");
    const submitRecordingBtn = document.getElementById("submitRecordingBtn");
    const recordedBlobInput = document.getElementById("recordedBlobInput");
    const recordedAudioForm = document.getElementById("recordedAudioForm");
    const uploadAudioForm = document.getElementById("uploadAudioForm");
    const micPermissionDenied = document.getElementById("micPermissionDenied");
    const processingIndicator = document.getElementById("processingIndicator");

    let mediaRecorder = null;
    let audioChunks = [];
    let recordInterval = null;
    let secondsElapsed = 0;
    let isRecording = false;
    let audioBlob = null;

    // Detect browser-supported MIME type
    function getSupportedMimeType() {
        const types = [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/mp4",
            "audio/ogg;codecs=opus",
            "audio/wav",
        ];
        for (const t of types) {
            if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(t)) {
                return t;
            }
        }
        return "audio/webm";
    }

    function formatTime(totalSeconds) {
        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    }

    async function startRecording() {
        audioChunks = [];
        secondsElapsed = 0;
        timerDisplay.textContent = "00:00";

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mimeType = getSupportedMimeType();
            mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });

            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                // Stop all tracks to release microphone hardware indicator
                stream.getTracks().forEach((track) => track.stop());

                const finalType = mediaRecorder.mimeType || "audio/webm";
                audioBlob = new Blob(audioChunks, { type: finalType });
                const audioUrl = URL.createObjectURL(audioBlob);

                audioPlayback.src = audioUrl;
                audioPreviewSection.classList.remove("d-none");
                submitRecordingBtn.classList.remove("d-none");
                recordingStatus.textContent = "Recording complete! Preview or submit below.";
            };

            mediaRecorder.start(250); // Slice chunks every 250ms
            isRecording = true;

            // UI feedback
            recordToggleBtn.classList.remove("btn-outline-danger");
            recordToggleBtn.classList.add("btn-danger", "record-btn-pulse");
            recordIcon.className = "bi bi-stop-fill display-5";
            recordingStatus.textContent = "Recording in progress... Click again to finish.";
            micPermissionDenied.classList.add("d-none");

            // Timer interval
            recordInterval = setInterval(() => {
                secondsElapsed++;
                timerDisplay.textContent = formatTime(secondsElapsed);
                if (secondsElapsed >= 180) { // Max 3 minutes
                    stopRecording();
                }
            }, 1000);

        } catch (err) {
            console.error("Microphone access error:", err);
            micPermissionDenied.classList.remove("d-none");
            recordingStatus.textContent = "Could not access microphone.";
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }
        clearInterval(recordInterval);
        isRecording = false;

        recordToggleBtn.classList.remove("btn-danger", "record-btn-pulse");
        recordToggleBtn.classList.add("btn-outline-danger");
        recordIcon.className = "bi bi-mic-fill display-5";
    }

    function resetRecording() {
        stopRecording();
        audioChunks = [];
        audioBlob = null;
        secondsElapsed = 0;
        timerDisplay.textContent = "00:00";
        audioPlayback.src = "";
        audioPreviewSection.classList.add("d-none");
        submitRecordingBtn.classList.add("d-none");
        recordingStatus.textContent = "Click the microphone to start speaking";
    }

    if (recordToggleBtn) {
        recordToggleBtn.addEventListener("click", () => {
            if (isRecording) {
                stopRecording();
            } else {
                audioPreviewSection.classList.add("d-none");
                submitRecordingBtn.classList.add("d-none");
                startRecording();
            }
        });
    }

    if (discardBtn) {
        discardBtn.addEventListener("click", resetRecording);
    }

    // Submit recorded audio file
    if (submitRecordingBtn) {
        submitRecordingBtn.addEventListener("click", () => {
            if (!audioBlob) {
                alert("Please record audio before submitting.");
                return;
            }

            // Create File from Blob
            const ext = audioBlob.type.includes("wav") ? "wav" : audioBlob.type.includes("ogg") ? "ogg" : "webm";
            const file = new File([audioBlob], `spoken_recording_${Date.now()}.${ext}`, { type: audioBlob.type });

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            recordedBlobInput.files = dataTransfer.files;

            // Show loading UI to prevent duplicate submissions
            submitRecordingBtn.disabled = true;
            recordToggleBtn.disabled = true;
            processingIndicator.classList.remove("d-none");

            recordedAudioForm.submit();
        });
    }

    // Submit uploaded file
    if (uploadAudioForm) {
        uploadAudioForm.addEventListener("submit", () => {
            const submitBtn = document.getElementById("submitUploadBtn");
            if (submitBtn) submitBtn.disabled = true;
            processingIndicator.classList.remove("d-none");
        });
    }
});
