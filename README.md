# DJI Thermal R-JPEG Converter

Tool for converting radiometric DJI thermal R-JPEG images into single-band Float32 TIFF files containing temperature values in degrees Celsius.

The project uses the official DJI Thermal SDK for radiometric decoding.

The converter is designed for batch processing of DJI thermal imagery and for use in workflows such as Agisoft Metashape.

## Current features

- DJI R-JPEG decoding using the official DJI Thermal SDK
- Float32 temperature raster generation
- Single-band TIFF output
- Temperature values stored directly in °C
- EXIF metadata extraction
- DJI XMP metadata extraction
- Radiometric parameter extraction
- GPS metadata preservation
- Altitude metadata preservation
- Gimbal and flight orientation preservation
- Batch folder conversion
- Multiple file conversion
- GUI for image and folder selection
- Output folder selection
- Existing TIFF handling
- Skip existing files
- Overwrite existing files
- Conversion progress tracking
- Conversion error handling
- CSV conversion report
- Automatic TIFF validation
- CSV validation report
- PASS / WARNING / FAIL validation statuses
- Validation against official DJI `dji_irp`
- Tested with Agisoft Metashape

## Output

Each converted TIFF contains:

- one Float32 raster band
- temperature values in °C
- original DJI EXIF metadata
- GPS metadata
- DJI XMP metadata
- radiometric parameters
- standard TIFF Make / Model / DateTime tags
- additional converter metadata stored in `ImageDescription`

The output TIFF is designed to preserve both radiometric temperature values and metadata required by photogrammetry software such as Agisoft Metashape.

## Project structure

DJI-thermal-RJPEG-converter/
├── src/
│   ├── converter.py
│   ├── dji_sdk.py
│   ├── metadata.py
│   ├── validator.py
│   ├── gui.py
│   ├── inspect_exif.py
│   └── inspect_radiometry.py
├── tests/
│   ├── validate_tiff.py
│   ├── compare_with_dji.py
│   └── orthomosaic_test.py
├── tools/
├── data/
├── requirements.txt
├── .gitignore
└── README.md

## Installation

Create a virtual environment:

py -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

## GUI

Run the graphical interface:

python src\gui.py

The GUI allows the user to select one or multiple DJI thermal R-JPEG images, select a folder containing images, choose an output folder, optionally overwrite existing TIFF files, monitor conversion progress, view conversion and validation status, and open the output folder after processing.

Existing TIFF files are skipped by default unless the overwrite option is enabled.

## Command-line conversion

Place DJI thermal R-JPEG files in:

data/input/

Run:

python src\converter.py

Converted TIFF files and the conversion report are written to:

data/output/

A custom input and output folder can also be provided:

python src\converter.py "path\to\input" "path\to\output"

Existing files are skipped by default.

To overwrite them:

python src\converter.py "path\to\input" "path\to\output" --existing overwrite

## Error handling

The converter processes files independently.

A single invalid or corrupted image does not stop the entire batch.

Current error categories include:

INVALID_RJPEG
DJI_SDK_ERROR
UNEXPECTED_ERROR

For example, a normal JPEG image without DJI radiometric data is rejected as an invalid DJI R-JPEG while the remaining thermal images continue processing.

## TIFF validation

Automatic validation is performed after GUI conversion.

Validation can also be run manually:

python tests\validate_tiff.py

The validator checks:

- single-band raster structure
- Float32 data type
- raster dimensions
- finite temperature values
- temperature metadata consistency
- minimum and maximum temperature consistency
- standard TIFF tags
- radiometric parameters
- EXIF metadata
- DJI XMP metadata
- GPS
- altitude
- gimbal orientation
- timestamps
- additional metadata

Validation statuses:

PASS means the TIFF passed all required checks.

WARNING means the TIFF is valid and usable, but optional metadata is missing.

Example:

Brak opcjonalnego DJI XMP: UTCAtExposure

A WARNING does not prevent the TIFF from being used.

FAIL means a critical validation problem was detected, for example:

- invalid raster structure
- wrong data type
- missing required temperature metadata
- invalid dimensions
- missing required DJI XMP fields
- NaN or Inf values

Example batch validation result:

PASS:     124
WARNING:  5
FAIL:     0
RAZEM:    129

## Validation report

After GUI processing, the application generates:

data/output/validation_report.csv

The report contains:

- filename
- validation status
- error count
- warning count
- validation errors
- validation warnings

