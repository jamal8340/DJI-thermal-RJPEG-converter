import json
import numpy as np
import tifffile
from pathlib import Path

# Importujemy naszą nową klasę
from dji_sdk import DJIThermalSDK

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    input_dir = base_dir / "data" / "input"
    output_dir = base_dir / "data" / "output"
    
    # Ścieżka do biblioteki DLL
    dll_path = str(base_dir / "tools" / "libdirp.dll")

    print("Inicjalizacja silnika DJI SDK...")
    sdk = DJIThermalSDK(dll_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    for image_path in input_dir.glob("*.jpg"):
        print(f"Przetwarzam plik: {image_path.name}") 
        name = image_path.stem
        new_file_tif = output_dir / f"{name}.tif"

        # Krok 1: Odbieramy teraz DWA elementy z naszego zaktualizowanego SDK
        result = sdk.process_image_info(str(image_path))

        if result is not None:
            temperature_matrix, radiometry_data = result
            
            # Krok 2: Zamieniamy słownik na ładny tekst (JSON), żeby TIFF go zrozumiał
            metadata_str = json.dumps(radiometry_data, indent=2)

            print(f"Zapisuję do pliku: {new_file_tif.name}...")
            
            # Krok 3: Zapisujemy plik ze wstrzykniętymi metadanymi!
            tifffile.imwrite(
                str(new_file_tif), 
                temperature_matrix.astype(np.float32), 
                photometric="minisblack",
                metadata={'ImageDescription': metadata_str}
            )
            print(f"SUKCES!\n{'-'*40}")