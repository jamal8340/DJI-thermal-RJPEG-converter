import subprocess
import numpy as np
import tifffile
from pathlib import Path

def extract_raw_temperatures(image_path: str, dji_tool_path: str, output_raw_path: str):
    """
    Krok 1: Wyciągnięcie pliku RAW ze zdjęcia JPEG przy użyciu DJI SDK.
    """
    if not Path(image_path).exists():
        print(f"BŁĄD: Nie znaleziono zdjęcia: {image_path}")
        return False
        
    Path(output_raw_path).parent.mkdir(parents=True, exist_ok=True)

    command = [
    dji_tool_path,
    "-s", image_path,
    "-a", "measure",
    "-o", output_raw_path,
    "--measurefmt", "float32"
    ]
    
    print("Wyciągam dane termalne z pliku RJPEG...")
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0:
        return True
    else:
        print("\nBŁĄD NARZĘDZIA DJI:")
        print(result.stdout.strip())
        return False

def raw_to_tiff(raw_path: str, tiff_path: str, width: int = 640, height: int = 512):
    """
    Krok 2: Zamiana wygenerowanego pliku RAW na TIFF (Twój kod).
    """
    print(f"Konwertuję plik RAW na TIFF ({width}x{height})...")
    
    temperature = np.fromfile(raw_path, dtype="<f4")
    expected_pixels = width * height

    if temperature.size != expected_pixels:
        print(f"BŁĄD: Zły rozmiar danych. Oczekiwano {expected_pixels}, otrzymano {temperature.size}.")
        print("Prawdopodobnie rozdzielczość zdjęcia jest inna niż 640x512.")
        return False

    temperature = temperature.reshape((height, width))

    print(f"Min: {temperature.min():.2f} °C | Max: {temperature.max():.2f} °C | Średnia: {temperature.mean():.2f} °C")

    tifffile.imwrite(tiff_path, temperature.astype(np.float32), photometric="minisblack")
    print(f"SUKCES! Gotowy plik: {tiff_path}")
    return True

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    
    input_image = str(base_dir / "data" / "input" / "DJI_20230920123005_0001_T.JPG")
    temp_raw = str(base_dir / "data" / "output" / "temp.raw")
    output_tiff = str(base_dir / "data" / "output" / "wynik.tif")
    dji_tool = str(base_dir / "tools" / "dji_irp.exe")
    
    if extract_raw_temperatures(input_image, dji_tool, temp_raw):
        raw_to_tiff(temp_raw, output_tiff)