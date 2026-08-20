# Portions copyright (c) 2014–Present DJI. All rights reserved.

import csv
import json
from pathlib import Path

import numpy as np
import tifffile


# Fields required for the Metashape workflow.
REQUIRED_XMP_FIELDS = [
    "GpsLatitude",
    "GpsLongitude",
    "AbsoluteAltitude",
    "GimbalYawDegree",
    "GimbalPitchDegree",
    "GimbalRollDegree",
]

# Missing optional fields produce warnings but do not invalidate the TIFF.
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
    Validate a single converted thermal TIFF.

    Returns a dictionary with status (PASS, WARNING, or FAIL), errors,
    and warnings.
    """
    tiff_path = Path(tiff_path)

    errors = []
    warnings = []

    if not tiff_path.exists():
        return {
            "status": "FAIL",
            "errors": [
                f"TIFF file does not exist: {tiff_path}"
            ],
            "warnings": [],
        }

    try:
        with tifffile.TiffFile(tiff_path) as tif:
            if len(tif.pages) == 0:
                return {
                    "status": "FAIL",
                    "errors": [
                        "TIFF does not contain any pages."
                    ],
                    "warnings": [],
                }

            page = tif.pages[0]
            data = page.asarray()

            if data.ndim != 2:
                errors.append(
                    f"Raster is not single-band: ndim={data.ndim}"
                )

            if data.dtype != np.float32:
                errors.append(
                    f"Invalid raster data type: {data.dtype}"
                )

            if not np.isfinite(data).all():
                errors.append(
                    "Raster contains NaN or Inf values."
                )

            for tag_name in [
                "Make",
                "Model",
                "DateTime",
            ]:
                if page.tags.get(tag_name) is None:
                    warnings.append(
                        f"Missing standard TIFF tag: {tag_name}"
                    )

            description = page.description

            if not description:
                errors.append(
                    "Missing ImageDescription."
                )
                return {
                    "status": "FAIL",
                    "errors": errors,
                    "warnings": warnings,
                }

            try:
                metadata = json.loads(description)
            except json.JSONDecodeError:
                errors.append(
                    "ImageDescription is not valid JSON."
                )
                return {
                    "status": "FAIL",
                    "errors": errors,
                    "warnings": warnings,
                }

            temperature = metadata.get(
                "temperature",
                {},
            )

            if temperature.get("unit") != "Celsius":
                errors.append(
                    "Missing or invalid temperature unit."
                )

            if temperature.get("data_type") != "float32":
                errors.append(
                    "Missing or invalid temperature data_type."
                )

            expected_width = temperature.get("width")
            expected_height = temperature.get("height")

            if (
                expected_width is None
                or expected_height is None
            ):
                errors.append(
                    "Missing raster dimensions in metadata."
                )
            else:
                expected_shape = (
                    int(expected_height),
                    int(expected_width),
                )

                if data.shape != expected_shape:
                    errors.append(
                        f"Raster shape {data.shape} does not match "
                        f"metadata shape {expected_shape}."
                    )

            metadata_min = temperature.get("min")
            metadata_max = temperature.get("max")

            if metadata_min is None:
                errors.append(
                    "Missing minimum temperature in metadata."
                )
            elif not np.isclose(
                float(data.min()),
                float(metadata_min),
                atol=1e-5,
            ):
                errors.append(
                    "Raster minimum temperature does not match metadata."
                )

            if metadata_max is None:
                errors.append(
                    "Missing maximum temperature in metadata."
                )
            elif not np.isclose(
                float(data.max()),
                float(metadata_max),
                atol=1e-5,
            ):
                errors.append(
                    "Raster maximum temperature does not match metadata."
                )

            radiometry = metadata.get(
                "radiometry",
                {},
            )

            for field in REQUIRED_RADIOMETRY_FIELDS:
                if radiometry.get(field) is None:
                    errors.append(
                        f"Missing radiometry field: {field}"
                    )

            source_metadata = metadata.get(
                "source_metadata",
                {},
            )

            exif = source_metadata.get(
                "exif",
                {},
            )

            dji_xmp = source_metadata.get(
                "dji_xmp",
                {},
            )

            if not exif:
                warnings.append(
                    "Source EXIF metadata is missing."
                )

            if not dji_xmp:
                errors.append(
                    "DJI XMP metadata is missing."
                )
            else:
                for field in REQUIRED_XMP_FIELDS:
                    value = dji_xmp.get(field)

                    if value is None or value == "":
                        errors.append(
                            f"Missing required DJI XMP field: {field}"
                        )

                for field in OPTIONAL_XMP_FIELDS:
                    value = dji_xmp.get(field)

                    if value is None or value == "":
                        warnings.append(
                            f"Missing optional DJI XMP field: {field}"
                        )

    except Exception as exc:
        errors.append(
            f"Failed to read TIFF: {exc}"
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
    """Validate multiple TIFF files and return batch validation statistics."""
    results = []

    passed = 0
    warnings_count = 0
    failed = 0

    for tiff_path in tiff_paths:
        tiff_path = Path(tiff_path)

        validation = validate_tiff(tiff_path)

        status = validation["status"]
        errors = validation["errors"]
        warnings = validation["warnings"]

        if status == "PASS":
            passed += 1
        elif status == "WARNING":
            warnings_count += 1
        else:
            failed += 1

        results.append(
            {
                "file": str(tiff_path),
                "filename": tiff_path.name,
                "valid": status != "FAIL",
                "status": status,
                "errors": errors,
                "warnings": warnings,
            }
        )

    return {
        "passed": passed,
        "warnings": warnings_count,
        "failed": failed,
        "total": len(results),
        "results": results,
    }


def save_validation_report(
    validation_result,
    report_path,
):
    """Write validation results to a CSV report."""
    report_path = Path(report_path)

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with report_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
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
            ],
        )

        writer.writeheader()

        for result in validation_result["results"]:
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])

            writer.writerow(
                {
                    "filename": result.get(
                        "filename",
                        "",
                    ),
                    "status": result.get(
                        "status",
                        "",
                    ),
                    "error_count": len(errors),
                    "warning_count": len(warnings),
                    "errors": " | ".join(errors),
                    "warnings": " | ".join(warnings),
                }
            )

    return report_path
