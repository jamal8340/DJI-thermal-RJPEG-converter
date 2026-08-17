import json
from pathlib import Path

import numpy as np
import tifffile


REQUIRED_XMP_FIELDS = [
    "GpsLatitude",
    "GpsLongitude",
    "AbsoluteAltitude",
    "RelativeAltitude",
    "GimbalRollDegree",
    "GimbalYawDegree",
    "GimbalPitchDegree",
    "FlightRollDegree",
    "FlightYawDegree",
    "FlightPitchDegree",
    "UTCAtExposure",
    "CameraSerialNumber",
    "DroneSerialNumber",
]

REQUIRED_RADIOMETRY_FIELDS = [
    "distance",
    "humidity",
    "emissivity",
    "reflection",
    "ambient_temp",
]


def validate_tiff(tiff_path):
    """
    Waliduje pojedynczy plik TIFF.

    Zwraca listę błędów.
    Pusta lista oznacza poprawny plik.
    """

    tiff_path = Path(tiff_path)
    errors = []

    if not tiff_path.exists():
        return [
            f"Plik TIFF nie istnieje: {tiff_path}"
        ]

    try:
        with tifffile.TiffFile(tiff_path) as tif:
            if len(tif.pages) == 0:
                return [
                    "TIFF nie zawiera żadnej strony."
                ]

            page = tif.pages[0]
            data = page.asarray()

            # Raster musi być jednopasmowy.
            if data.ndim != 2:
                errors.append(
                    f"Raster nie jest jednopasmowy: ndim={data.ndim}"
                )

            # Temperatura powinna być Float32.
            if data.dtype != np.float32:
                errors.append(
                    f"Niepoprawny typ danych: {data.dtype}"
                )

            # Nie akceptujemy NaN ani Inf.
            if not np.isfinite(data).all():
                errors.append(
                    "Raster zawiera NaN lub Inf."
                )

            # Standardowe tagi TIFF.
            for tag_name in [
                "Make",
                "Model",
                "DateTime",
            ]:
                if page.tags.get(tag_name) is None:
                    errors.append(
                        f"Brak standardowego tagu TIFF: {tag_name}"
                    )

            # Pełne metadane zapisane jako JSON.
            description = page.description

            if not description:
                errors.append(
                    "Brak ImageDescription."
                )
                return errors

            try:
                metadata = json.loads(description)

            except json.JSONDecodeError:
                errors.append(
                    "ImageDescription nie jest poprawnym JSON-em."
                )
                return errors

            # Dane temperatury.
            temperature = metadata.get(
                "temperature",
                {}
            )

            if temperature.get("unit") != "Celsius":
                errors.append(
                    "Niepoprawna lub brakująca jednostka temperatury."
                )

            if temperature.get("data_type") != "float32":
                errors.append(
                    "Niepoprawny lub brakujący data_type."
                )

            expected_width = temperature.get("width")
            expected_height = temperature.get("height")

            if (
                expected_width is None
                or expected_height is None
            ):
                errors.append(
                    "Brak wymiarów obrazu w metadanych."
                )

            else:
                expected_shape = (
                    int(expected_height),
                    int(expected_width),
                )

                if data.shape != expected_shape:
                    errors.append(
                        f"Niezgodny rozmiar rastra: "
                        f"{data.shape}, "
                        f"oczekiwano {expected_shape}."
                    )

            # Sprawdzenie min/max temperatury.
            metadata_min = temperature.get("min")
            metadata_max = temperature.get("max")

            if metadata_min is None:
                errors.append(
                    "Brak minimalnej temperatury w metadanych."
                )

            elif not np.isclose(
                float(data.min()),
                float(metadata_min),
                atol=1e-5,
            ):
                errors.append(
                    "Minimalna temperatura rastra "
                    "nie zgadza się z metadanymi."
                )

            if metadata_max is None:
                errors.append(
                    "Brak maksymalnej temperatury w metadanych."
                )

            elif not np.isclose(
                float(data.max()),
                float(metadata_max),
                atol=1e-5,
            ):
                errors.append(
                    "Maksymalna temperatura rastra "
                    "nie zgadza się z metadanymi."
                )

            # Radiometria.
            radiometry = metadata.get(
                "radiometry",
                {}
            )

            for field in REQUIRED_RADIOMETRY_FIELDS:
                if radiometry.get(field) is None:
                    errors.append(
                        f"Brak radiometrii: {field}"
                    )

            # EXIF + DJI XMP.
            source_metadata = metadata.get(
                "source_metadata",
                {}
            )

            exif = source_metadata.get(
                "exif",
                {}
            )

            dji_xmp = source_metadata.get(
                "dji_xmp",
                {}
            )

            if not exif:
                errors.append(
                    "Brak EXIF."
                )

            if not dji_xmp:
                errors.append(
                    "Brak DJI XMP."
                )

            for field in REQUIRED_XMP_FIELDS:
                value = dji_xmp.get(field)

                if value is None or value == "":
                    errors.append(
                        f"Brak DJI XMP: {field}"
                    )

    except Exception as exc:
        errors.append(
            f"Błąd odczytu TIFF: {exc}"
        )

    return errors


def validate_files(tiff_paths):
    """
    Waliduje listę TIFF-ów.

    Zwraca podsumowanie:
    passed, failed, total oraz szczegóły.
    """

    results = []

    passed = 0
    failed = 0

    for tiff_path in tiff_paths:
        tiff_path = Path(tiff_path)

        errors = validate_tiff(
            tiff_path
        )

        if errors:
            failed += 1

            results.append({
                "file": str(tiff_path),
                "valid": False,
                "errors": errors,
            })

        else:
            passed += 1

            results.append({
                "file": str(tiff_path),
                "valid": True,
                "errors": [],
            })

    return {
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "results": results,
    }