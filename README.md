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
- Automatic output folder generation
- Output folder naming based on radiometric parameters
- Detection of mixed source radiometric parameters
- Manual output folder override
- Existing TIFF handling
- Skip existing files
- Overwrite existing files
- Conversion progress tracking
- Conversion error handling
- Automatic TIFF validation
- PASS / WARNING / FAIL validation statuses
- Unified Excel conversion and validation report
- Validation against official DJI reference tools
- Tested with Agisoft Metashape
- Portable Windows executable packaging
- Minimal DJI runtime packaging for Windows executable builds

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

For a typical 640 × 512 DJI thermal image, an uncompressed Float32 TIFF is approximately 1.3 MB.

With lossless Deflate compression, tested output files are typically approximately 230–250 KB while preserving the original Float32 temperature values.

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

The displayed values are loaded from the first selected source image for reference.

During batch processing, every image continues to use its own stored parameters even though the GUI preview shows values from only the first selected image.

When the option is disabled, the user can enter custom values that are applied to all images in the current conversion batch.

Supported ranges, based on the DJI Thermal SDK used by the project, are:

- Emissivity: 0.10–1.00
- Distance: 1–25 m
- Humidity: 1–100%
- Reflected temperature: -40–100 °C

The GUI validates all entered parameters before conversion.

If multiple values are invalid, all detected errors are shown together.

Numeric values may be entered using either a dot or comma as the decimal separator.

Examples:

22 -> 22.0

0,95 -> 0.95

25 -> 25.0

Formatting is applied when the field loses focus or when Enter is pressed.

Custom values are passed to the official DJI Thermal SDK before temperature calculation using the SDK measurement parameter API.

The converter does not modify calculated temperatures manually after decoding.

Changing a measurement parameter causes the DJI SDK to recalculate the complete temperature raster using the selected settings.

## Automatic output folders

The GUI automatically proposes an output folder based on the selected input location and radiometric parameters.

For a selected folder:

D:\Project\Thermal

the output folder is created inside the selected input directory.

For a selected image:

D:\Project\Thermal\DJI_0001_T.JPG

the output folder is created in the same directory as the image.

When multiple selected images are located in the same directory, the output folder is also created in that directory.

If all selected source images use identical stored radiometric parameters, the output folder name contains those parameters.

Example:

TIFF_em_0.95_dist_25_hum_50_refl_25

If the selected images contain different stored radiometric parameters, the default output folder is:

TIFF_source_params

If custom radiometric values are enabled, the folder name is generated from the selected custom values.

Example:

TIFF_em_0.90_dist_25_hum_60_refl_20

The automatically selected path is only a default.

The user can always choose a different output location using the `Change output folder` button.

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
├── tools_dev/
├── data/
├── DJI_Thermal_Converter.spec
├── DJI_Thermal_Converter_onefile.spec
├── requirements.txt
├── THIRD_PARTY_NOTICES.txt
├── .gitignore
└── README.md

## Runtime files

The final Windows executable uses only the DJI runtime components required by the application.

The `tools/` directory contains:

- libdirp.dll
- libv_dirp.dll
- libv_girp.dll
- libv_iirp.dll
- libv_cirp.dll
- libv_hirp.dll
- libv_list.ini
- MicroIA_Release_x64.dll
- MicroJPEG_Release_x64.dll
- MicroTA_Release_x64.dll
- libexif.dll
- libintl-8.dll
- libiconv-2.dll

DJI development utilities, import libraries, documentation, datasets and SDK sample files are not included in the production runtime package.

Development-only DJI command-line utilities may be kept locally in:

tools_dev/

This directory is ignored by Git and is not included in production builds.

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
- openpyxl

PyInstaller is used for Windows executable builds.

## GUI

Run the graphical interface:

python src\gui.py

The GUI allows the user to:

- select one or multiple DJI thermal R-JPEG images
- select a folder containing thermal images
- automatically generate an output folder
- manually choose a different output folder
- use radiometric parameters stored in each source image
- enter custom emissivity
- enter custom measurement distance
- enter custom humidity
- enter custom reflected temperature
- validate custom radiometric parameters
- optionally overwrite existing TIFF files
- monitor conversion progress
- view conversion and validation status
- generate a final Excel report
- open the output folder after processing

Existing TIFF files are skipped by default unless the overwrite option is enabled.

When custom radiometric parameters are enabled, the same selected values are applied to all images in the current conversion batch.

When `Use values stored in each image` is enabled, every source R-JPEG uses its own stored radiometric values.

## Command-line conversion

Place DJI thermal R-JPEG files in:

data/input/

Run:

python src\converter.py

Converted TIFF files and the internal conversion report are written to the configured output directory.

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

The compression implementation has been internally tested against uncompressed Float32 output.

For the tested DJI 640 × 512 thermal images:

Uncompressed TIFF size: approximately 1.32 MB

Compressed TIFF size: approximately 230–250 KB

The compression is lossless and does not alter the Float32 temperature raster.

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

Example internal batch validation result:

PASS:     124
WARNING:  5
FAIL:     0
RAZEM:    129

The same validation status was maintained after switching the production TIFF output to Deflate compression.

## Unified Excel report

After GUI processing, the application generates one final report:

DJI_Thermal_Converter_Report.xlsx

The report combines conversion and validation information into a single workbook.

The workbook contains a `Results` sheet with per-image data and a `Summary` sheet with batch-level information.

The Results sheet can contain information such as:

- source filename
- conversion status
- validation status
- validation warnings
- validation errors
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
- output TIFF path
- conversion error information

The Summary sheet provides batch-level information such as:

- total files
- successfully converted files
- skipped files
- conversion errors
- PASS count
- WARNING count
- FAIL count
- radiometric parameter mode

