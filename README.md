# DJI Thermal R-JPEG Converter

Tool for converting radiometric DJI thermal R-JPEG images to single-band Float32 TIFF files containing temperature values in degrees Celsius.

The project uses the official DJI Thermal SDK for radiometric decoding.

## Current features

- DJI R-JPEG decoding using DJI Thermal SDK
- Float32 temperature raster generation
- Single-band TIFF output
- EXIF metadata extraction
- DJI XMP metadata extraction
- Radiometric parameter extraction
- Batch folder conversion
- CSV conversion report
- TIFF validation
- Validation against official DJI `dji_irp`

## Output

Each TIFF contains:

- one Float32 band
- temperature values in °C
- original DJI EXIF metadata
- DJI XMP metadata
- radiometric parameters
- standard TIFF Make / Model / DateTime tags

## Installation

Create virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1