# DJI Thermal R-JPEG Converter

Tool for converting radiometric DJI thermal R-JPEG images into single-band Float32 TIFF files containing temperature values in degrees Celsius.

The project uses the official DJI Thermal SDK for radiometric decoding and temperature calculation.

The converter is designed for batch processing of DJI thermal imagery and for use in workflows such as Agisoft Metashape.

## Current features

- DJI R-JPEG decoding using the official DJI Thermal SDK
- Float32 temperature raster generation
- Single-band TIFF output
- Temperature values stored directly in °C
- Lossless Deflate compression of output TIFF files
- Significantly reduced TIFF file size compared with uncompressed Float32 output
- EXIF metadata extraction
- DJI XMP metadata extraction
- Radiometric parameter extraction
- User-configurable radiometric parameters
- Option to use radiometric parameters stored in each source R-JPEG
- Custom emissivity setting
- Custom measurement distance setting
- Custom humidity setting
- Custom reflected temperature setting
- Validation of custom radiometric parameter ranges
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
- Portable Windows executable packaging

## Output

Each converted TIFF contains:

- one Float32 raster band
- temperature values in °C
- lossless Deflate compression
- DJI XMP metadata
- GPS metadata
- altitude metadata
- gimbal and flight orientation metadata
- radiometric parameters used during conversion
- standard TIFF Make / Model / DateTime tags
- additional converter metadata stored in `ImageDescription`

The output TIFF is designed to preserve both radiometric temperature values and metadata required by photogrammetry software such as Agisoft Metashape.

For a typical 640 × 512 DJI thermal image, an uncompressed Float32 TIFF is approximately 1.3 MB. With lossless Deflate compression, tested output files are typically approximately 230–250 KB while preserving exactly the same Float32 pixel values.

## Radiometric parameters

The converter can either use radiometric parameters stored in each source DJI R-JPEG or apply custom values selected by the user.

Supported configurable parameters are:

- Emissivity
- Distance
- Humidity
- Reflected temperature

The GUI contains the option:

`Use values stored in each image`

When this option is enabled, each image is converted using its own radiometric parameters stored in the original DJI R-JPEG.

The displayed values are loaded from the selected source image for reference.

When the option is disabled, the user can enter custom values that are applied to all images in the current conversion batch.

Supported ranges, based on the DJI Thermal SDK used by the project, are:

- Emissivity: 0.10–1.00
- Distance: 1–25 m
- Humidity: 1–100%
- Reflected temperature: -40–100 °C

The GUI validates all entered parameters before conversion. If multiple values are invalid, all detected errors are shown together.

Custom values are passed to the official DJI Thermal SDK before temperature calculation using the SDK measurement parameter API. The converter does not modify calculated temperatures manually after decoding.

For example, changing measurement distance from 5 m to 25 m causes the DJI SDK to recalculate the complete temperature raster using the new parameter.

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
│   ├── orthomosaic_test.py
│   ├── test_tifffile_deflate.py
│   └── test_tifffile_deflate_batch.py
├── tools/
├── data/
├── DJI_Thermal_Converter.spec
├── DJI_Thermal_Converter_onefile.spec
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

Main Python dependencies include:

- NumPy
- Pillow
- tifffile

## GUI

Run the graphical interface:

python src\gui.py

The GUI allows the user to:

- select one or multiple DJI thermal R-JPEG images
- select a folder containing thermal images
- choose an output folder
- use radiometric parameters stored in each source image
- enter custom emissivity
- enter custom measurement distance
- enter custom humidity
- enter custom reflected temperature
- validate custom radiometric parameters
- optionally overwrite existing TIFF files
- monitor conversion progress
- view conversion and validation status
- open the output folder after processing

Existing TIFF files are skipped by default unless the overwrite option is enabled.

When custom radiometric parameters are enabled, the same selected values are applied to all images in the current conversion batch.

When `Use values stored in each image` is enabled, every source R-JPEG uses its own stored radiometric values.

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

