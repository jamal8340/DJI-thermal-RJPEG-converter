import csv
import json
from pathlib import Path

import numpy as np
import tifffile

from dji_sdk import DJIThermalSDK
from metadata import extract_metadata


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent

    input_dir = base_dir / "data" / "input"
    output_dir = base_dir / "data" / "output"
    report_path = output_dir / "conversion_report.csv"

    dll_path = str(base_dir / "tools" / "libdirp.dll")

    print("Inicjalizacja silnika DJI SDK...")

    sdk = DJIThermalSDK(dll_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = [
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"}
    ]

    report_rows = []

    for image_path in image_paths:
        print(f"Przetwarzam plik: {image_path.name}")

        name = image_path.stem
        new_file_tif = output_dir / f"{name}.tif"

        try:
            result = sdk.process_image_info(str(image_path))

            if result is None:
                raise RuntimeError("DJI SDK nie zwrócił danych.")

            temperature_matrix, radiometry_data = result

            # EXIF + DJI XMP
            image_metadata = extract_metadata(image_path)

            exif_data = image_metadata.get("exif", {})
            dji_xmp = image_metadata.get("dji_xmp", {})

            # Pełny zestaw metadanych zapisany w TIFF
            full_metadata = {
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

            metadata_str = json.dumps(
                full_metadata,
                indent=2,
                ensure_ascii=False
            )

            # Standardowe tagi TIFF
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

            print(f"Zapisuję do pliku: {new_file_tif.name}...")

            tifffile.imwrite(
                str(new_file_tif),
                temperature_matrix.astype(np.float32),
                photometric="minisblack",
                description=metadata_str,
                metadata=None,
                extratags=extra_tags
            )

            # Dane do raportu CSV
            report_rows.append({
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
            })

            print(f"SUKCES!\n{'-' * 40}")

        except Exception as exc:
            print(f"BŁĄD: {image_path.name}")
            print(str(exc))
            print("-" * 40)

            report_rows.append({
                "filename": image_path.name,
                "status": "ERROR",
                "error": str(exc),
            })

    # Raport całej konwersji
    if report_rows:
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

        print(f"\nRaport zapisany: {report_path}")