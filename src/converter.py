import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from dji_sdk import (
    DJIThermalSDK,
    DJIError,
    InvalidRJPEGError,
    get_default_dll_path,
)

from metadata import (
    extract_metadata,
    get_source_exif_for_tiff,
)


REPORT_FIELDS = [
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


def build_full_metadata(
    temperature_matrix,
    radiometry_data,
    image_metadata
):
    return {
        "temperature": {
            "unit": "Celsius",
            "data_type": "float32",
            "width": int(
                temperature_matrix.shape[1]
            ),
            "height": int(
                temperature_matrix.shape[0]
            ),
            "min": float(
                temperature_matrix.min()
            ),
            "max": float(
                temperature_matrix.max()
            ),
        },
        "radiometry": radiometry_data,
        "source_metadata": image_metadata,
    }


def build_report_row(
    image_path,
    temperature_matrix,
    radiometry_data,
    image_metadata
):
    dji_xmp = image_metadata.get(
        "dji_xmp",
        {}
    )

    return {
        "filename": image_path.name,
        "status": "OK",

        "width": int(
            temperature_matrix.shape[1]
        ),

        "height": int(
            temperature_matrix.shape[0]
        ),

        "min_temp_c": float(
            temperature_matrix.min()
        ),

        "max_temp_c": float(
            temperature_matrix.max()
        ),

        "distance": radiometry_data.get(
            "distance"
        ),

        "humidity": radiometry_data.get(
            "humidity"
        ),

        "emissivity": radiometry_data.get(
            "emissivity"
        ),

        "reflection": radiometry_data.get(
            "reflection"
        ),

        "ambient_temp": radiometry_data.get(
            "ambient_temp"
        ),

        "gps_latitude": dji_xmp.get(
            "GpsLatitude"
        ),

        "gps_longitude": dji_xmp.get(
            "GpsLongitude"
        ),

        "absolute_altitude": dji_xmp.get(
            "AbsoluteAltitude"
        ),

        "relative_altitude": dji_xmp.get(
            "RelativeAltitude"
        ),

        "gimbal_roll": dji_xmp.get(
            "GimbalRollDegree"
        ),

        "gimbal_yaw": dji_xmp.get(
            "GimbalYawDegree"
        ),

        "gimbal_pitch": dji_xmp.get(
            "GimbalPitchDegree"
        ),

        "flight_roll": dji_xmp.get(
            "FlightRollDegree"
        ),

        "flight_yaw": dji_xmp.get(
            "FlightYawDegree"
        ),

        "flight_pitch": dji_xmp.get(
            "FlightPitchDegree"
        ),

        "utc_at_exposure": dji_xmp.get(
            "UTCAtExposure"
        ),

        "camera_serial": dji_xmp.get(
            "CameraSerialNumber"
        ),

        "drone_serial": dji_xmp.get(
            "DroneSerialNumber"
        ),

        "error": "",
    }


def save_temperature_tiff(
    output_path,
    temperature_matrix,
    source_image,
    metadata_str
):
    """
    Zapisuje:
    - jednopasmowy Float32 TIFF
    - temperaturę w °C
    - oryginalny EXIF
    - GPS IFD
    - DJI XMP
    - nasz JSON w ImageDescription
    """

    output_path = Path(
        output_path
    )

    temperature_matrix = (
        temperature_matrix
        .astype(
            np.float32
        )
    )

    exif = get_source_exif_for_tiff(
        source_image,
        image_description=metadata_str
    )

    image = Image.fromarray(
        temperature_matrix,
        mode="F"
    )

    image.save(
        output_path,
        format="TIFF",
        exif=exif.tobytes()
    )


def convert_image(
    sdk,
    image_path,
    output_dir
):
    image_path = Path(
        image_path
    )

    output_dir = Path(
        output_dir
    )

    print(
        f"Przetwarzam plik: "
        f"{image_path.name}"
    )

    output_path = (
        output_dir
        / f"{image_path.stem}.tif"
    )

    result = sdk.process_image_info(
        str(image_path)
    )

    if result is None:
        raise DJIError(
            "DJI SDK nie zwrócił danych."
        )

    (
        temperature_matrix,
        radiometry_data
    ) = result

    image_metadata = extract_metadata(
        image_path
    )

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

    print(
        f"Zapisuję TIFF: "
        f"{output_path.name}..."
    )

    save_temperature_tiff(
        output_path=output_path,
        temperature_matrix=temperature_matrix,
        source_image=image_path,
        metadata_str=metadata_str
    )

    print("SUKCES!")
    print("-" * 40)

    report_row = build_report_row(
        image_path,
        temperature_matrix,
        radiometry_data,
        image_metadata
    )

    return (
        report_row,
        output_path
    )


def save_report(
    report_rows,
    report_path
):
    with Path(report_path).open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=REPORT_FIELDS
        )

        writer.writeheader()

        writer.writerows(
            report_rows
        )


def create_sdk(
    dll_path=None
):
    """
    Tworzy instancję DJI Thermal SDK.

    Jeśli dll_path:
    - nie został podany -> używa domyślnej ścieżki z dji_sdk.py
    - istnieje -> używa podanej ścieżki
    - nie istnieje -> próbuje automatycznej ścieżki

    Dzięki temu działa zarówno:
    - normalny Python
    - PyInstaller --onedir
    """

    if dll_path:
        candidate = Path(
            dll_path
        )

        if candidate.exists():
            return DJIThermalSDK(
                candidate
            )

        print(
            "Podana ścieżka DJI SDK nie istnieje:"
        )

        print(
            candidate
        )

        print(
            "Próba użycia automatycznej ścieżki..."
        )

    default_dll = get_default_dll_path()

    print(
        f"DJI SDK: {default_dll}"
    )

    return DJIThermalSDK()