## Conversion report

After batch conversion, the application generates:

data/output/conversion_report.csv

The report contains information such as:

- source filename
- conversion status
- image dimensions
- minimum temperature
- maximum temperature
- emissivity
- humidity
- measurement distance
- reflected temperature
- ambient temperature
- GPS coordinates
- absolute altitude
- relative altitude
- gimbal orientation
- flight orientation
- exposure timestamp
- camera serial number
- drone serial number
- conversion error information

## DJI reference validation

The temperature raster can be compared with output generated by the official DJI `dji_irp` utility.

Example DJI command:

tools\dji_irp.exe -s data\input\DJI_20230920123005_0001_T.JPG -a measure -o data\reference\official.raw --measurefmt float32

Then run:

python tests\compare_with_dji.py

The current converter implementation has been verified pixel-by-pixel against the official DJI Float32 output.

Example result:

Max difference:  0.00000000 °C
Mean difference: 0.00000000 °C
RMSE:            0.00000000 °C

This confirms that the generated Float32 temperature raster matches the official DJI temperature output.

## Agisoft Metashape compatibility

The generated TIFF files have been tested in Agisoft Metashape.

Metashape successfully reads metadata from the converted TIFF files, including:

- Longitude
- Latitude
- Altitude
- Yaw
- Pitch
- Roll

A test batch containing 129 thermal TIFF files was successfully imported into Metashape.

Example alignment result:

125 / 129 images aligned

The remaining images could still be loaded into Metashape but were not automatically aligned due to image matching limitations.

This does not indicate a TIFF conversion failure.

The test workflow successfully produced:

- camera alignment
- depth maps
- point cloud
- DEM
- thermal orthomosaic

## Orthomosaic test

A Metashape thermal orthomosaic was exported as Float32 TIFF and inspected using:

python tests\orthomosaic_test.py

The exported orthomosaic retained Float32 raster data.

Example:

Dtype: float32

The exported file contained:

- channel 1: temperature raster
- channel 2: alpha / valid pixel mask

Example statistics for valid temperature pixels:

Mean:   23.379351 °C
Median: 23.184223 °C
P01:    14.740828 °C
P99:    42.899948 °C
Max:    60.791855 °C

## DJI metadata preservation

The converter preserves metadata from the source DJI R-JPEG image.

Important metadata includes:

GpsLatitude
GpsLongitude
AbsoluteAltitude
RelativeAltitude
GimbalRollDegree
GimbalYawDegree
GimbalPitchDegree
FlightRollDegree
FlightYawDegree
FlightPitchDegree
UTCAtExposure
CameraSerialNumber
DroneSerialNumber

Metadata that is not present in the original DJI R-JPEG cannot be recreated by the converter.

Some metadata fields, such as `UTCAtExposure`, may be absent in individual source images. These cases are reported as validation warnings rather than conversion failures.

## DJI Thermal SDK

The project uses the official DJI Thermal SDK.

The converter does not implement proprietary DJI radiometric decoding itself.

Temperature values are extracted through the official DJI SDK API.

Main SDK operations currently used include:

dirp_create_from_rjpeg
dirp_get_rjpeg_resolution
dirp_measure_ex
dirp_get_measurement_params
dirp_destroy

DJI SDK binaries and their redistribution are subject to DJI licensing terms.

The redistribution rights for DJI SDK binaries should be verified before distributing a packaged version of the application.

## Data and repository policy

Test images, generated TIFF files and other working data are not intended to be committed to the repository.

The following directories and files should remain local:

data/
.venv/
.vs/
__pycache__/

The repository contains source code only, except for explicitly permitted placeholder files.

## Project status

- Core conversion engine: working
- DJI SDK integration: working
- Float32 TIFF generation: working
- Batch conversion: working
- Multiple file conversion: working
- EXIF extraction: working
- DJI XMP extraction: working
- GPS preservation: working
- Orientation preservation: working
- Radiometric metadata extraction: working
- Conversion error handling: working
- Skip / overwrite handling: working
- CSV conversion reporting: working
- TIFF validation: working
- PASS / WARNING / FAIL validation: working
- CSV validation reporting: working
- DJI reference validation: working
- Agisoft Metashape metadata compatibility: tested
- Agisoft Metashape alignment: tested
- DEM generation: tested
- Thermal orthomosaic generation: tested
- GUI: working
- Executable packaging: planned
- Automated pytest test suite: planned