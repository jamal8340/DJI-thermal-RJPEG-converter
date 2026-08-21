import re
from pathlib import Path
from PIL import ExifTags, Image


def make_json_safe(value):
    """Convert metadata values to JSON-serializable Python types."""
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def extract_exif(image_path):
    """Extract standard EXIF/TIFF metadata and GPS information from an image."""
    image_path = Path(image_path)
    exif_data = {}

    try:
        with Image.open(image_path) as image:
            exif = image.getexif()

            if not exif:
                return exif_data

            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(
                    tag_id,
                    str(tag_id),
                )
                exif_data[tag_name] = make_json_safe(value)

            # EXIF sub-IFD
            try:
                exif_ifd = exif.get_ifd(34665)

                for tag_id, value in exif_ifd.items():
                    tag_name = ExifTags.TAGS.get(
                        tag_id,
                        str(tag_id),
                    )
                    exif_data[tag_name] = make_json_safe(value)
            except Exception:
                pass

            # GPS sub-IFD
            try:
                gps_ifd = exif.get_ifd(34853)
                gps_data = {}

                for tag_id, value in gps_ifd.items():
                    tag_name = ExifTags.GPSTAGS.get(
                        tag_id,
                        str(tag_id),
                    )
                    gps_data[tag_name] = make_json_safe(value)

                if gps_data:
                    exif_data["GPSInfo"] = gps_data
            except Exception:
                pass

    except Exception as exc:
        print(f"Warning: failed to read EXIF metadata: {exc}")

    return exif_data


def extract_dji_xmp(image_path):
    """Extract DJI drone-dji XMP fields from the source image."""
    image_path = Path(image_path)
    xmp_data = {}

    try:
        raw_data = image_path.read_bytes().decode(
            "utf-8",
            errors="ignore",
        )
    except OSError as exc:
        print(f"Warning: failed to read XMP metadata: {exc}")
        return xmp_data

    attribute_pattern = re.compile(
        r'drone-dji:([A-Za-z0-9_]+)\s*=\s*"([^"]*)"'
    )

    for match in attribute_pattern.finditer(raw_data):
        key = match.group(1)
        value = match.group(2)
        xmp_data[key] = value

    element_pattern = re.compile(
        r"<drone-dji:([A-Za-z0-9_]+)>"
        r"(.*?)"
        r"</drone-dji:\1>",
        re.DOTALL,
    )

    for match in element_pattern.finditer(raw_data):
        key = match.group(1)
        value = match.group(2).strip()
        xmp_data[key] = value

    return xmp_data


def extract_raw_xmp(image_path):
    """Return the raw XMP packet from the source DJI JPEG as bytes, if present."""
    image_path = Path(image_path)

    try:
        raw = image_path.read_bytes()
    except OSError:
        return None

    packet_match = re.search(
        br"(<\?xpacket\s+begin=.*?"
        br"<x:xmpmeta.*?"
        br"</x:xmpmeta>.*?"
        br"<\?xpacket\s+end=.*?\?>)",
        raw,
        re.DOTALL,
    )

    if packet_match:
        return packet_match.group(1)

    xmp_match = re.search(
        br"(<x:xmpmeta.*?</x:xmpmeta>)",
        raw,
        re.DOTALL,
    )

    if xmp_match:
        return xmp_match.group(1)

    return None


def get_source_exif_for_tiff(
    image_path,
    image_description=None,
):
    """
    Return the source EXIF object prepared for TIFF output.

    ImageDescription can be replaced with converter metadata. Raw XMP is stored
    in TIFF tag 700 when available.
    """
    image_path = Path(image_path)

    with Image.open(image_path) as image:
        exif = image.getexif()

    if image_description is not None:
        exif[270] = image_description

    raw_xmp = extract_raw_xmp(image_path)

    if raw_xmp:
        exif[700] = raw_xmp

    return exif


def extract_metadata(image_path):
    """Return the metadata structure used by the converter."""
    image_path = Path(image_path)

    return {
        "source_file": image_path.name,
        "exif": extract_exif(image_path),
        "dji_xmp": extract_dji_xmp(image_path),
    }
