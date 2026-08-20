from pathlib import Path

import numpy as np
import tifffile


def main():
    """Compare a converted TIFF against a local DJI Float32 RAW reference."""
    project_dir = Path(__file__).resolve().parent.parent

    tiff_path = (
        project_dir
        / "data"
        / "output"
        / "DJI_20230920123005_0001_T.tif"
    )
    raw_path = (
        project_dir
        / "data"
        / "reference"
        / "official.raw"
    )

    if not tiff_path.exists():
        raise FileNotFoundError(f"Converted TIFF not found: {tiff_path}")

    if not raw_path.exists():
        raise FileNotFoundError(f"Reference RAW not found: {raw_path}")

    converted = tifffile.imread(tiff_path).astype(
        np.float32,
        copy=False,
    )
    reference = np.fromfile(
        raw_path,
        dtype=np.float32,
    )

    if reference.size != converted.size:
        raise ValueError(
            "Pixel count mismatch: "
            f"TIFF={converted.size}, RAW={reference.size}"
        )

    reference = reference.reshape(converted.shape)
    difference = np.abs(converted - reference)

    print("DJI reference comparison")
    print("=" * 50)
    print(f"Shape:        {converted.shape}")
    print(f"Max diff:     {difference.max():.8f} °C")
    print(f"Mean diff:    {difference.mean():.8f} °C")
    print(
        "RMSE:         "
        f"{np.sqrt(np.mean(difference ** 2)):.8f} °C"
    )

    if np.allclose(converted, reference, atol=1e-5):
        print("\nPASS: converted raster matches the local reference.")
    else:
        print("\nFAIL: converted raster differs from the local reference.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()