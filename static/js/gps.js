(function () {
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
        var gpsStatus = document.querySelector("[data-gps-status]");

        if (!gpsStatus) {
            return;
        }

        gpsStatus.textContent = "Localizacao indisponivel no momento.";
    }

    function requestLocation() {
        var gpsStatus = document.querySelector("[data-gps-status]");

        if (!navigator.geolocation) {
            handleGpsError();
            return;
        }

        if (gpsStatus) {
            gpsStatus.textContent = "Obtendo localizacao...";
        }

        navigator.geolocation.getCurrentPosition(
            function (position) {
                updateGpsFields(position);

                if (gpsStatus) {
                    gpsStatus.textContent = "Localizacao capturada com sucesso.";
                }
            },
            handleGpsError,
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }

    document.addEventListener("DOMContentLoaded", requestLocation);
})();