Custom radiometric parameters can also be provided from the command line.

Example:

python src\converter.py "path\to\input" "path\to\output" --distance 25 --humidity 60 --emissivity 0.90 --reflection 20 --existing overwrite

Available radiometric arguments are:

--distance

--humidity

--emissivity

--reflection

If these arguments are not provided, the values stored in each DJI R-JPEG are used.

## Error handling

The converter processes files independently.

A single invalid or corrupted image does not stop the entire batch.

Current error categories include:

INVALID_RJPEG

DJI_SDK_ERROR

UNEXPECTED_ERROR

For example, a normal JPEG image without DJI radiometric data is rejected as an invalid DJI R-JPEG while the remaining thermal images continue processing.

Invalid custom radiometric values are rejected before temperature calculation.

The DJI SDK parameter ranges are also checked before applying custom measurement parameters.

## TIFF compression

Output TIFF files use lossless Deflate compression.

Compression is applied using `tifffile`.

The compression was tested against uncompressed Float32 output.

For the tested DJI 640 × 512 thermal images:

Uncompressed TIFF size: approximately 1.32 MB

Compressed TIFF size: approximately 230–250 KB

The compression is lossless.

Pixel comparison tests produced:

MAX DIFF: 0.0

MEAN DIFF: 0.0

RMSE: 0.0

This means Deflate compression does not modify any temperature values in the Float32 raster.

Compressed TIFF files were also successfully imported into Agisoft Metashape with reference metadata available.

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

The same validation result was obtained after switching the production TIFF output to Deflate compression.

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

The radiometric parameter values stored in the report represent the values used by the DJI SDK during temperature calculation.

## DJI reference validation

The temperature raster can be compared with output generated by the official DJI `dji_irp` utility.

Example DJI command:

tools\dji_irp.exe -s data\input\DJI_20230920123005_0001_T.JPG -a measure -o data\reference\official.raw --measurefmt float32

The project includes tools for internal comparison of converter output with official DJI Float32 output.

The production converter has been tested using identical source R-JPEG images and equivalent DJI SDK measurement parameters.

Internal tests confirmed pixel-identical Float32 temperature values between the generated TIFF raster and official DJI output.

The same result was confirmed after enabling Deflate compression.

## Custom radiometric parameter validation

Custom radiometric parameters were also compared with the official DJI `dji_irp` utility.

For example, a source R-JPEG containing:

distance: 5.0

humidity: 50.0

emissivity: 0.95

reflection: 25.0

can be recalculated using custom parameters such as:

distance: 25.0

humidity: 60.0

emissivity: 0.90

reflection: 20.0

The custom values are passed to `dirp_set_measurement_params` before `dirp_measure_ex`.

Tests using modified measurement parameters confirmed that the generated Float32 temperature raster matches the output produced by the official DJI tool using the same settings.

## Agisoft Metashape compatibility

The generated TIFF files have been tested in Agisoft Metashape.

Metashape successfully reads reference metadata from the converted TIFF files, including:

- Longitude
- Latitude
- Altitude
- Yaw
- Pitch
- Roll

Both uncompressed development TIFF files and the final Deflate-compressed TIFF files were tested.

The compressed production TIFF files retained the required reference information in Metashape.

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

The thermal TIFF files can also be used together with RGB imagery in photogrammetry workflows when required by the project.

## Orientation metadata

DJI gimbal orientation values and Metashape orientation values may use different angle conventions.

For example, DJI may store a gimbal pitch such as:

GimbalPitchDegree: -49.60

while Metashape may display the corresponding camera pitch as approximately:

Pitch: 40.40°

This is caused by the different orientation conventions used by DJI and Metashape and does not indicate metadata corruption.

DJI gimbal and flight orientation metadata are preserved from the original source image.

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

The orthomosaic generation process is performed by Metashape and may include interpolation and resampling. These operations are separate from the source R-JPEG to TIFF conversion performed by this project.

## DJI metadata preservation

The converter preserves important metadata from the source DJI R-JPEG image.