def convert_images(
    image_paths,
    output_dir,
    dll_path=None,
    progress_callback=None,
    existing_policy="skip"
):
    output_dir = Path(
        output_dir
    )

    if existing_policy not in {
        "skip",
        "overwrite",
    }:
        raise ValueError(
            "existing_policy musi mieć "
            "wartość 'skip' albo 'overwrite'."
        )

    image_paths = [
        Path(path)
        for path in image_paths
        if Path(path).is_file()
        and Path(path).suffix.lower()
        in {
            ".jpg",
            ".jpeg",
        }
    ]

    if not image_paths:
        raise ValueError(
            "Nie wybrano żadnych "
            "plików JPG/JPEG."
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path = (
        output_dir
        / "conversion_report.csv"
    )

    print(
        "Inicjalizacja silnika DJI SDK..."
    )

    sdk = create_sdk(
        dll_path
    )

    report_rows = []
    output_files = []

    success_count = 0
    error_count = 0
    skipped_count = 0

    total = len(
        image_paths
    )

    for index, image_path in enumerate(
        image_paths,
        start=1
    ):
        output_path = (
            output_dir
            / f"{image_path.stem}.tif"
        )

        if (
            output_path.exists()
            and existing_policy == "skip"
        ):
            print(
                f"POMINIĘTO: "
                f"{image_path.name}"
            )

            report_rows.append({
                "filename": image_path.name,
                "status": "SKIPPED",
                "error": (
                    "Output TIFF already exists"
                ),
            })

            output_files.append(
                output_path
            )

            skipped_count += 1

        else:
            try:
                (
                    row,
                    created_file
                ) = convert_image(
                    sdk,
                    image_path,
                    output_dir
                )

                report_rows.append(
                    row
                )

                output_files.append(
                    created_file
                )

                success_count += 1

            except InvalidRJPEGError as exc:
                print(
                    f"BŁĄD R-JPEG: "
                    f"{image_path.name}"
                )

                print(
                    str(exc)
                )

                print(
                    "-" * 40
                )

                report_rows.append({
                    "filename": image_path.name,
                    "status": "ERROR",
                    "error": (
                        f"INVALID_RJPEG: {exc}"
                    ),
                })

                error_count += 1

            except DJIError as exc:
                print(
                    f"BŁĄD DJI SDK: "
                    f"{image_path.name}"
                )

                print(
                    str(exc)
                )

                print(
                    "-" * 40
                )

                report_rows.append({
                    "filename": image_path.name,
                    "status": "ERROR",
                    "error": (
                        f"DJI_SDK_ERROR: {exc}"
                    ),
                })

                error_count += 1

            except Exception as exc:
                print(
                    f"BŁĄD: "
                    f"{image_path.name}"
                )

                print(
                    str(exc)
                )

                print(
                    "-" * 40
                )

                report_rows.append({
                    "filename": image_path.name,
                    "status": "ERROR",
                    "error": (
                        f"UNEXPECTED_ERROR: {exc}"
                    ),
                })

                error_count += 1

        if progress_callback:
            progress_callback(
                index,
                total,
                success_count,
                error_count,
                skipped_count
            )

    save_report(
        report_rows,
        report_path
    )

    print(
        "\nKONWERSJA ZAKOŃCZONA"
    )

    print(
        f"Poprawnie: {success_count}"
    )

    print(
        f"Pominięto: {skipped_count}"
    )

    print(
        f"Błędy:     {error_count}"
    )

    print(
        f"Razem:     {total}"
    )

    print(
        f"Raport:    {report_path}"
    )

    return {
        "success": success_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total": total,
        "report": report_path,
        "output_files": output_files,
    }


def convert_folder(
    input_dir,
    output_dir,
    dll_path=None,
    progress_callback=None,
    existing_policy="skip"
):
    input_dir = Path(
        input_dir
    )

    if not input_dir.exists():
        raise FileNotFoundError(
            f"Folder wejściowy "
            f"nie istnieje: "
            f"{input_dir}"
        )

    if not input_dir.is_dir():
        raise NotADirectoryError(
            f"Ścieżka wejściowa "
            f"nie jest folderem: "
            f"{input_dir}"
        )

    image_paths = sorted([
        path
        for path in input_dir.iterdir()
        if path.is_file()
        and path.suffix.lower()
        in {
            ".jpg",
            ".jpeg",
        }
    ])

    if not image_paths:
        raise ValueError(
            "Brak plików JPG/JPEG "
            "w folderze wejściowym."
        )

    return convert_images(
        image_paths=image_paths,
        output_dir=output_dir,
        dll_path=dll_path,
        progress_callback=progress_callback,
        existing_policy=existing_policy
    )


def parse_arguments():
    base_dir = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    parser = argparse.ArgumentParser(
        description=(
            "Convert DJI thermal R-JPEG "
            "images to Float32 TIFF."
        )
    )

    parser.add_argument(
        "input",
        nargs="?",
        default=str(
            base_dir
            / "data"
            / "input"
        )
    )

    parser.add_argument(
        "output",
        nargs="?",
        default=str(
            base_dir
            / "data"
            / "output"
        )
    )

    parser.add_argument(
        "--dll",
        default=None,
        help=(
            "Opcjonalna ścieżka do libdirp.dll. "
            "Jeśli pominięta, ścieżka zostanie "
            "wykryta automatycznie."
        )
    )

    parser.add_argument(
        "--existing",
        choices=[
            "skip",
            "overwrite",
        ],
        default="skip"
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    convert_folder(
        input_dir=args.input,
        output_dir=args.output,
        dll_path=args.dll,
        existing_policy=args.existing
    )


if __name__ == "__main__":
    main()