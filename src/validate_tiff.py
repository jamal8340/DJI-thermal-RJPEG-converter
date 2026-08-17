import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from validator import validate_files


def main():
    output_dir = PROJECT_ROOT / "data" / "output"

    if not output_dir.exists():
        print(f"Folder nie istnieje: {output_dir}")
        return

    tiff_files = sorted([
        path
        for path in output_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".tif", ".tiff"}
    ])

    if not tiff_files:
        print("Brak plików TIFF do walidacji.")
        return

    print(
        f"Walidacja {len(tiff_files)} plików TIFF...\n"
    )

    validation = validate_files(
        tiff_files
    )

    for result in validation["results"]:
        filename = result["filename"]
        status = result["status"]

        print(
            f"[{status}] {filename}"
        )

        for error in result.get(
            "errors",
            []
        ):
            print(
                f"       ERROR: {error}"
            )

        for warning in result.get(
            "warnings",
            []
        ):
            print(
                f"       WARNING: {warning}"
            )

    print()
    print("=" * 50)
    print("PODSUMOWANIE WALIDACJI")

    print(
        f"PASS:     {validation['passed']}"
    )

    print(
        f"WARNING:  {validation['warnings']}"
    )

    print(
        f"FAIL:     {validation['failed']}"
    )

    print(
        f"RAZEM:    {validation['total']}"
    )

    print()

    if validation["failed"] > 0:
        print(
            "BŁĄD - część TIFF-ów nie przeszła walidacji."
        )

    elif validation["warnings"] > 0:
        print(
            "OK - wszystkie TIFF-y są używalne."
        )

        print(
            "Niektóre pliki mają tylko ostrzeżenia "
            "dotyczące opcjonalnych metadanych."
        )

    else:
        print(
            "OK - wszystkie TIFF-y przeszły "
            "walidację bez ostrzeżeń."
        )


if __name__ == "__main__":
    main()