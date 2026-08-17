import csv
import json
from pathlib import Path

import numpy as np
import tifffile


# Te pola traktujemy jako krytyczne dla naszego workflow / Metashape.
REQUIRED_XMP_FIELDS = [
    "GpsLatitude",
    "GpsLongitude",
    "AbsoluteAltitude",
    "GimbalYawDegree",
    "GimbalPitchDegree",
    "GimbalRollDegree",
]

# Ich brak nie unieważnia TIFF-a.
OPTIONAL_XMP_FIELDS = [
    "RelativeAltitude",
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
    Waliduje pojedynczy TIFF.

    Zwraca:
    {
        "status": "PASS" | "WARNING" | "FAIL",
        "errors": [...],
        "warnings": [...]
    }
    """

    tiff_path = Path(tiff_path)

    errors = []
    warnings = []

    if not tiff_path.exists():
        return {
            "status": "FAIL",
            "errors": [
                f"Plik TIFF nie istnieje: {tiff_path}"
            ],
            "warnings": [],
        }

    try:
        with tifffile.TiffFile(tiff_path) as tif:
            if len(tif.pages) == 0:
                return {
                    "status": "FAIL",
                    "errors": [
                        "TIFF nie zawiera żadnej strony."
                    ],
                    "warnings": [],
                }

            page = tif.pages[0]
            data = page.asarray()

            # ---------------------------------
            # RASTER
            # ---------------------------------

            if data.ndim != 2:
                errors.append(
                    f"Raster nie jest jednopasmowy: ndim={data.ndim}"
                )

            if data.dtype != np.float32:
                errors.append(
                    f"Niepoprawny typ danych: {data.dtype}"
                )

            if not np.isfinite(data).all():
                errors.append(
                    "Raster zawiera NaN lub Inf."
                )

            # ---------------------------------
            # STANDARDOWE TAGI TIFF
            # ---------------------------------

            for tag_name in [
                "Make",
                "Model",
                "DateTime",
            ]:
                if page.tags.get(tag_name) is None:
                    warnings.append(
                        f"Brak standardowego tagu TIFF: {tag_name}"
                    )

            # ---------------------------------
            # NASZE METADATA JSON
            # ---------------------------------

            description = page.description

            if not description:
                errors.append(
                    "Brak ImageDescription."
                )

                return {
                    "status": "FAIL",
                    "errors": errors,
                    "warnings": warnings,
                }

            try:
                metadata = json.loads(
                    description
                )

            except json.JSONDecodeError:
                errors.append(
                    "ImageDescription nie jest poprawnym JSON-em."
                )

                return {
                    "status": "FAIL",
                    "errors": errors,
                    "warnings": warnings,
                }

            # ---------------------------------
            # TEMPERATURA
            # ---------------------------------

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

            expected_width = temperature.get(
                "width"
            )

            expected_height = temperature.get(
                "height"
            )

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
                        f"Niezgodny rozmiar: "
                        f"{data.shape}, "
                        f"oczekiwano {expected_shape}."
                    )

            # ---------------------------------
            # MIN / MAX
            # ---------------------------------

            metadata_min = temperature.get(
                "min"
            )

            metadata_max = temperature.get(
                "max"
            )

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

            # ---------------------------------
            # RADIOMETRIA
            # ---------------------------------

            radiometry = metadata.get(
                "radiometry",
                {}
            )

            for field in REQUIRED_RADIOMETRY_FIELDS:
                if radiometry.get(field) is None:
                    errors.append(
                        f"Brak radiometrii: {field}"
                    )

            # ---------------------------------
            # EXIF / DJI XMP
            # ---------------------------------

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
                warnings.append(
                    "Brak EXIF w metadanych źródłowych."
                )

            if not dji_xmp:
                errors.append(
                    "Brak DJI XMP."
                )

            else:
                # Krytyczne pola
                for field in REQUIRED_XMP_FIELDS:
                    value = dji_xmp.get(
                        field
                    )

                    if value is None or value == "":
                        errors.append(
                            f"Brak wymaganego DJI XMP: {field}"
                        )

                # Pola opcjonalne
                for field in OPTIONAL_XMP_FIELDS:
                    value = dji_xmp.get(
                        field
                    )

                    if value is None or value == "":
                        warnings.append(
                            f"Brak opcjonalnego DJI XMP: {field}"
                        )

    except Exception as exc:
        errors.append(
            f"Błąd odczytu TIFF: {exc}"
        )

    if errors:
        status = "FAIL"

    elif warnings:
        status = "WARNING"

    else:
        status = "PASS"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


def validate_files(tiff_paths):
    """
    Waliduje listę TIFF-ów.
    """

    results = []

    passed = 0
    warnings_count = 0
    failed = 0

    for tiff_path in tiff_paths:
        tiff_path = Path(
            tiff_path
        )

        validation = validate_tiff(
            tiff_path
        )

        status = validation[
            "status"
        ]

        errors = validation[
            "errors"
        ]

        warnings = validation[
            "warnings"
        ]

        if status == "PASS":
            passed += 1

        elif status == "WARNING":
            warnings_count += 1

        else:
            failed += 1

        results.append({
            "file": str(tiff_path),
            "filename": tiff_path.name,
            "valid": status != "FAIL",
            "status": status,
            "errors": errors,
            "warnings": warnings,
        })

    return {
        "passed": passed,
        "warnings": warnings_count,
        "failed": failed,
        "total": len(results),
        "results": results,
    }


def save_validation_report(
    validation_result,
    report_path
):
    """
    Zapisuje validation_report.csv.
    """

    report_path = Path(
        report_path
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with report_path.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "filename",
                "status",
                "error_count",
                "warning_count",
                "errors",
                "warnings",
            ]
        )

        writer.writeheader()

        for result in validation_result[
            "results"
        ]:
            errors = result.get(
                "errors",
                []
            )

            warnings = result.get(
                "warnings",
                []
            )

            writer.writerow({
                "filename": result.get(
                    "filename",
                    ""
                ),

                "status": result.get(
                    "status",
                    ""
                ),

                "error_count": len(
                    errors
                ),

                "warning_count": len(
                    warnings
                ),

                "errors": " | ".join(
                    errors
                ),

                "warnings": " | ".join(
                    warnings
                ),
            })

    return report_path