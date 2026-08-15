import ctypes
import os
from pathlib import Path


class MeasurementParams(ctypes.Structure):
    _fields_ = [
        ("distance", ctypes.c_float),
        ("humidity", ctypes.c_float),
        ("emissivity", ctypes.c_float),
        ("reflection", ctypes.c_float),
        ("ambient_temp", ctypes.c_float),
    ]


base_dir = Path(__file__).resolve().parent.parent

image_path = (
    base_dir
    / "data"
    / "input"
    / "DJI_20230920123005_0001_T.JPG"
)

tools_dir = base_dir / "tools"
dll_path = tools_dir / "libdirp.dll"

os.add_dll_directory(str(tools_dir))
libdirp = ctypes.CDLL(str(dll_path))

libdirp.dirp_create_from_rjpeg.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_int32,
    ctypes.POINTER(ctypes.c_void_p),
]
libdirp.dirp_create_from_rjpeg.restype = ctypes.c_int32

libdirp.dirp_get_measurement_params.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(MeasurementParams),
]
libdirp.dirp_get_measurement_params.restype = ctypes.c_int32

libdirp.dirp_destroy.argtypes = [ctypes.c_void_p]
libdirp.dirp_destroy.restype = ctypes.c_int32


image_data = image_path.read_bytes()

buffer = (ctypes.c_uint8 * len(image_data)).from_buffer_copy(image_data)
handle = ctypes.c_void_p()

result = libdirp.dirp_create_from_rjpeg(
    buffer,
    len(image_data),
    ctypes.byref(handle),
)

if result != 0:
    raise RuntimeError(f"Could not create DIRP handle. Error code: {result}")

try:
    params = MeasurementParams()

    result = libdirp.dirp_get_measurement_params(
        handle,
        ctypes.byref(params),
    )

    if result != 0:
        raise RuntimeError(
            f"Could not read measurement parameters. Error code: {result}"
        )

    print("\n=== DJI RADIOMETRY ===")
    print("=" * 80)
    print(f"Distance: {params.distance:.3f} m")
    print(f"Humidity: {params.humidity:.3f} %")
    print(f"Emissivity: {params.emissivity:.3f}")
    print(f"Reflection temperature: {params.reflection:.3f} °C")
    print(f"Ambient temperature: {params.ambient_temp:.3f} °C")

finally:
    libdirp.dirp_destroy(handle)