import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from validator import validate_files


def main():
    """Validate all TIFF files in the default development output directory."""
    output_dir = PROJECT_ROOT / "data" / "output"

    if not output_dir.exists():
        raise FileNotFoundError(
            f"Output folder does not exist: {output_dir}"
        )

    tiff_files = sorted(
        path
        for path in output_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".tif", ".tiff"}
    )

    if not tiff_files:
        print("No TIFF files found.")
        return

    print(f"Validating {len(tiff_files)} TIFF files...\n")
    validation = validate_files(tiff_files)

    for result in validation["results"]:
        print(f"[{result['status']}] {result['filename']}")

        for error in result.get("errors", []):
            print(f"    ERROR: {error}")

        for warning in result.get("warnings", []):
            print(f"    WARNING: {warning}")

    print()
    print("=" * 50)
    print("VALIDATION SUMMARY")
    print(f"PASS:     {validation['passed']}")
    print(f"WARNING:  {validation['warnings']}")
    print(f"FAIL:     {validation['failed']}")
    print(f"TOTAL:    {validation['total']}")
    print()

    if validation["failed"] > 0:
        print("FAIL: some TIFF files did not pass validation.")
        raise SystemExit(1)

    if validation["warnings"] > 0:
        print(
            "PASS WITH WARNINGS: all TIFF files are usable, "
            "but some contain non-critical metadata warnings."
        )
        return

    print("PASS: all TIFF files passed validation without warnings.")


if __name__ == "__main__":
    main()