# DJI Thermal R-JPEG Converter

Tool for converting radiometric DJI thermal R-JPEG images into single-band Float32 TIFF files containing temperature values in degrees Celsius.

The converter uses the DJI Thermal SDK for radiometric decoding and temperature calculation and is designed for batch processing and photogrammetry workflows such as Agisoft Metashape.

## Features

- DJI radiometric R-JPEG decoding
- Float32 temperature raster output
- Temperature values stored directly in °C
- Lossless Deflate TIFF compression
- Batch folder and multi-file conversion
- EXIF and DJI XMP metadata preservation
- GPS, altitude and orientation metadata preservation
- Source or custom radiometric parameters
- Custom emissivity
- Custom distance
- Custom humidity
- Custom reflected temperature
- Automatic radiometric parameter validation
- Automatic output folder generation
- Skip / overwrite handling
- Conversion progress tracking
- Automatic TIFF validation
- PASS / WARNING / FAIL validation statuses
- Unified Excel conversion and validation report
- Windows executable packaging with PyInstaller
- Tested with Agisoft Metashape

## Radiometric processing

The converter can use the radiometric parameters stored in each source DJI R-JPEG or apply custom values selected by the user.

Supported configurable parameters:

- Emissivity: 0.10–1.00
- Distance: 1–25 m
- Humidity: 1–100%
- Reflected temperature: -40–100 °C

When `Use values stored in each image` is enabled, every image uses its own radiometric parameters stored in the source R-JPEG.

The values displayed in the GUI are only a preview from the first selected image.

When source values are disabled, custom parameters are applied to all images in the current batch.

Temperature calculation is performed by the DJI Thermal SDK. The converter does not implement or modify the proprietary DJI radiometric algorithm.

## Output

Each converted TIFF contains:

- one Float32 raster band
- temperature values in °C
- lossless Deflate compression
- converter metadata in `ImageDescription`
- DJI XMP metadata in TIFF tag 700
- TIFF Make / Model / DateTime tags
- radiometric parameters used during conversion

The generated TIFF files are intended to retain metadata required by downstream photogrammetry workflows.

## Automatic output folders

The GUI can automatically create an output folder next to the selected input data.

When all selected source images use identical radiometric parameters, the folder name includes those values, for example:

`TIFF_em_0.95_dist_25_hum_50_refl_25`

If source images contain different radiometric parameters:

`TIFF_source_params`

For custom radiometric parameters, the output folder name is generated from the selected values.

Automatic output can be disabled using:

`Use automatic output folder`

A custom output location can then be selected manually.

## GUI

Run:

`python src\gui.py`

The GUI allows the user to:

- select individual images or a folder
- configure radiometric parameters
- select automatic or manual output
- skip or overwrite existing TIFF files
- monitor conversion progress
- view validation results
- generate the final Excel report
- open the output folder after processing

## Command-line conversion

Default input and output folders:

`python src\converter.py`

Custom folders:

`python src\converter.py "path\to\input" "path\to\output"`

Overwrite existing TIFF files:

`python src\converter.py "path\to\input" "path\to\output" --existing overwrite`

Example with custom radiometric parameters:

`python src\converter.py "path\to\input" "path\to\output" --distance 25 --humidity 60 --emissivity 0.90 --reflection 20`

If custom parameters are not provided, values stored in each R-JPEG are used.

## Validation

The converter validates generated TIFF files after GUI conversion.

Checks include:

- single-band raster structure
- Float32 data type
- finite temperature values
- raster dimensions
- temperature metadata consistency
- radiometric parameters
- DJI XMP metadata
- GPS and altitude
- gimbal orientation

Statuses:

- `PASS` — all required checks passed
- `WARNING` — TIFF is valid but optional metadata is missing
- `FAIL` — a critical validation problem was detected

Manual validation:

`python tests\validate_tiff.py`

## Excel report

After GUI processing, the application creates:

`DJI_Thermal_Converter_Report.xlsx`

The workbook contains:

- `Results` — per-image conversion and validation information
- `Summary` — batch statistics and radiometric mode

Intermediate CSV reports are used internally and are not intended to remain in the final output folder.

## Agisoft Metashape

Generated TIFF files have been tested in Agisoft Metashape.

The workflow has been verified for:

- reference metadata import
- camera alignment
- point cloud generation
- DEM generation
- thermal orthomosaic generation

DJI and Metashape may use different orientation conventions, so displayed pitch, yaw and roll values do not always use identical numeric representations.

## Project structure

DJI-thermal-RJPEG-converter/
├── src/
│   ├── converter.py
│   ├── dji_sdk.py
│   ├── metadata.py
│   ├── validator.py
│   ├── gui.py
│   ├── inspect_exif.py
│   ├── inspect_radiometry.py
│   └── validate_tiff.py
├── tests/
│   ├── validate_tiff.py
│   ├── compare_with_dji.py
│   ├── orthomosaic_test.py
│   ├── test_tifffile_deflate.py
│   └── test_tifffile_deflate_batch.py
├── assets/
├── tools/
├── tools_dev/
├── data/
├── DJI_Thermal_Converter.spec
├── DJI_Thermal_Converter_onefile.spec
├── requirements.txt
├── THIRD_PARTY_NOTICES.txt
├── .gitignore
└── README.md

## Installation

Create and activate a virtual environment:

`py -m venv .venv`

`.\.venv\Scripts\Activate.ps1`

Install dependencies:

`pip install -r requirements.txt`

Main Python dependencies:

- NumPy
- Pillow
- tifffile
- openpyxl

PyInstaller is used for Windows executable builds.

## Windows executable

Production onefile build:

`pyinstaller --noconfirm --clean DJI_Thermal_Converter_onefile.spec`

Output:

`dist\DJI_Thermal_Converter.exe`

The production build includes only the required DJI runtime components and application assets.

## DJI Thermal SDK

The converter uses the DJI Thermal SDK API for:

- R-JPEG decoding
- image resolution
- radiometric parameter extraction
- radiometric parameter overrides
- temperature raster calculation

DJI SDK binaries and redistribution are subject to DJI licensing terms.

Only runtime components required by the application should be included in production builds.

## Third-party software

Third-party dependencies and runtime components are documented in:

`THIRD_PARTY_NOTICES.txt`

This includes software such as:

- DJI Thermal SDK runtime components
- Python
- NumPy
- Pillow
- tifffile
- openpyxl
- PyInstaller

## Repository policy

Development data and generated files should remain local.

Ignored directories include:

.venv/
.vs/
data/
build/
dist/
tools_dev/
__pycache__/

The production package should contain only the files required to run the application and any required third-party notices.