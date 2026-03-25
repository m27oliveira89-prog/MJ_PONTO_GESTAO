(function () {
    function setStatus(message) {
        var statusElement = document.querySelector("[data-camera-status]");

        if (!statusElement) {
            return;
        }

        statusElement.textContent = message;
    }

    function fillFotoField(imageDataUrl) {
        var fotoField = document.querySelector('input[name="foto_url"]');

        if (!fotoField) {
            return;
        }

        fotoField.value = imageDataUrl;
    }

    function captureFrame(videoElement, canvasElement) {
        var context = canvasElement.getContext("2d");

        canvasElement.width = videoElement.videoWidth || 640;
        canvasElement.height = videoElement.videoHeight || 480;
        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

        return canvasElement.toDataURL("image/jpeg", 0.8);
    }

    function initializeCamera() {
        var videoElement = document.querySelector("[data-camera-preview]");
        var captureButton = document.querySelector("[data-camera-capture]");
        var canvasElement = document.querySelector("[data-camera-canvas]");

        if (!videoElement || !captureButton || !canvasElement) {
            return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus("Camera indisponivel neste navegador.");
            return;
        }

        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                videoElement.srcObject = stream;
                setStatus("Camera pronta para captura.");

                captureButton.addEventListener("click", function () {
                    var imageDataUrl = captureFrame(videoElement, canvasElement);
                    fillFotoField(imageDataUrl);
                    setStatus("Foto capturada com sucesso.");
                });
            })
            .catch(function () {
                setStatus("Nao foi possivel acessar a camera.");
            });
    }

    document.addEventListener("DOMContentLoaded", initializeCamera);
})();
