from pathlib import Path
from dji_sdk import DJIThermalSDK, get_default_dll_path


def main():
    """Print radiometric parameters stored in a development test R-JPEG."""
    base_dir = Path(__file__).resolve().parent.parent
    image_path = (
        base_dir
        / "data"
        / "input"
        / "DJI_20230920123005_0001_T.JPG"
    )

    if not image_path.exists():
        raise FileNotFoundError(f"Test image not found: {image_path}")

    sdk = DJIThermalSDK(get_default_dll_path())
    _, radiometry = sdk.process_image_info(image_path)

    print("\n=== DJI RADIOMETRY ===")
    print("=" * 80)
    print(f"Distance: {radiometry['distance']:.3f} m")
    print(f"Humidity: {radiometry['humidity']:.3f} %")
    print(f"Emissivity: {radiometry['emissivity']:.3f}")
    print(
        "Reflected temperature: "
        f"{radiometry['reflection']:.3f} °C"
    )
    print(
        "Ambient temperature: "
        f"{radiometry['ambient_temp']:.3f} °C"
    )


if __name__ == "__main__":
    main()