from pathlib import Path

import numpy as np
import tifffile


ORTHO_PATH = Path(
    r"D:\Converter\data\output\orto.tif"
)


def main():
    data = tifffile.imread(
        ORTHO_PATH
    )

    print("=" * 50)
    print("ORTHOMOSAIC CHECK")
    print("=" * 50)

    print(f"Shape: {data.shape}")
    print(f"Dtype: {data.dtype}")

    if data.ndim != 3 or data.shape[2] != 2:
        print(
            "Nieoczekiwany układ kanałów."
        )
        return

    temperature = data[:, :, 0]
    alpha = data[:, :, 1]

    valid_mask = (
        (alpha == 1)
        & np.isfinite(temperature)
    )

    valid_temperature = temperature[
        valid_mask
    ]

    print()
    print("ALPHA / MASK")
    print("-" * 50)

    print(
        f"Valid pixels: {valid_mask.sum():,}"
    )

    print(
        f"Total pixels: {valid_mask.size:,}"
    )

    print(
        f"Coverage: "
        f"{valid_mask.mean() * 100:.2f}%"
    )

    print()
    print("TEMPERATURE - VALID AREA ONLY")
    print("-" * 50)

    if valid_temperature.size == 0:
        print(
            "Brak poprawnych pikseli."
        )
        return

    print(
        f"Min:    {valid_temperature.min():.6f} °C"
    )

    print(
        f"Max:    {valid_temperature.max():.6f} °C"
    )

    print(
        f"Mean:   {valid_temperature.mean():.6f} °C"
    )

    print(
        f"Median: "
        f"{np.median(valid_temperature):.6f} °C"
    )

    print(
        f"P01:    "
        f"{np.percentile(valid_temperature, 1):.6f} °C"
    )

    print(
        f"P99:    "
        f"{np.percentile(valid_temperature, 99):.6f} °C"
    )

    print()

    if data.dtype == np.float32:
        print(
            "OK: ortomozaika jest Float32."
        )


if __name__ == "__main__":
    main()