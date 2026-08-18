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


class FloatRange(ctypes.Structure):
    _fields_ = [
        ("min", ctypes.c_float),
        ("max", ctypes.c_float),
    ]


class MeasurementParamsRange(ctypes.Structure):
    _fields_ = [
        ("distance", FloatRange),
        ("humidity", FloatRange),
        ("emissivity", FloatRange),
        ("reflection", FloatRange),
        ("ambient_temp", FloatRange),
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
        <project>\\tools\\libdirp.dll

    PyInstaller:
        <temporary PyInstaller dir>\\tools\\libdirp.dll
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
            self.lib = ctypes.CDLL(
                str(dll_path)
            )
        except OSError as exc:
            raise DJIError(
                f"Nie udało się załadować DJI SDK: {exc}"
            ) from exc

        self._configure_api()

    def _configure_api(self):
        self.lib.dirp_create_from_rjpeg.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int32,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self.lib.dirp_create_from_rjpeg.restype = (
            ctypes.c_int32
        )

        self.lib.dirp_get_rjpeg_resolution.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(DirpResolution),
        ]
        self.lib.dirp_get_rjpeg_resolution.restype = (
            ctypes.c_int32
        )

        self.lib.dirp_measure_ex.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int32,
        ]
        self.lib.dirp_measure_ex.restype = (
            ctypes.c_int32
        )

        self.lib.dirp_get_measurement_params.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(MeasurementParams),
        ]
        self.lib.dirp_get_measurement_params.restype = (
            ctypes.c_int32
        )

        self.lib.dirp_set_measurement_params.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(MeasurementParams),
        ]
        self.lib.dirp_set_measurement_params.restype = (
            ctypes.c_int32
        )

        self.lib.dirp_get_measurement_params_range.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(MeasurementParamsRange),
        ]
        self.lib.dirp_get_measurement_params_range.restype = (
            ctypes.c_int32
        )

        self.lib.dirp_destroy.argtypes = [
            ctypes.c_void_p
        ]
        self.lib.dirp_destroy.restype = (
            ctypes.c_int32
        )

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
            "distance": round(
                float(params.distance),
                4
            ),
            "humidity": round(
                float(params.humidity),
                4
            ),
            "emissivity": round(
                float(params.emissivity),
                4
            ),
            "reflection": round(
                float(params.reflection),
                4
            ),
            "ambient_temp": round(
                float(params.ambient_temp),
                4
            ),
        }

    def get_measurement_ranges(self, handle):
        ranges = MeasurementParamsRange()

        result = (
            self.lib
            .dirp_get_measurement_params_range(
                handle,
                ctypes.byref(ranges)
            )
        )

        if result != 0:
            raise DJIError(
                "Nie udało się pobrać zakresów parametrów "
                f"radiometrycznych (kod DJI SDK: {result})."
            )

        return {
            "distance": (
                float(ranges.distance.min),
                float(ranges.distance.max),
            ),
            "humidity": (
                float(ranges.humidity.min),
                float(ranges.humidity.max),
            ),
            "emissivity": (
                float(ranges.emissivity.min),
                float(ranges.emissivity.max),
            ),
            "reflection": (
                float(ranges.reflection.min),
                float(ranges.reflection.max),
            ),
            "ambient_temp": (
                float(ranges.ambient_temp.min),
                float(ranges.ambient_temp.max),
            ),
        }

    def set_measurement_params(
        self,
        handle,
        overrides
    ):
        """
        Nadpisuje wybrane parametry radiometryczne.

        Dozwolone klucze:
        - distance
        - humidity
        - emissivity
        - reflection

        ambient_temp pozostaje aktualnie wartością
        pochodzącą z oryginalnego R-JPEG.
        """
        if not overrides:
            return self.get_radiometry(
                handle
            )

        allowed_keys = {
            "distance",
            "humidity",
            "emissivity",
            "reflection",
        }

        unknown_keys = (
            set(overrides)
            - allowed_keys
        )

        if unknown_keys:
            raise ValueError(
                "Nieobsługiwane parametry radiometryczne: "
                + ", ".join(
                    sorted(unknown_keys)
                )
            )

        current = self.get_radiometry(
            handle
        )

        ranges = self.get_measurement_ranges(
            handle
        )

        updated = dict(
            current
        )

        for key, raw_value in overrides.items():
            if raw_value is None:
                continue

            try:
                value = float(
                    raw_value
                )
            except (
                TypeError,
                ValueError
            ) as exc:
                raise ValueError(
                    f"Niepoprawna wartość parametru "
                    f"{key}: {raw_value}"
                ) from exc

            if not np.isfinite(
                value
            ):
                raise ValueError(
                    f"Parametr {key} musi być "
                    "skończoną liczbą."
                )

            minimum, maximum = (
                ranges[key]
            )

            if not (
                minimum
                <= value
                <= maximum
            ):
                raise ValueError(
                    f"Parametr {key} = {value} "
                    f"jest poza zakresem DJI SDK "
                    f"[{minimum}, {maximum}]."
                )

            updated[key] = value

        params = MeasurementParams(
            distance=updated["distance"],
            humidity=updated["humidity"],
            emissivity=updated["emissivity"],
            reflection=updated["reflection"],
            ambient_temp=current[
                "ambient_temp"
            ],
        )

        result = (
            self.lib
            .dirp_set_measurement_params(
                handle,
                ctypes.byref(params)
            )
        )

        if result != 0:
            raise DJIError(
                "DJI SDK odrzucił parametry "
                f"radiometryczne "
                f"(kod DJI SDK: {result})."
            )

        return self.get_radiometry(
            handle
        )

    def process_image_info(
        self,
        image_path,
        measurement_overrides=None
    ):
        image_path = Path(
            image_path
        )

        if not image_path.exists():
            raise FileNotFoundError(
                f"Plik nie istnieje: {image_path}"
            )

        if image_path.suffix.lower() not in {
            ".jpg",
            ".jpeg",
        }:
            raise InvalidRJPEGError(
                f"Nieobsługiwany format pliku: "
                f"{image_path.suffix}"
            )

        try:
            image_data = (
                image_path.read_bytes()
            )
        except OSError as exc:
            raise DJIError(
                f"Nie można odczytać pliku: {exc}"
            ) from exc

        if not image_data:
            raise InvalidRJPEGError(
                "Plik jest pusty."
            )

        buffer = (
            ctypes.c_uint8
            * len(image_data)
        ).from_buffer_copy(
            image_data
        )

        handle = ctypes.c_void_p()

        create_result = (
            self.lib
            .dirp_create_from_rjpeg(
                buffer,
                len(image_data),
                ctypes.byref(handle)
            )
        )

        if create_result != 0:
            raise InvalidRJPEGError(
                "Plik JPG nie jest poprawnym DJI "
                "radiometric R-JPEG lub jest uszkodzony "
                f"(kod DJI SDK: {create_result})."
            )

        try:
            resolution = DirpResolution()

            resolution_result = (
                self.lib
                .dirp_get_rjpeg_resolution(
                    handle,
                    ctypes.byref(
                        resolution
                    )
                )
            )

            if resolution_result != 0:
                raise DJIError(
                    "Nie udało się pobrać "
                    "rozdzielczości "
                    f"(kod DJI SDK: "
                    f"{resolution_result})."
                )

            if (
                resolution.width <= 0
                or resolution.height <= 0
            ):
                raise DJIError(
                    "DJI SDK zwrócił "
                    "niepoprawną rozdzielczość."
                )

            print(
                "Sukces! Zdjęcie zdekodowane. "
                f"Wymiary: "
                f"{resolution.width}x"
                f"{resolution.height}"
            )

            original_radiometry = (
                self.get_radiometry(
                    handle
                )
            )

            print(
                "\nParametry zapisane w R-JPEG:"
            )

            for key, value in (
                original_radiometry.items()
            ):
                print(
                    f"- {key}: {value}"
                )

            if measurement_overrides:
                print(
                    "\nNadpisywanie parametrów:"
                )

                for key, value in (
                    measurement_overrides
                    .items()
                ):
                    if value is not None:
                        print(
                            f"- {key}: {value}"
                        )

                radiometry_data = (
                    self.set_measurement_params(
                        handle,
                        measurement_overrides
                    )
                )

            else:
                radiometry_data = (
                    original_radiometry
                )

            print(
                "\nParametry użyte do "
                "obliczenia temperatur:"
            )

            for key, value in (
                radiometry_data.items()
            ):
                print(
                    f"- {key}: {value}"
                )

            num_pixels = (
                resolution.width
                * resolution.height
            )

            buffer_size = (
                num_pixels
                * ctypes.sizeof(
                    ctypes.c_float
                )
            )

            temp_buffer = (
                ctypes.c_float
                * num_pixels
            )()

            measure_result = (
                self.lib
                .dirp_measure_ex(
                    handle,
                    temp_buffer,
                    buffer_size
                )
            )

            if measure_result != 0:
                raise DJIError(
                    "Nie udało się obliczyć "
                    "temperatur "
                    f"(kod DJI SDK: "
                    f"{measure_result})."
                )

            temperature_matrix = (
                np.ctypeslib
                .as_array(
                    temp_buffer
                )
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
                    "DJI SDK zwrócił NaN lub Inf "
                    "w macierzy temperatur."
                )

            print(
                "\nTemperatury pobrane! "
                f"Min: "
                f"{temperature_matrix.min():.2f} °C | "
                f"Max: "
                f"{temperature_matrix.max():.2f} °C | "
                f"Mean: "
                f"{temperature_matrix.mean():.2f} °C"
            )

            return (
                temperature_matrix,
                radiometry_data
            )

        finally:
            if handle.value:
                self.lib.dirp_destroy(
                    handle
                )


