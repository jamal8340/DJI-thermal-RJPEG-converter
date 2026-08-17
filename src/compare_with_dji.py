import numpy as np
import tifffile
from pathlib import Path


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent

    tiff_path = (
        base_dir
        / "data"
        / "output"
        / "DJI_20230920123005_0001_T.tif"
    )

    raw_path = (
        base_dir
        / "data"
        / "reference"
        / "official.raw"
    )

    # Nasz TIFF
    our_data = tifffile.imread(tiff_path).astype(np.float32)

    # Oficjalny wynik DJI - Float32 RAW
    dji_data = np.fromfile(raw_path, dtype=np.float32)

    if dji_data.size != our_data.size:
        print("BŁĄD: Liczba pikseli się nie zgadza.")
        print(f"Nasz TIFF: {our_data.size}")
        print(f"DJI RAW:    {dji_data.size}")
        raise SystemExit

    dji_data = dji_data.reshape(our_data.shape)

    difference = np.abs(our_data - dji_data)

    print("Porównanie z oficjalnym DJI:")
    print(f"Rozmiar: {our_data.shape}")
    print(f"Max różnica:  {difference.max():.8f} °C")
    print(f"Mean różnica: {difference.mean():.8f} °C")
    print(f"RMSE:         {np.sqrt(np.mean(difference ** 2)):.8f} °C")

    if np.allclose(our_data, dji_data, atol=1e-5):
        print("\nOK - wyniki są zgodne z DJI.")
    else:
        print("\nUWAGA - wyniki różnią się od oficjalnego DJI.")