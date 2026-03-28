(function () {
    function setGpsStatus(message) {
        var gpsStatus = document.querySelector("[data-gps-status]");

        if (!gpsStatus) {
            return;
        }

        gpsStatus.textContent = message;
    }

    function setGpsError(message) {
        var errorElement = document.querySelector("[data-gps-error]");

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

    function updateGpsFields(position) {
        var latitudeField = document.querySelector('input[name="latitude"]');
        var longitudeField = document.querySelector('input[name="longitude"]');

        if (!latitudeField || !longitudeField) {
            return;
        }

        latitudeField.value = position.coords.latitude;
        longitudeField.value = position.coords.longitude;
    }

    function handleGpsError() {
        setGpsError("Ative o GPS do seu dispositivo para registrar o ponto");
        setGpsStatus("Ative o GPS do seu dispositivo para registrar o ponto");
    }

    function validateBeforeSubmit() {
        var formElement = document.querySelector("form.form-grid");

        if (!formElement) {
            return;
        }

        formElement.addEventListener("submit", function (event) {
            var latitudeField = document.querySelector('input[name="latitude"]');
            var longitudeField = document.querySelector('input[name="longitude"]');

            if (
                !latitudeField ||
                !longitudeField ||
                !latitudeField.value ||
                !longitudeField.value
            ) {
                event.preventDefault();
                handleGpsError();
            }
        });
    }

    function requestLocation() {
        if (!navigator.geolocation) {
            handleGpsError();
            return;
        }

        setGpsStatus("Obtendo localizacao...");

        navigator.geolocation.getCurrentPosition(
            function (position) {
                updateGpsFields(position);
                setGpsError("");
                setGpsStatus("Localizacao capturada com sucesso.");
            },
            handleGpsError,
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }

    document.addEventListener("DOMContentLoaded", function () {
        requestLocation();
        validateBeforeSubmit();
    });
})();