if __name__ == "__main__":
    base_dir = get_app_base_dir()

    dll_path = get_default_dll_path()

    test_image = (
        base_dir
        / "data"
        / "input"
        / "DJI_20230920123005_0001_T.JPG"
    )

    print(
        f"Base dir: {base_dir}"
    )

    print(
        f"DJI DLL:  {dll_path}"
    )

    sdk = DJIThermalSDK(
        dll_path
    )

    try:
        print()
        print("=" * 60)
        print("TEST A - PARAMETRY ZDJĘCIA")
        print("=" * 60)

        matrix_original, params_original = (
            sdk.process_image_info(
                test_image
            )
        )

        print()
        print("=" * 60)
        print("TEST B - DISTANCE = 25 m")
        print("=" * 60)

        matrix_modified, params_modified = (
            sdk.process_image_info(
                test_image,
                measurement_overrides={
                    "distance": 25.0,
                }
            )
        )

        difference = (
            matrix_modified
            - matrix_original
        )

        print()
        print("=" * 60)
        print("PORÓWNANIE")
        print("=" * 60)

        print(
            f"Original mean: "
            f"{matrix_original.mean():.6f} °C"
        )

        print(
            f"Modified mean: "
            f"{matrix_modified.mean():.6f} °C"
        )

        print(
            f"Mean change:   "
            f"{difference.mean():.6f} °C"
        )

        print(
            f"Max change:    "
            f"{np.max(np.abs(difference)):.6f} °C"
        )

        if np.array_equal(
            matrix_original,
            matrix_modified
        ):
            print(
                "UWAGA: raster się nie zmienił."
            )
        else:
            print(
                "OK: zmiana parametrów "
                "wpłynęła na raster temperatur."
            )

    except Exception as exc:
        print(
            f"\nBŁĄD: {exc}"
        )