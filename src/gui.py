import csv
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from converter import (
    convert_folder,
    convert_images,
)

from validator import (
    validate_files,
    save_validation_report,
)


BG = "#F7F1E7"
CARD_BG = "#FFFDF8"
TEXT = "#171717"
MUTED = "#6D675F"
ACCENT = "#D39A2C"
ACCENT_HOVER = "#B9801E"
BORDER = "#DDD5C8"


class ConverterGUI:
    def __init__(self, root):
        self.root = root

        self.root.title(
            "DJI Thermal R-JPEG Converter"
        )

        self.root.geometry(
            "800x610"
        )

        self.root.minsize(
            740,
            550
        )

        self.root.configure(
            bg=BG
        )

        base_dir = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        self.default_dll = (
            base_dir
            / "tools"
            / "libdirp.dll"
        )

        self.default_output = (
            base_dir
            / "data"
            / "output"
        )

        self.selected_files = []
        self.input_folder = None
        self.selection_mode = None

        self.last_output_dir = None

        self.output_path = tk.StringVar(
            value=str(
                self.default_output
            )
        )

        self.input_status = tk.StringVar(
            value=""
        )

        self.output_status = tk.StringVar(
            value=(
                "✓ Default output folder selected"
            )
        )

        self.main_status = tk.StringVar(
            value="Ready"
        )

        self.overwrite_existing = (
            tk.BooleanVar(
                value=False
            )
        )

        self.setup_style()
        self.create_widgets()

    def setup_style(self):
        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )
        except tk.TclError:
            pass

        style.configure(
            "Main.TFrame",
            background=BG
        )

        style.configure(
            "Card.TFrame",
            background=CARD_BG
        )

        style.configure(
            "Title.TLabel",
            background=BG,
            foreground=TEXT,
            font=(
                "Segoe UI",
                21,
                "bold"
            )
        )

        style.configure(
            "Subtitle.TLabel",
            background=BG,
            foreground=MUTED,
            font=(
                "Segoe UI",
                10
            )
        )

        style.configure(
            "Section.TLabel",
            background=CARD_BG,
            foreground=TEXT,
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        style.configure(
            "Muted.TLabel",
            background=CARD_BG,
            foreground=MUTED,
            font=(
                "Segoe UI",
                9
            )
        )

        style.configure(
            "Success.TLabel",
            background=CARD_BG,
            foreground=ACCENT_HOVER,
            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

        style.configure(
            "Status.TLabel",
            background=BG,
            foreground=MUTED,
            font=(
                "Segoe UI",
                9
            )
        )

        style.configure(
            "Secondary.TButton",
            background=CARD_BG,
            foreground=TEXT,
            bordercolor=BORDER,
            padding=(15, 9),
            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="white",
            borderwidth=0,
            padding=(28, 12),
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        style.map(
            "Accent.TButton",
            background=[
                (
                    "active",
                    ACCENT_HOVER
                ),
                (
                    "disabled",
                    "#C9B88D"
                )
            ]
        )

        style.configure(
            "Custom.TCheckbutton",
            background=CARD_BG,
            foreground=MUTED,
            font=(
                "Segoe UI",
                9
            )
        )

        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor="#EAE1D4",
            background=ACCENT
        )

    def create_card(
        self,
        parent
    ):
        card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            bd=0
        )

        card.pack(
            fill="x",
            pady=(0, 15)
        )

        inner = ttk.Frame(
            card,
            style="Card.TFrame",
            padding=17
        )

        inner.pack(
            fill="x"
        )

        return inner

    def create_widgets(self):
        container = ttk.Frame(
            self.root,
            style="Main.TFrame",
            padding=30
        )

        container.pack(
            fill="both",
            expand=True
        )

        # HEADER
        ttk.Label(
            container,
            text=(
                "DJI Thermal R-JPEG Converter"
            ),
            style="Title.TLabel"
        ).pack(
            anchor="w"
        )

        ttk.Label(
            container,
            text=(
                "Convert DJI radiometric images "
                "to Float32 temperature TIFF files."
            ),
            style="Subtitle.TLabel"
        ).pack(
            anchor="w",
            pady=(5, 26)
        )

        # INPUT
        input_card = self.create_card(
            container
        )

        ttk.Label(
            input_card,
            text="Input images",
            style="Section.TLabel"
        ).pack(
            anchor="w"
        )

        self.input_path_label = ttk.Label(
            input_card,
            text="No input selected",
            style="Muted.TLabel"
        )

        self.input_path_label.pack(
            anchor="w",
            pady=(5, 12)
        )

        input_row = ttk.Frame(
            input_card,
            style="Card.TFrame"
        )

        input_row.pack(
            anchor="w"
        )

        ttk.Button(
            input_row,
            text="Select images",
            style="Secondary.TButton",
            command=self.select_images
        ).pack(
            side="left",
            padx=(0, 10)
        )

        ttk.Button(
            input_row,
            text="Select folder",
            style="Secondary.TButton",
            command=self.select_folder
        ).pack(
            side="left"
        )

        ttk.Checkbutton(
            input_card,
            text=(
                "Overwrite existing TIFF files"
            ),
            variable=self.overwrite_existing,
            style="Custom.TCheckbutton"
        ).pack(
            anchor="w",
            pady=(10, 0)
        )

        self.input_status_label = ttk.Label(
            input_card,
            textvariable=self.input_status,
            style="Muted.TLabel"
        )

        self.input_status_label.pack(
            anchor="w",
            pady=(8, 0)
        )

        # OUTPUT
        output_card = self.create_card(
            container
        )

        ttk.Label(
            output_card,
            text="Output folder",
            style="Section.TLabel"
        ).pack(
            anchor="w"
        )

        ttk.Label(
            output_card,
            textvariable=self.output_path,
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(5, 12)
        )

        output_buttons = ttk.Frame(
            output_card,
            style="Card.TFrame"
        )

        output_buttons.pack(
            anchor="w"
        )

        ttk.Button(
            output_buttons,
            text="Change output folder",
            style="Secondary.TButton",
            command=self.select_output
        ).pack(
            side="left",
            padx=(0, 10)
        )

        self.open_output_button = ttk.Button(
            output_buttons,
            text="Open output folder",
            style="Secondary.TButton",
            command=self.open_output_folder,
            state="disabled"
        )

        self.open_output_button.pack(
            side="left"
        )

        self.output_status_label = ttk.Label(
            output_card,
            textvariable=self.output_status,
            style="Success.TLabel"
        )

        self.output_status_label.pack(
            anchor="w",
            pady=(10, 0)
        )

        # CONVERT
        self.convert_button = ttk.Button(
            container,
            text="Convert images",
            style="Accent.TButton",
            command=self.start_conversion
        )

        self.convert_button.pack(
            pady=(5, 18)
        )

        self.progress = ttk.Progressbar(
            container,
            mode="determinate",
            maximum=100,
            value=0,
            style=(
                "Custom.Horizontal.TProgressbar"
            )
        )

        self.progress.pack(
            fill="x",
            pady=(0, 8)
        )

        self.progress_percent = ttk.Label(
            container,
            text="0%",
            style="Status.TLabel"
        )

        self.progress_percent.pack()

        ttk.Label(
            container,
            textvariable=self.main_status,
            style="Status.TLabel"
        ).pack(
            pady=(5, 0)
        )

    def select_images(self):
        files = filedialog.askopenfilenames(
            title=(
                "Select DJI thermal images"
            ),
            filetypes=[
                (
                    "JPEG images",
                    "*.jpg *.jpeg *.JPG *.JPEG"
                )
            ]
        )

        if not files:
            return

        self.selected_files = [
            Path(path)
            for path in files
        ]

        self.input_folder = None
        self.selection_mode = "files"

        count = len(
            self.selected_files
        )

        if count == 1:
            self.input_path_label.config(
                text=str(
                    self.selected_files[0]
                )
            )

            self.input_status.set(
                "✓ 1 image selected"
            )

        else:
            self.input_path_label.config(
                text=str(
                    self.selected_files[0].parent
                )
            )

            self.input_status.set(
                f"✓ {count} images selected"
            )

        self.input_status_label.configure(
            style="Success.TLabel"
        )

    def select_folder(self):
        folder = filedialog.askdirectory(
            title=(
                "Select folder with DJI R-JPEG images"
            )
        )

        if not folder:
            return

        folder_path = Path(
            folder
        )

        files = [
            path
            for path in folder_path.iterdir()
            if path.is_file()
            and path.suffix.lower()
            in {".jpg", ".jpeg"}
        ]

        self.selected_files = []
        self.input_folder = folder_path
        self.selection_mode = "folder"

        self.input_path_label.config(
            text=str(folder_path)
        )

        if files:
            self.input_status.set(
                f"✓ Folder selected — "
                f"{len(files)} image(s) found"
            )

            self.input_status_label.configure(
                style="Success.TLabel"
            )

        else:
            self.input_status.set(
                "No JPG/JPEG images found"
            )

    def select_output(self):
        folder = filedialog.askdirectory(
            title="Select output folder",
            initialdir=str(
                self.default_output
            )
        )

        if not folder:
            return

        self.output_path.set(
            folder
        )

        self.output_status.set(
            "✓ Output folder selected"
        )

        self.last_output_dir = Path(
            folder
        )

        self.open_output_button.config(
            state="normal"
        )

    def open_output_folder(self):
        folder = self.last_output_dir

        if folder is None:
            folder = Path(
                self.output_path.get()
            )

        if not folder.exists():
            messagebox.showerror(
                "Output folder",
                (
                    "Output folder does not exist."
                )
            )
            return

        try:
            os.startfile(
                str(folder)
            )

        except Exception as exc:
            messagebox.showerror(
                "Open folder error",
                str(exc)
            )

    def start_conversion(self):
        if self.selection_mode is None:
            messagebox.showerror(
                "No input selected",
                (
                    "Select images or "
                    "an input folder first."
                )
            )
            return

        output_dir = (
            self.output_path
            .get()
            .strip()
        )

        if not output_dir:
            messagebox.showerror(
                "Output folder",
                "Select an output folder."
            )
            return

        if not self.default_dll.exists():
            messagebox.showerror(
                "DJI SDK",
                (
                    "DJI SDK library was not found:\n"
                    f"{self.default_dll}"
                )
            )
            return

        try:
            Path(output_dir).mkdir(
                parents=True,
                exist_ok=True
            )

        except OSError as exc:
            messagebox.showerror(
                "Output folder error",
                str(exc)
            )
            return

        policy = (
            "overwrite"
            if self.overwrite_existing.get()
            else "skip"
        )

        self.progress.configure(
            value=0
        )

        self.progress_percent.config(
            text="0%"
        )

        self.convert_button.config(
            state="disabled"
        )

        self.open_output_button.config(
            state="disabled"
        )

        self.main_status.set(
            "Starting conversion..."
        )

        thread = threading.Thread(
            target=self.run_conversion,
            args=(
                output_dir,
                policy
            ),
            daemon=True
        )

        thread.start()

    def run_conversion(
        self,
        output_dir,
        policy
    ):
        try:
            if self.selection_mode == "files":
                result = convert_images(
                    image_paths=self.selected_files,
                    output_dir=output_dir,
                    dll_path=self.default_dll,
                    progress_callback=(
                        self.progress_callback
                    ),
                    existing_policy=policy
                )

            else:
                result = convert_folder(
                    input_dir=self.input_folder,
                    output_dir=output_dir,
                    dll_path=self.default_dll,
                    progress_callback=(
                        self.progress_callback
                    ),
                    existing_policy=policy
                )

            self.root.after(
                0,
                self.set_validation_status
            )

            validation = validate_files(
                result["output_files"]
            )

            validation_report = (
                Path(output_dir)
                / "validation_report.csv"
            )

            save_validation_report(
                validation,
                validation_report
            )

            error_details = self.read_conversion_errors(
                result["report"]
            )

            self.root.after(
                0,
                self.conversion_success,
                result,
                validation,
                output_dir,
                error_details
            )

        except Exception as exc:
            self.root.after(
                0,
                self.conversion_error,
                str(exc)
            )

    def read_conversion_errors(
        self,
        report_path
    ):
        errors = []

        report_path = Path(
            report_path
        )

        if not report_path.exists():
            return errors

        try:
            with report_path.open(
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as csv_file:

                reader = csv.DictReader(
                    csv_file
                )

                for row in reader:
                    if row.get("status") != "ERROR":
                        continue

                    filename = row.get(
                        "filename",
                        "Unknown file"
                    )

                    error = row.get(
                        "error",
                        "Unknown error"
                    )

                    errors.append(
                        f"{filename}\n{error}"
                    )

        except Exception:
            pass

        return errors

    def set_validation_status(self):
        self.main_status.set(
            "Conversion complete — validating TIFF files..."
        )

    def progress_callback(
        self,
        current,
        total,
        success,
        errors,
        skipped
    ):
        if total <= 0:
            percent = 0

        else:
            percent = int(
                (current / total) * 100
            )

        self.root.after(
            0,
            self.update_progress,
            percent,
            current,
            total,
            success,
            errors,
            skipped
        )

    def update_progress(
        self,
        percent,
        current,
        total,
        success,
        errors,
        skipped
    ):
        self.progress.configure(
            value=percent
        )

        self.progress_percent.config(
            text=f"{percent}%"
        )

        self.main_status.set(
            f"{current} / {total}  •  "
            f"OK: {success}  •  "
            f"Errors: {errors}  •  "
            f"Skipped: {skipped}"
        )

    def conversion_success(
        self,
        result,
        validation,
        output_dir,
        error_details
    ):
        self.last_output_dir = Path(
            output_dir
        )

        self.progress.configure(
            value=100
        )

        self.progress_percent.config(
            text="100%"
        )

        self.convert_button.config(
            state="normal"
        )

        self.open_output_button.config(
            state="normal"
        )

        # Czytelny status pod paskiem.
        status_parts = [
            f"OK: {result['success']}",
            f"Errors: {result['errors']}",
            f"Validated: {validation['passed']}",
        ]

        if validation["warnings"] > 0:
            status_parts.append(
                f"Warnings: {validation['warnings']}"
            )

        if result["skipped"] > 0:
            status_parts.append(
                f"Skipped: {result['skipped']}"
            )

        if validation["failed"] > 0:
            status_parts.append(
                f"Validation errors: {validation['failed']}"
            )

        self.main_status.set(
            "✓ " + "  •  ".join(
                status_parts
            )
        )

        # Czytelny popup.
        message_lines = [
            f"Successfully converted: {result['success']}",
        ]

        if result["skipped"] > 0:
            message_lines.append(
                f"Skipped: {result['skipped']}"
            )

        if result["errors"] > 0:
            message_lines.append(
                f"Conversion errors: {result['errors']}"
            )

        message_lines.append("")

        if (
            validation["failed"] == 0
            and validation["warnings"] == 0
        ):
            message_lines.append(
                f"All {validation['passed']} TIFF file(s) "
                "passed validation."
            )

        elif validation["failed"] == 0:
            message_lines.append(
                f"Passed validation: {validation['passed']}"
            )

            message_lines.append(
                f"Passed with warnings: {validation['warnings']}"
            )

            message_lines.append(
                "Warnings do not prevent the TIFF files "
                "from being used."
            )

                else:
                    message_lines.append(
                        f"Validated successfully: {validation['passed']}"
                    )

                    message_lines.append(
                        f"Validation errors: {validation['failed']}"
                    )

        # Pokazujemy konkretne błędy konwersji.
        if error_details:
            message_lines.append("")
            message_lines.append(
                "Files with conversion errors:"
            )

            # Maksymalnie kilka pozycji, żeby popup
            # nie zrobił się ogromny.
            for error in error_details[:5]:
                message_lines.append("")
                message_lines.append(
                    error
                )

            if len(error_details) > 5:
                message_lines.append("")
                message_lines.append(
                    f"...and {len(error_details) - 5} more."
                )

        message_lines.append("")
        message_lines.append(
            f"Output folder:\n{output_dir}"
        )

        message = "\n".join(
            message_lines
        )

        if (
            result["errors"] == 0
            and validation["failed"] == 0
        ):
            messagebox.showinfo(
                "Conversion completed",
                message
            )

        else:
            messagebox.showwarning(
                "Conversion completed with warnings",
                message
            )

    def conversion_error(
        self,
        error_message
    ):
        self.convert_button.config(
            state="normal"
        )

        self.open_output_button.config(
            state="normal"
        )

        self.main_status.set(
            "Conversion failed"
        )

        messagebox.showerror(
            "Conversion error",
            error_message
        )


def main():
    root = tk.Tk()

    ConverterGUI(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()