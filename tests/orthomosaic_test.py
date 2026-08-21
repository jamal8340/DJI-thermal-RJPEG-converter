from pathlib import Path
import numpy as np
import tifffile


def main():
    """Inspect a two-band Float32 thermal orthomosaic exported from Metashape."""
    project_dir = Path(__file__).resolve().parent.parent
    ortho_path = project_dir / "data" / "output" / "orto.tif"

    if not ortho_path.exists():
        raise FileNotFoundError(
            f"Orthomosaic not found: {ortho_path}"
        )

    data = tifffile.imread(ortho_path)

    print("=" * 50)
    print("ORTHOMOSAIC CHECK")
    print("=" * 50)
    print(f"Shape: {data.shape}")
    print(f"Dtype: {data.dtype}")

    if data.ndim != 3 or data.shape[2] != 2:
        raise ValueError(
            f"Unexpected channel layout: {data.shape}"
        )

    temperature = data[:, :, 0]
    alpha = data[:, :, 1]

    valid_mask = (
        (alpha == 1)
        & np.isfinite(temperature)
    )
    valid_temperature = temperature[valid_mask]

    print()
    print("ALPHA / MASK")
    print("-" * 50)
    print(f"Valid pixels: {valid_mask.sum():,}")
    print(f"Total pixels: {valid_mask.size:,}")
    print(f"Coverage:     {valid_mask.mean() * 100:.2f}%")

    if valid_temperature.size == 0:
        raise ValueError(
            "No valid temperature pixels found."
        )

    print()
    print("TEMPERATURE - VALID AREA ONLY")
    print("-" * 50)
    print(f"Min:    {valid_temperature.min():.6f} °C")
    print(f"Max:    {valid_temperature.max():.6f} °C")
    print(f"Mean:   {valid_temperature.mean():.6f} °C")
    print(f"Median: {np.median(valid_temperature):.6f} °C")
    print(
        f"P01:    {np.percentile(valid_temperature, 1):.6f} °C"
    )
    print(
        f"P99:    {np.percentile(valid_temperature, 99):.6f} °C"
    )

    if data.dtype != np.float32:
        raise TypeError(
            f"Expected Float32 orthomosaic, got {data.dtype}"
        )

    print("\nPASS: orthomosaic is Float32.")


if __name__ == "__main__":
    main()
