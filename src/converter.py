import argparse
import csv
import json
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

from dji_sdk import (
    DJIThermalSDK,
    DJIError,
    InvalidRJPEGError,
    get_default_dll_path,
)
from metadata import (
    extract_metadata,
    extract_raw_xmp,
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
    image_metadata,
):
    """Build the metadata structure stored in TIFF ImageDescription."""
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


def build_report_row(
    image_path,
    temperature_matrix,
    radiometry_data,
    image_metadata,
):
    """Build one conversion report row for a successfully converted image."""
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


def get_basic_exif_tags(source_image):
    """
    Return basic TIFF/EXIF tags that can be safely written as top-level TIFF tags.

    GPS and DJI orientation metadata are preserved through the raw XMP packet
    stored in TIFF tag 700.
    """
    source_image = Path(source_image)
    tags = []

    with Image.open(source_image) as image:
        exif = image.getexif()

        for tag_id in (
            271,  # Make
            272,  # Model
            306,  # DateTime
        ):
            value = exif.get(tag_id)

            if not value:
                continue

            value = str(value)

            tags.append(
                (
                    tag_id,
                    "s",
                    len(value) + 1,
                    value,
                    True,
                )
            )

    return tags


def save_temperature_tiff(
    output_path,
    temperature_matrix,
    source_image,
    metadata_str,
):
    """
    Write a single-band Float32 temperature TIFF.

    The output uses lossless Deflate compression, stores converter metadata in
    ImageDescription, preserves basic TIFF/EXIF tags, and embeds the source DJI
    XMP packet in TIFF tag 700 when available.
    """
    output_path = Path(output_path)
    source_image = Path(source_image)

    temperature_matrix = temperature_matrix.astype(
        np.float32,
        copy=False,
    )

    extratags = get_basic_exif_tags(source_image)
    raw_xmp = extract_raw_xmp(source_image)

    if raw_xmp:
        xmp_bytes = bytes(raw_xmp)
        extratags.append(
            (
                700,
                "B",
                len(xmp_bytes),
                xmp_bytes,
                True,
            )
        )

    tifffile.imwrite(
        output_path,
        temperature_matrix,
        dtype=np.float32,
        photometric="minisblack",
        compression="zlib",
        compressionargs={"level": 6},
        metadata=None,
        description=metadata_str,
        extratags=extratags,
    )


def convert_image(
    sdk,
    image_path,
    output_dir,
    measurement_overrides=None,
):
    """Convert one DJI radiometric R-JPEG to a Float32 temperature TIFF."""
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_path = output_dir / f"{image_path.stem}.tif"

    temperature_matrix, radiometry_data = sdk.process_image_info(
        str(image_path),
        measurement_overrides=measurement_overrides,
    )

    image_metadata = extract_metadata(image_path)

    full_metadata = build_full_metadata(
        temperature_matrix,
        radiometry_data,
        image_metadata,
    )

    metadata_str = json.dumps(
        full_metadata,
        indent=2,
        ensure_ascii=False,
    )

    save_temperature_tiff(
        output_path=output_path,
        temperature_matrix=temperature_matrix,
        source_image=image_path,
        metadata_str=metadata_str,
    )

    report_row = build_report_row(
        image_path,
        temperature_matrix,
        radiometry_data,
        image_metadata,
    )

    return report_row, output_path


def save_report(report_rows, report_path):
    """Write the internal CSV conversion report."""
    with Path(report_path).open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=REPORT_FIELDS,
        )
        writer.writeheader()
        writer.writerows(report_rows)


def create_sdk(dll_path=None):
    """Create a DJI Thermal SDK instance using an explicit or automatic DLL path."""
    if dll_path:
        candidate = Path(dll_path)

        if candidate.exists():
            return DJIThermalSDK(candidate)

        print(
            f"Warning: DJI SDK path does not exist: {candidate}. "
            "Falling back to automatic detection."
        )

    default_dll = get_default_dll_path()
    return DJIThermalSDK(default_dll)


