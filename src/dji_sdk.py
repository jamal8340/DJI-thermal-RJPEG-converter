import ctypes
import os
import sys
from pathlib import Path

import numpy as np


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


class DJIError(RuntimeError):
    """Błąd związany z DJI Thermal SDK."""


class InvalidRJPEGError(DJIError):
    """Plik nie jest poprawnym radiometrycznym DJI R-JPEG."""


def get_app_base_dir():
    """
    Zwraca katalog bazowy aplikacji.

    Działa zarówno:
    - przy uruchamianiu kodu przez Pythona,
    - po spakowaniu aplikacji przez PyInstaller.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )


def get_default_dll_path():
    """
    Zwraca ścieżkę do libdirp.dll.

    Python:
        <project>\tools\libdirp.dll

    PyInstaller --onedir:
        <exe>\_internal\tools\libdirp.dll
    """
    if getattr(sys, "frozen", False):
        return (
            Path(sys._MEIPASS)
            / "tools"
            / "libdirp.dll"
        )

    return (
        get_app_base_dir()
        / "tools"
        / "libdirp.dll"
    )


class DJIThermalSDK:
    def __init__(self, dll_path=None):
        if dll_path is None:
            dll_path = get_default_dll_path()

        dll_path = Path(dll_path).resolve()

        if not dll_path.exists():
            raise FileNotFoundError(
                f"Nie znaleziono biblioteki DJI SDK: {dll_path}"
            )

        tools_dir = dll_path.parent

        self._dll_directory_handle = None

        if hasattr(os, "add_dll_directory"):
            self._dll_directory_handle = os.add_dll_directory(
                str(tools_dir)
            )

        try:
            self.lib = ctypes.CDLL(str(dll_path))
        except OSError as exc:
            raise DJIError(
                f"Nie udało się załadować DJI SDK: {exc}"
            ) from exc

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
            ctypes.c_int32,
        ]
        self.lib.dirp_measure_ex.restype = ctypes.c_int32

        self.lib.dirp_get_measurement_params.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(MeasurementParams),
        ]
        self.lib.dirp_get_measurement_params.restype = ctypes.c_int32

        self.lib.dirp_destroy.argtypes = [
            ctypes.c_void_p
        ]
        self.lib.dirp_destroy.restype = ctypes.c_int32

    def get_radiometry(self, handle):
        params = MeasurementParams()

        result = self.lib.dirp_get_measurement_params(
            handle,
            ctypes.byref(params)
        )

        if result != 0:
            raise DJIError(
                "Nie udało się pobrać parametrów radiometrycznych "
                f"(kod DJI SDK: {result})."
            )

        return {
            "distance": round(params.distance, 2),
            "humidity": round(params.humidity, 2),
            "emissivity": round(params.emissivity, 2),
            "reflection": round(params.reflection, 2),
            "ambient_temp": round(params.ambient_temp, 2),
        }

    def process_image_info(self, image_path):
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Plik nie istnieje: {image_path}"
            )

        if image_path.suffix.lower() not in {".jpg", ".jpeg"}:
            raise InvalidRJPEGError(
                f"Nieobsługiwany format pliku: {image_path.suffix}"
            )

        try:
            image_data = image_path.read_bytes()
        except OSError as exc:
            raise DJIError(
                f"Nie można odczytać pliku: {exc}"
            ) from exc

        if not image_data:
            raise InvalidRJPEGError(
                "Plik jest pusty."
            )

        buffer = (
            ctypes.c_uint8 * len(image_data)
        ).from_buffer_copy(image_data)

        handle = ctypes.c_void_p()

        create_result = self.lib.dirp_create_from_rjpeg(
            buffer,
            len(image_data),
            ctypes.byref(handle)
        )

        if create_result != 0:
            raise InvalidRJPEGError(
                "Plik JPG nie jest poprawnym DJI radiometric R-JPEG "
                f"lub jest uszkodzony (kod DJI SDK: {create_result})."
            )

        try:
            resolution = DirpResolution()

            resolution_result = self.lib.dirp_get_rjpeg_resolution(
                handle,
                ctypes.byref(resolution)
            )

            if resolution_result != 0:
                raise DJIError(
                    "Nie udało się pobrać rozdzielczości "
                    f"(kod DJI SDK: {resolution_result})."
                )

            if resolution.width <= 0 or resolution.height <= 0:
                raise DJIError(
                    "DJI SDK zwrócił niepoprawną rozdzielczość."
                )

            print(
                "Sukces! Zdjęcie zdekodowane. "
                f"Wymiary: {resolution.width}x{resolution.height}"
            )

            num_pixels = (
                resolution.width
                * resolution.height
            )

            buffer_size = (
                num_pixels
                * ctypes.sizeof(ctypes.c_float)
            )

            temp_buffer = (
                ctypes.c_float * num_pixels
            )()

            measure_result = self.lib.dirp_measure_ex(
                handle,
                temp_buffer,
                buffer_size
            )

            if measure_result != 0:
                raise DJIError(
                    "Nie udało się obliczyć temperatur "
                    f"(kod DJI SDK: {measure_result})."
                )

            temperature_matrix = (
                np.ctypeslib
                .as_array(temp_buffer)
                .copy()
                .reshape(
                    (
                        resolution.height,
                        resolution.width
                    )
                )
            )

            if not np.isfinite(
                temperature_matrix
            ).all():
                raise DJIError(
                    "DJI SDK zwrócił NaN lub Inf w macierzy temperatur."
                )

            print(
                "Temperatury pobrane! "
                f"Min: {temperature_matrix.min():.2f} °C | "
                f"Max: {temperature_matrix.max():.2f} °C"
            )

            radiometry_data = self.get_radiometry(
                handle
            )

            return (
                temperature_matrix,
                radiometry_data
            )

        finally:
            if handle.value:
                self.lib.dirp_destroy(handle)


if __name__ == "__main__":
    base_dir = get_app_base_dir()

    dll_path = get_default_dll_path()

    test_image = (
        base_dir
        / "data"
        / "input"
        / "DJI_20230920123005_0001_T.JPG"
    )

    print(f"Base dir: {base_dir}")
    print(f"DJI DLL:  {dll_path}")

    sdk = DJIThermalSDK(
        dll_path
    )

    try:
        matrix, params = sdk.process_image_info(
            test_image
        )

        print("\nOdczytane parametry radiometryczne:")

        for key, value in params.items():
            print(
                f"- {key}: {value}"
            )

    except Exception as exc:
        print(
            f"BŁĄD: {exc}"
        )