Important DJI XMP fields include:

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

In the current 129-image validation dataset, five images do not contain optional `UTCAtExposure` metadata in the source DJI data. These TIFF files remain valid and usable.

## DJI Thermal SDK

The project uses the official DJI Thermal SDK.

The converter does not implement proprietary DJI radiometric decoding itself.

Temperature values are calculated through the official DJI SDK API.

Main SDK operations currently used include:

dirp_create_from_rjpeg

dirp_get_rjpeg_resolution

dirp_measure_ex

dirp_get_measurement_params

dirp_set_measurement_params

dirp_get_measurement_params_range

dirp_destroy

The converter uses `dirp_get_measurement_params` to read radiometric settings stored in the source R-JPEG.

When the user provides custom radiometric parameters, the converter uses `dirp_set_measurement_params` before temperature calculation.

The supported parameter ranges are obtained and validated according to DJI Thermal SDK measurement parameter ranges.

DJI SDK binaries and their redistribution are subject to DJI licensing terms.

The redistribution rights for DJI SDK binaries and required runtime libraries should be reviewed before distributing packaged versions of the application.

## Compatibility with other DJI thermal cameras

The converter is based on DJI Thermal SDK R-JPEG processing rather than hard-coded decoding for one specific camera model.

It may therefore work with other DJI thermal cameras that generate radiometric R-JPEG files compatible with the same DJI Thermal SDK.

Compatibility with a specific camera or drone model should be confirmed using sample R-JPEG files from that device.

The recommended compatibility procedure is:

- obtain one or more original radiometric R-JPEG files from the target camera
- verify that DJI Thermal SDK can decode the files
- perform temperature conversion
- verify the generated Float32 TIFF
- verify required metadata
- verify downstream software compatibility if required

A device should not be considered officially supported by this project until it has been tested.

## Executable packaging

The application can be packaged as a Windows executable using PyInstaller.

Both onedir and onefile builds have been tested.

The onefile build produces a portable executable that can be moved and started without a local Python installation.

Example build specification:

DJI_Thermal_Converter_onefile.spec

Example build command:

pyinstaller --noconfirm --clean DJI_Thermal_Converter_onefile.spec

The executable includes the Python application and required runtime components.

Before distributing the executable, DJI SDK redistribution requirements and third-party license obligations should be reviewed.

## Data and repository policy

Test images, generated TIFF files, build output and other working data are not intended to be committed to the repository.

The following directories and files should remain local:

data/

.venv/

.vs/

build/

dist/

__pycache__/

DJI SDK development files, documentation, samples and unnecessary utilities should not be committed or redistributed unless their applicable license explicitly permits it.

The final application package should include only runtime components required by the converter and permitted for redistribution.

## Project status

- Core conversion engine: working
- DJI SDK integration: working
- Float32 TIFF generation: working
- Lossless Deflate TIFF compression: working
- Compressed TIFF pixel integrity: verified
- Batch conversion: working
- Multiple file conversion: working
- EXIF extraction: working
- DJI XMP extraction: working
- GPS preservation: working
- Orientation preservation: working
- Radiometric metadata extraction: working
- Custom emissivity: working
- Custom distance: working
- Custom humidity: working
- Custom reflected temperature: working
- DJI SDK radiometric parameter override: working
- Radiometric parameter validation: working
- Use source image radiometric values option: working
- Conversion error handling: working
- Skip / overwrite handling: working
- CSV conversion reporting: working
- TIFF validation: working
- PASS / WARNING / FAIL validation: working
- CSV validation reporting: working
- DJI reference validation: working
- Custom parameter comparison with DJI reference: working
- Agisoft Metashape metadata compatibility: tested
- Agisoft Metashape compressed TIFF compatibility: tested
- Agisoft Metashape alignment: tested
- DEM generation: tested
- Thermal orthomosaic generation: tested
- GUI: working
- Windows executable packaging: working
- PyInstaller onedir build: working
- PyInstaller onefile build: working
- Automated pytest test suite: planned