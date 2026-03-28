(function () {
    var activeStream = null;

    function setStatus(message) {
        var statusElement = document.querySelector("[data-camera-status]");

        if (!statusElement) {
            return;
        }

        statusElement.textContent = message;
    }

    function setError(message) {
        var errorElement = document.querySelector("[data-camera-error]");

        if (!errorElement) {
            return;
        }

        if (!message) {
            errorElement.hidden = true;
            errorElement.textContent = "";
            return;
        }

        errorElement.hidden = false;
        errorElement.textContent = message;
    }

    function fillFotoField(imageDataUrl) {
        var fotoField = document.querySelector('input[name="foto_url"]');

        if (!fotoField) {
            return;
        }

        fotoField.value = imageDataUrl;
    }

    function updatePhotoPreview(imageDataUrl) {
        var photoPreview = document.querySelector("[data-camera-photo-preview]");
        var videoElement = document.querySelector("[data-camera-preview]");

        if (photoPreview) {
            photoPreview.src = imageDataUrl;
            photoPreview.hidden = false;
        }

        if (videoElement) {
            videoElement.hidden = true;
        }
    }

    function captureFrame(videoElement, canvasElement) {
        var context = canvasElement.getContext("2d");

        canvasElement.width = videoElement.videoWidth || 640;
        canvasElement.height = videoElement.videoHeight || 480;
        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

        return canvasElement.toDataURL("image/jpeg", 0.8);
    }

    function startCamera(videoElement) {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus("Camera indisponivel neste navegador.");
            return Promise.resolve();
        }

        return navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: "user" }
            },
            audio: false
        })
            .then(function (stream) {
                stopActiveStream();
                activeStream = stream;
                videoElement.srcObject = stream;
                videoElement.hidden = false;
                setError("");
                setStatus("Camera pronta para captura.");
            })
            .catch(function () {
                setStatus("Nao foi possivel acessar a camera.");
            });
    }

    function stopActiveStream() {
        if (!activeStream) {
            return;
        }

        activeStream.getTracks().forEach(function (track) {
            track.stop();
        });
    }

    function validateBeforeSubmit() {
        var formElement = document.querySelector("form.form-grid");

        if (!formElement) {
            return;
        }

        formElement.addEventListener("submit", function (event) {
            var fotoField = document.querySelector('input[name="foto_url"]');

            if (fotoField && !fotoField.value) {
                event.preventDefault();
                setError("\u00c9 necess\u00e1rio tirar a foto para registrar o ponto");
                setStatus("Capture a foto antes de enviar.");
            }
        });
    }

    function initializeCamera() {
        var videoElement = document.querySelector("[data-camera-preview]");
        var openButton = document.querySelector("[data-camera-open]");
        var captureButton = document.querySelector("[data-camera-capture]");
        var canvasElement = document.querySelector("[data-camera-canvas]");

        if (!videoElement || !openButton || !captureButton || !canvasElement) {
            return;
        }

        openButton.addEventListener("click", function () {
            startCamera(videoElement);
        });

        captureButton.addEventListener("click", function () {
            if (!activeStream || !videoElement.srcObject) {
                setStatus("Abra a camera antes de capturar a foto.");
                return;
            }

            var imageDataUrl = captureFrame(videoElement, canvasElement);
            fillFotoField(imageDataUrl);
            updatePhotoPreview(imageDataUrl);
            setError("");
            setStatus("Foto capturada com sucesso.");
        });

        validateBeforeSubmit();
    }

    document.addEventListener("DOMContentLoaded", initializeCamera);
})();