def convert_images(
    image_paths,
    output_dir,
    dll_path=None,
    progress_callback=None,
    existing_policy="skip",
    measurement_overrides=None,
):
    """
    Convert multiple DJI R-JPEG files and return batch conversion statistics.

    Existing output TIFF files can be skipped or overwritten. Errors are handled
    per image so one invalid source file does not stop the entire batch.
    """
    output_dir = Path(output_dir)

    if existing_policy not in {"skip", "overwrite"}:
        raise ValueError(
            "existing_policy must be 'skip' or 'overwrite'."
        )

    image_paths = [
        Path(path)
        for path in image_paths
        if Path(path).is_file()
        and Path(path).suffix.lower() in {".jpg", ".jpeg"}
    ]

    if not image_paths:
        raise ValueError(
            "No JPG/JPEG files were selected."
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = output_dir / "conversion_report.csv"
    sdk = create_sdk(dll_path)

    report_rows = []
    output_files = []

    success_count = 0
    error_count = 0
    skipped_count = 0
    total = len(image_paths)

    for index, image_path in enumerate(
        image_paths,
        start=1,
    ):
        output_path = output_dir / f"{image_path.stem}.tif"

        if (
            output_path.exists()
            and existing_policy == "skip"
        ):
            report_rows.append(
                {
                    "filename": image_path.name,
                    "status": "SKIPPED",
                    "error": "Output TIFF already exists",
                }
            )
            output_files.append(output_path)
            skipped_count += 1

        else:
            try:
                row, created_file = convert_image(
                    sdk,
                    image_path,
                    output_dir,
                    measurement_overrides=measurement_overrides,
                )

                report_rows.append(row)
                output_files.append(created_file)
                success_count += 1

            except InvalidRJPEGError as exc:
                report_rows.append(
                    {
                        "filename": image_path.name,
                        "status": "ERROR",
                        "error": f"INVALID_RJPEG: {exc}",
                    }
                )
                error_count += 1

            except DJIError as exc:
                report_rows.append(
                    {
                        "filename": image_path.name,
                        "status": "ERROR",
                        "error": f"DJI_SDK_ERROR: {exc}",
                    }
                )
                error_count += 1

            except Exception as exc:
                report_rows.append(
                    {
                        "filename": image_path.name,
                        "status": "ERROR",
                        "error": f"UNEXPECTED_ERROR: {exc}",
                    }
                )
                error_count += 1

        if progress_callback:
            progress_callback(
                index,
                total,
                success_count,
                error_count,
                skipped_count,
            )

    save_report(
        report_rows,
        report_path,
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
    existing_policy="skip",
    measurement_overrides=None,
):
    """Convert all JPG/JPEG files directly contained in an input directory."""
    input_dir = Path(input_dir)

    if not input_dir.exists():
        raise FileNotFoundError(
            f"Input folder does not exist: {input_dir}"
        )

    if not input_dir.is_dir():
        raise NotADirectoryError(
            f"Input path is not a directory: {input_dir}"
        )

    image_paths = sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".jpg", ".jpeg"}
    )

    if not image_paths:
        raise ValueError(
            "No JPG/JPEG files found in the input folder."
        )

    return convert_images(
        image_paths=image_paths,
        output_dir=output_dir,
        dll_path=dll_path,
        progress_callback=progress_callback,
        existing_policy=existing_policy,
        measurement_overrides=measurement_overrides,
    )


def parse_arguments():
    """Parse command-line arguments for batch conversion."""
    base_dir = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description=(
            "Convert DJI thermal R-JPEG images to Float32 TIFF."
        )
    )

    parser.add_argument(
        "input",
        nargs="?",
        default=str(base_dir / "data" / "input"),
    )

    parser.add_argument(
        "output",
        nargs="?",
        default=str(base_dir / "data" / "output"),
    )

    parser.add_argument(
        "--dll",
        default=None,
        help=(
            "Optional path to libdirp.dll. "
            "If omitted, the path is detected automatically."
        ),
    )

    parser.add_argument(
        "--existing",
        choices=["skip", "overwrite"],
        default="skip",
    )

    parser.add_argument(
        "--distance",
        type=float,
        default=None,
        help="Override measurement distance in meters.",
    )

    parser.add_argument(
        "--humidity",
        type=float,
        default=None,
        help="Override relative humidity.",
    )

    parser.add_argument(
        "--emissivity",
        type=float,
        default=None,
        help="Override surface emissivity.",
    )

    parser.add_argument(
        "--reflection",
        type=float,
        default=None,
        help="Override reflected temperature in Celsius.",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    measurement_overrides = {
        "distance": args.distance,
        "humidity": args.humidity,
        "emissivity": args.emissivity,
        "reflection": args.reflection,
    }

    measurement_overrides = {
        key: value
        for key, value in measurement_overrides.items()
        if value is not None
    }

    if not measurement_overrides:
        measurement_overrides = None

    convert_folder(
        input_dir=args.input,
        output_dir=args.output,
        dll_path=args.dll,
        existing_policy=args.existing,
        measurement_overrides=measurement_overrides,
    )


if __name__ == "__main__":
    main()