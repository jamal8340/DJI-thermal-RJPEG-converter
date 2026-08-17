import json
import tifffile
from pathlib import Path


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "data" / "output"

    tiff_files = list(output_dir.glob("*.tif"))

    if not tiff_files:
        print("Brak plików TIFF w data/output.")
        raise SystemExit

    for tiff_path in tiff_files:
        print(f"\nSprawdzam: {tiff_path.name}")

        with tifffile.TiffFile(tiff_path) as tif:
            page = tif.pages[0]
            data = page.asarray()

            # --- Standardowe tagi TIFF ---
            print("\nStandardowe tagi TIFF:")

            for tag_name in ["Make", "Model", "DateTime"]:
                tag = page.tags.get(tag_name)

                if tag:
                    print(f"{tag_name}: {tag.value}")
                else:
                    print(f"{tag_name}: BRAK")

            # --- Dane rastra ---
            print("\nRaster temperatury:")
            print(f"Rozmiar: {data.shape}")
            print(f"Typ danych: {data.dtype}")
            print(f"Min temperatura: {data.min():.2f} °C")
            print(f"Max temperatura: {data.max():.2f} °C")

            # --- Metadane JSON zapisane w ImageDescription ---
            description = page.description

            if not description:
                print("\nBŁĄD: Brak ImageDescription.")
                continue

            try:
                metadata = json.loads(description)

            except json.JSONDecodeError:
                print("\nBŁĄD: ImageDescription nie jest poprawnym JSON-em.")
                continue

            # --- Radiometria ---
            radiometry = metadata.get("radiometry", {})

            print("\nRadiometria:")
            print(json.dumps(
                radiometry,
                indent=2,
                ensure_ascii=False
            ))

            # --- EXIF ---
            source_metadata = metadata.get("source_metadata", {})
            exif = source_metadata.get("exif", {})

            print("\nEXIF:")
            print(json.dumps(
                exif,
                indent=2,
                ensure_ascii=False
            ))

            # --- DJI XMP ---
            dji_xmp = source_metadata.get("dji_xmp", {})

            print("\nDJI XMP:")
            print(json.dumps(
                dji_xmp,
                indent=2,
                ensure_ascii=False
            ))

            # --- Skrócona kontrola najważniejszych danych ---
            print("\nNajważniejsze dane:")

            print(f"GPS Latitude: {dji_xmp.get('GpsLatitude', 'BRAK')}")
            print(f"GPS Longitude: {dji_xmp.get('GpsLongitude', 'BRAK')}")
            print(f"Absolute Altitude: {dji_xmp.get('AbsoluteAltitude', 'BRAK')}")
            print(f"Relative Altitude: {dji_xmp.get('RelativeAltitude', 'BRAK')}")

            print(f"Gimbal Roll: {dji_xmp.get('GimbalRollDegree', 'BRAK')}")
            print(f"Gimbal Yaw: {dji_xmp.get('GimbalYawDegree', 'BRAK')}")
            print(f"Gimbal Pitch: {dji_xmp.get('GimbalPitchDegree', 'BRAK')}")

            print(f"Flight Roll: {dji_xmp.get('FlightRollDegree', 'BRAK')}")
            print(f"Flight Yaw: {dji_xmp.get('FlightYawDegree', 'BRAK')}")
            print(f"Flight Pitch: {dji_xmp.get('FlightPitchDegree', 'BRAK')}")

            print(f"UTC At Exposure: {dji_xmp.get('UTCAtExposure', 'BRAK')}")
            print(f"Camera Serial: {dji_xmp.get('CameraSerialNumber', 'BRAK')}")
            print(f"Drone Serial: {dji_xmp.get('DroneSerialNumber', 'BRAK')}")

            print("\nWalidacja zakończona.")
            print("-" * 50)