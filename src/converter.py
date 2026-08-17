import csv
import json
from pathlib import Path

import numpy as np
import tifffile

from dji_sdk import DJIThermalSDK
from metadata import extract_metadata


def build_full_metadata(temperature_matrix, radiometry_data, image_metadata):
    """Buduje komplet metadanych zapisywanych w ImageDescription."""

    return {
        "temperature": {
            "unit": "Celsius",
            "data_type": "float32",
            "width": int(temperature_matrix.shape[1]),
            "height": int(temperature_matrix.shape[0]),
            "min": float(temperature_matrix.min()),
            "max": float(temperature_matrix.max()),
        },
        "radiometry": radiometry_data,
        "source_metadata": image_metadata,
    }


def build_standard_tiff_tags(image_metadata):
    """Tworzy standardowe tagi TIFF: Make, Model, DateTime."""

    exif_data = image_metadata.get("exif", {})

    make = str(exif_data.get("Make", "DJI"))
    model = str(exif_data.get("Model", ""))

    datetime_value = str(
        exif_data.get("DateTimeOriginal")
        or exif_data.get("DateTime")
        or ""
    )

    extra_tags = []

    if make:
        extra_tags.append(
            (271, "s", len(make) + 1, make, False)
        )

    if model:
        extra_tags.append(
            (272, "s", len(model) + 1, model, False)
        )

    if datetime_value:
        extra_tags.append(
            (306, "s", len(datetime_value) + 1, datetime_value, False)
        )

    return extra_tags


def build_report_row(
    image_path,
    temperature_matrix,
    radiometry_data,
    image_metadata
):
    """Buduje jeden wiersz raportu CSV."""

    dji_xmp = image_metadata.get("dji_xmp", {})

    return {
        "filename": image_path.name,
        "status": "OK",
        "width": int(temperature_matrix.shape[1]),
        "height": int(temperature_matrix.shape[0]),
        "min_temp_c": float(temperature_matrix.min()),
        "max_temp_c": float(temperature_matrix.max()),
        "distance": radiometry_data.get("distance"),
        "humidity": radiometry_data.get("humidity"),
        "emissivity": radiometry_data.get("emissivity"),
        "reflection": radiometry_data.get("reflection"),
        "ambient_temp": radiometry_data.get("ambient_temp"),
        "gps_latitude": dji_xmp.get("GpsLatitude"),
        "gps_longitude": dji_xmp.get("GpsLongitude"),
        "absolute_altitude": dji_xmp.get("AbsoluteAltitude"),
        "relative_altitude": dji_xmp.get("RelativeAltitude"),
        "gimbal_roll": dji_xmp.get("GimbalRollDegree"),
        "gimbal_yaw": dji_xmp.get("GimbalYawDegree"),
        "gimbal_pitch": dji_xmp.get("GimbalPitchDegree"),
        "flight_roll": dji_xmp.get("FlightRollDegree"),
        "flight_yaw": dji_xmp.get("FlightYawDegree"),
        "flight_pitch": dji_xmp.get("FlightPitchDegree"),
        "utc_at_exposure": dji_xmp.get("UTCAtExposure"),
        "camera_serial": dji_xmp.get("CameraSerialNumber"),
        "drone_serial": dji_xmp.get("DroneSerialNumber"),
        "error": "",
    }


def convert_image(sdk, image_path, output_dir):
    """
    Konwertuje jeden DJI R-JPEG do jednopasmowego TIFF Float32.
    Zwraca dane do raportu CSV.
    """

    print(f"Przetwarzam plik: {image_path.name}")

    output_path = output_dir / f"{image_path.stem}.tif"

    result = sdk.process_image_info(str(image_path))

    if result is None:
        raise RuntimeError("DJI SDK nie zwrócił danych.")

    temperature_matrix, radiometry_data = result

    # EXIF + DJI XMP
    image_metadata = extract_metadata(image_path)

    # Pełne metadane do ImageDescription
    full_metadata = build_full_metadata(
        temperature_matrix,
        radiometry_data,
        image_metadata
    )

    metadata_str = json.dumps(
        full_metadata,
        indent=2,
        ensure_ascii=False
    )

    # Standardowe tagi TIFF
    extra_tags = build_standard_tiff_tags(image_metadata)

    print(f"Zapisuję do pliku: {output_path.name}...")

    tifffile.imwrite(
        str(output_path),
        temperature_matrix.astype(np.float32),
        photometric="minisblack",
        description=metadata_str,
        metadata=None,
        extratags=extra_tags
    )

    print("SUKCES!")
    print("-" * 40)

    return build_report_row(
        image_path,
        temperature_matrix,
        radiometry_data,
        image_metadata
    )


def save_report(report_rows, report_path):
    """Zapisuje raport całej konwersji do CSV."""

    fieldnames = [
        "filename",
        "status",
        "width",
        "height",
        "min_temp_c",
        "max_temp_c",
        "distance",
        "humidity",
        "emissivity",
        "reflection",
        "ambient_temp",
        "gps_latitude",
        "gps_longitude",
        "absolute_altitude",
        "relative_altitude",
        "gimbal_roll",
        "gimbal_yaw",
        "gimbal_pitch",
        "flight_roll",
        "flight_yaw",
        "flight_pitch",
        "utc_at_exposure",
        "camera_serial",
        "drone_serial",
        "error",
    ]

    with report_path.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(report_rows)


def main():
    base_dir = Path(__file__).resolve().parent.parent

    input_dir = base_dir / "data" / "input"
    output_dir = base_dir / "data" / "output"
    report_path = output_dir / "conversion_report.csv"

    dll_path = str(
        base_dir / "tools" / "libdirp.dll"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    image_paths = [
        path
        for path in input_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".jpg", ".jpeg"}
    ]

    if not image_paths:
        print("Brak plików JPG w data/input.")
        return

    print("Inicjalizacja silnika DJI SDK...")

    sdk = DJIThermalSDK(dll_path)

    report_rows = []

    success_count = 0
    error_count = 0

    for image_path in image_paths:
        try:
            row = convert_image(
                sdk,
                image_path,
                output_dir
            )

            report_rows.append(row)
            success_count += 1

        except Exception as exc:
            print(f"BŁĄD: {image_path.name}")
            print(str(exc))
            print("-" * 40)

            report_rows.append({
                "filename": image_path.name,
                "status": "ERROR",
                "error": str(exc),
            })

            error_count += 1

    save_report(
        report_rows,
        report_path
    )

    print("\nKONWERSJA ZAKOŃCZONA")
    print(f"Poprawnie: {success_count}")
    print(f"Błędy:     {error_count}")
    print(f"Razem:     {len(image_paths)}")
    print(f"Raport:    {report_path}")


if __name__ == "__main__":
    main()