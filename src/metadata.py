import re
from pathlib import Path
from PIL import Image, ExifTags


def _to_serializable(value):
    """Konwertuje wartości EXIF do typów, które można zapisać jako JSON."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, (list, tuple)):
        return [_to_serializable(v) for v in value]

    if isinstance(value, dict):
        return {str(k): _to_serializable(v) for k, v in value.items()}

    try:
        # Obsługa IFDRational itp.
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            if value.denominator != 0:
                return float(value)

        if isinstance(value, (int, float, str, bool)) or value is None:
            return value

        return str(value)

    except Exception:
        return str(value)


def _extract_exif(image_path: Path) -> dict:
    """Odczytuje standardowe metadane EXIF z DJI JPG."""
    result = {}

    with Image.open(image_path) as image:
        exif = image.getexif()

        if not exif:
            return result

        # Główne tagi EXIF
        for tag_id, value in exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))

            # GPS i ExifOffset są osobnymi IFD, więc obsłużymy je niżej
            if tag_name in {"GPSInfo", "ExifOffset"}:
                continue

            result[tag_name] = _to_serializable(value)

        # EXIF IFD — np. DateTimeOriginal, ExposureTime itd.
        try:
            exif_ifd = exif.get_ifd(0x8769)

            for tag_id, value in exif_ifd.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                result[tag_name] = _to_serializable(value)

        except Exception:
            pass

        # GPS IFD
        try:
            gps_ifd = exif.get_ifd(0x8825)

            if gps_ifd:
                gps_data = {}

                for tag_id, value in gps_ifd.items():
                    tag_name = ExifTags.GPSTAGS.get(tag_id, str(tag_id))
                    gps_data[tag_name] = _to_serializable(value)

                result["GPS"] = gps_data

        except Exception:
            pass

    return result


def _extract_dji_xmp(image_path: Path) -> dict:
    """
    Wydobywa pola drone-dji:* zapisane w XMP.
    DJI przechowuje tam m.in. wysokości i orientację gimbala/drona.
    """
    raw = image_path.read_bytes().decode("utf-8", errors="ignore")

    result = {}

    # Format:
    # drone-dji:GimbalYawDegree="+10.20"
    attribute_pattern = re.compile(
        r'drone-dji:([A-Za-z0-9_]+)\s*=\s*"([^"]*)"'
    )

    for key, value in attribute_pattern.findall(raw):
        result[key] = value

    # Alternatywny format:
    # <drone-dji:GimbalYawDegree>...</drone-dji:GimbalYawDegree>
    element_pattern = re.compile(
        r"<drone-dji:([A-Za-z0-9_]+)[^>]*>(.*?)</drone-dji:\1>",
        re.DOTALL,
    )

    for key, value in element_pattern.findall(raw):
        result[key] = value.strip()

    return result


def extract_metadata(image_path) -> dict:
    """
    Zwraca metadane potrzebne do zachowania wraz z rastrem temperatur.
    """
    image_path = Path(image_path)

    return {
        "source_file": image_path.name,
        "exif": _extract_exif(image_path),
        "dji_xmp": _extract_dji_xmp(image_path),
    }