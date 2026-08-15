import ctypes
import os
import numpy as np  
from pathlib import Path

class MeasurementParams(ctypes.Structure):
    _fields_ = [
        ("distance", ctypes.c_float),
        ("humidity", ctypes.c_float),
        ("emissivity", ctypes.c_float),
        ("reflection", ctypes.c_float),
        ("ambient_temp", ctypes.c_float),
    ]

class DirpResolution(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_int32),
        ("height", ctypes.c_int32),
    ]

# --- GŁÓWNA KLASA OBSŁUGUJĄCA DLL ---

class DJIThermalSDK:
    def __init__(self, dll_path: str):
        """Ładuje bibliotekę libdirp.dll i definiuje jej funkcje."""
        tools_dir = Path(dll_path).parent
        os.add_dll_directory(str(tools_dir))
        self.lib = ctypes.CDLL(str(dll_path))

        self.lib.dirp_create_from_rjpeg.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int32,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self.lib.dirp_create_from_rjpeg.restype = ctypes.c_int32

        self.lib.dirp_get_rjpeg_resolution.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(DirpResolution),
        ]
        self.lib.dirp_get_rjpeg_resolution.restype = ctypes.c_int32
        
        self.lib.dirp_measure_ex.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int32
        ]
        self.lib.dirp_measure_ex.restype = ctypes.c_int32

        # --- NOWOŚĆ: Rejestracja funkcji radiometrycznej ---
        self.lib.dirp_get_measurement_params.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(MeasurementParams),
        ]
        self.lib.dirp_get_measurement_params.restype = ctypes.c_int32

        self.lib.dirp_destroy.argtypes = [ctypes.c_void_p]
        self.lib.dirp_destroy.restype = ctypes.c_int32

    def get_radiometry(self, handle) -> dict:
        """Pobiera parametry radiometryczne ze zdjęcia na podstawie jego uchwytu w RAM."""
        params = MeasurementParams()
        if self.lib.dirp_get_measurement_params(handle, ctypes.byref(params)) == 0:
            return {
                "distance": round(params.distance, 2),
                "humidity": round(params.humidity, 2),
                "emissivity": round(params.emissivity, 2),
                "reflection": round(params.reflection, 2),
                "ambient_temp": round(params.ambient_temp, 2)
            }
        print("BŁĄD: Nie można pobrać parametrów radiometrycznych.")
        return {}

    def process_image_info(self, image_path: str):
        """Wczytuje obraz do RAM, pobiera rozdzielczość, temperatury oraz radiometrię."""
        image_data = Path(image_path).read_bytes()
        buffer = (ctypes.c_uint8 * len(image_data)).from_buffer_copy(image_data)
        handle = ctypes.c_void_p()

        if self.lib.dirp_create_from_rjpeg(buffer, len(image_data), ctypes.byref(handle)) != 0:
            print("BŁĄD: Nie można otworzyć zdjęcia przez SDK.")
            return None

        try:
            res = DirpResolution()
            if self.lib.dirp_get_rjpeg_resolution(handle, ctypes.byref(res)) == 0:
                print(f"Sukces! Zdjęcie zdekodowane. Wymiary: {res.width}x{res.height}")
                
                num_pixels = res.width * res.height
                buffer_size = num_pixels * ctypes.sizeof(ctypes.c_float)
                
                temp_buffer = (ctypes.c_float * num_pixels)()
                
                if self.lib.dirp_measure_ex(handle, temp_buffer, buffer_size) != 0:
                    print("BŁĄD: Nie można zmierzyć temperatur.")
                    return None
                    
                temperature_matrix = np.ctypeslib.as_array(temp_buffer).reshape((res.height, res.width))
                print(f"Temperatury pobrane! Min: {temperature_matrix.min():.2f} °C | Max: {temperature_matrix.max():.2f} °C")
                
                # --- NOWOŚĆ: Pobieranie radiometrii i zwracanie dwóch wartości ---
                radiometry_data = self.get_radiometry(handle)
                
                return temperature_matrix, radiometry_data
       
            else:
                print("BŁĄD: Nie można pobrać rozdzielczości.")
                return None
        finally:
            self.lib.dirp_destroy(handle)

# --- SZYBKI TEST ---
if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    dll_path = str(base_dir / "tools" / "libdirp.dll")
    test_image = str(base_dir / "data" / "input" / "DJI_20230920123005_0001_T.JPG")
    
    sdk = DJIThermalSDK(dll_path)
    wynik = sdk.process_image_info(test_image)
    
    # Testujemy, czy funkcja poprawnie zwraca dwie rzeczy
    if wynik is not None:
        macierz, parametry = wynik
        print("\nOdczytane parametry radiometryczne:")
        for klucz, wartosc in parametry.items():
            print(f"- {klucz}: {wartosc}")