Previous intermediate CSV reports are not intended to remain in the final user output folder.

The GUI removes old report files before generating the new final report.

## DJI reference validation

The converter has been internally validated against the official DJI reference utility using representative source R-JPEG images and equivalent radiometric parameters.

Development-only DJI utilities are stored outside the production runtime directory.

Example internal development command:

tools_dev\dji_irp.exe -s data\input\DJI_20230920123005_0001_T.JPG -a measure -o data\reference\official.raw --measurefmt float32

The project includes development tools for internal comparison of converter output with official DJI reference output.

Detailed evaluation results are kept as internal development and validation information rather than published as product claims.

## Custom radiometric parameter validation

Custom radiometric parameter handling has also been internally validated against the official DJI reference utility using equivalent measurement settings.

The custom values are passed to `dirp_set_measurement_params` before `dirp_measure_ex`.

This verifies that custom parameter handling is performed through the DJI SDK rather than by modifying the resulting temperature raster after conversion.

## Agisoft Metashape compatibility

The generated TIFF files have been tested in Agisoft Metashape.

Metashape successfully reads reference metadata from the converted TIFF files, including:

- Longitude
- Latitude
- Altitude
- Yaw
- Pitch
- Roll

Both development TIFF files and Deflate-compressed production TIFF files were tested.

The compressed production TIFF files retained the required reference information in Metashape.

A representative thermal image batch was successfully imported into Metashape.

The test workflow successfully produced:

- camera alignment
- depth maps
- point cloud
- DEM
- thermal orthomosaic

Individual images may remain unaligned due to image matching or scene characteristics.

This does not by itself indicate a TIFF conversion failure.

The thermal TIFF files can also be used together with RGB imagery in photogrammetry workflows when required by the project.

## Orientation metadata

DJI gimbal orientation values and Metashape orientation values may use different angle conventions.

For example, DJI gimbal pitch values and Metashape camera pitch values may not be numerically identical even when they describe the same camera orientation.

This is caused by differences in coordinate and orientation conventions and does not indicate metadata corruption.

DJI gimbal and flight orientation metadata are preserved from the original source image.

## Orthomosaic test

A Metashape thermal orthomosaic was exported as Float32 TIFF and inspected using:

python tests\orthomosaic_test.py

The exported orthomosaic retained Float32 raster data.

The exported file contained:

- channel 1: temperature raster
- channel 2: alpha / valid pixel mask

The orthomosaic generation process is performed by Metashape and may include interpolation and resampling.

These operations are separate from the source R-JPEG to TIFF conversion performed by this project.

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

Some metadata fields, such as `UTCAtExposure`, may be absent in individual source images.

These cases are reported as validation warnings rather than conversion failures.

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

Supported parameter ranges are validated according to DJI Thermal SDK measurement parameter ranges.

DJI SDK binaries and their redistribution are subject to DJI licensing terms.

The production application includes only runtime components required by the converter.

SDK development files, source samples, documentation, datasets, utility executables and import libraries are not included in the production executable package.

Third-party software and runtime components are documented in:

THIRD_PARTY_NOTICES.txt

Redistribution and internal deployment should follow the applicable DJI and third-party license terms.

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

Both onedir and onefile builds have been tested during development.

The onefile build produces a portable executable that can be moved and started without a local Python installation.

Production build specification:

DJI_Thermal_Converter_onefile.spec

Build command:

pyinstaller --noconfirm --clean DJI_Thermal_Converter_onefile.spec

The production specification includes only the required DJI runtime files instead of packaging the entire SDK directory.

The final executable was tested after being copied to a separate clean directory without access to the development project directory.

## Data and repository policy

Test images, generated TIFF files, development utilities, build output and other working data are not intended to be committed to the repository.

The following directories and files should remain local:

data/

.venv/

.vs/

build/

dist/

tools_dev/

__pycache__/

DJI SDK development files, documentation, samples, datasets and unnecessary utilities should not be committed or included in production builds.

The final application package should contain only runtime components required by the converter and permitted for redistribution.

## Third-party software notices

Third-party dependencies and runtime components are documented in:

THIRD_PARTY_NOTICES.txt

The project currently uses software including:

- DJI Thermal SDK runtime components
- Python
- NumPy
- Pillow
- tifffile
- openpyxl
- PyInstaller

Additional transitive runtime components may be included by Python packages or PyInstaller and remain subject to their respective license terms.

## Project status

- Core conversion engine: working
- DJI SDK integration: working
- Float32 TIFF generation: working
- Lossless Deflate TIFF compression: working
- Compressed TIFF pixel integrity: verified internally
- Batch conversion: working
- Multiple file conversion: working
- Automatic output folder generation: working
- Radiometric parameter-based output folder naming: working
- Mixed source parameter detection: working
- Manual output folder override: working
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
- Radiometric value formatting on focus loss: working
- Radiometric value formatting on Enter: working
- Use source image radiometric values option: working
- Conversion error handling: working
- Skip / overwrite handling: working
- Automatic TIFF validation: working
- PASS / WARNING / FAIL validation: working
- Unified Excel reporting: working
- DJI reference validation: internally tested
- Custom parameter comparison with DJI reference: internally tested
- Agisoft Metashape metadata compatibility: tested
- Agisoft Metashape compressed TIFF compatibility: tested
- Agisoft Metashape alignment workflow: tested
- DEM generation: tested
- Thermal orthomosaic generation: tested
- GUI: working
- Windows executable packaging: working
- PyInstaller onefile build: working
- Minimal DJI runtime packaging: working
- Standalone executable test outside development directory: working
- Third-party notices: added
- Automated pytest test suite: planned