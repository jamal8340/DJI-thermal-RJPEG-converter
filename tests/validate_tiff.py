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
    errors = []

    try:
        with tifffile.TiffFile(tiff_path) as tif:
            page = tif.pages[0]
            data = page.asarray()

            # --- Raster ---
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
                    "Raster zawiera NaN lub Inf"
                )

            # --- Standardowe tagi TIFF ---
            for tag_name in ["Make", "Model", "DateTime"]:
                if page.tags.get(tag_name) is None:
                    errors.append(
                        f"Brak standardowego tagu TIFF: {tag_name}"
                    )

            # --- ImageDescription ---
            description = page.description

            if not description:
                errors.append("Brak ImageDescription")
                return errors

            try:
                metadata = json.loads(description)
            except json.JSONDecodeError:
                errors.append(
                    "ImageDescription nie jest poprawnym JSON-em"
                )
                return errors

            # --- Informacje o temperaturze ---
            temperature = metadata.get("temperature", {})

            if temperature.get("unit") != "Celsius":
                errors.append(
                    "Brak lub błędna jednostka temperatury"
                )

            if temperature.get("data_type") != "float32":
                errors.append(
                    "Brak lub błędny data_type temperatury"
                )

            expected_width = temperature.get("width")
            expected_height = temperature.get("height")

            if expected_width is None or expected_height is None:
                errors.append(
                    "Brak wymiarów obrazu w metadanych"
                )
            else:
                expected_shape = (
                    int(expected_height),
                    int(expected_width)
                )

                if data.shape != expected_shape:
                    errors.append(
                        f"Niezgodny rozmiar rastra: "
                        f"{data.shape}, oczekiwano {expected_shape}"
                    )

            # --- Kontrola min/max ---
            metadata_min = temperature.get("min")
            metadata_max = temperature.get("max")

            if metadata_min is not None:
                if not np.isclose(
                    float(data.min()),
                    float(metadata_min),
                    atol=1e-5
                ):
                    errors.append(
                        "Minimalna temperatura nie zgadza się "
                        "z metadanymi"
                    )

            if metadata_max is not None:
                if not np.isclose(
                    float(data.max()),
                    float(metadata_max),
                    atol=1e-5
                ):
                    errors.append(
                        "Maksymalna temperatura nie zgadza się "
                        "z metadanymi"
                    )

            # --- Radiometria ---
            radiometry = metadata.get("radiometry", {})

            for field in REQUIRED_RADIOMETRY_FIELDS:
                if radiometry.get(field) is None:
                    errors.append(
                        f"Brak radiometrii: {field}"
                    )

            # --- Source metadata ---
            source_metadata = metadata.get(
                "source_metadata",
                {}
            )

            exif = source_metadata.get("exif", {})
            dji_xmp = source_metadata.get("dji_xmp", {})

            if not exif:
                errors.append("Brak EXIF")

            if not dji_xmp:
                errors.append("Brak DJI XMP")

            # --- Najważniejsze pola DJI XMP ---
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


def main():
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "data" / "output"

    tiff_files = sorted(
        output_dir.glob("*.tif")
    )

    if not tiff_files:
        print(
            "Brak plików TIFF w data/output."
        )
        return

    pass_count = 0
    fail_count = 0

    print(
        f"Walidacja {len(tiff_files)} plików TIFF...\n"
    )

    for tiff_path in tiff_files:
        errors = validate_tiff(tiff_path)

        if not errors:
            print(
                f"[PASS] {tiff_path.name}"
            )
            pass_count += 1

        else:
            print(
                f"[FAIL] {tiff_path.name}"
            )

            for error in errors:
                print(
                    f"       - {error}"
                )

            fail_count += 1

    print("\n" + "=" * 50)
    print("PODSUMOWANIE WALIDACJI")
    print(f"PASS:  {pass_count}")
    print(f"FAIL:  {fail_count}")
    print(f"RAZEM: {len(tiff_files)}")

    if fail_count == 0:
        print(
            "\nOK - wszystkie TIFF-y "
            "przeszły walidację."
        )
    else:
        print(
            "\nUWAGA - część TIFF-ów "
            "wymaga sprawdzenia."
        )


if __name__ == "__main__":
    main()