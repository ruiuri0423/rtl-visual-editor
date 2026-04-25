from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel

class ExportPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Export"))

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(150)
        layout.addWidget(self.preview)

        self.export_rtl_btn = QPushButton("Export RTL...")
        self.export_png_btn = QPushButton("Export PNG...")
        self.export_pdf_btn = QPushButton("Export PDF...")
        layout.addWidget(self.export_rtl_btn)
        layout.addWidget(self.export_png_btn)
        layout.addWidget(self.export_pdf_btn)
        layout.addStretch()

    def set_preview(self, code: str):
        self.preview.setText(code)