import sys
import os
import argparse
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    parser = argparse.ArgumentParser(description="RTL Visual Editor")
    parser.add_argument("--api-key", "-k", default="", help="OpenAI API key")
    parser.add_argument("--file", "-f", help="Load Verilog file on startup")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow(api_key=args.api_key or os.environ.get("OPENAI_API_KEY", ""))

    if args.file:
        with open(args.file, "r") as f:
            rtl_code = f.read()
        window.input_panel.text_edit.setText(rtl_code)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
