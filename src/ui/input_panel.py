from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog, QLabel
from PyQt6.QtCore import pyqtSignal

class InputPanel(QWidget):
    parse_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.setMaximumWidth(400)

        label = QLabel("RTL Code Input")
        layout.addWidget(label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste Verilog RTL code here...")
        layout.addWidget(self.text_edit)

        load_btn = QPushButton("Load File")
        load_btn.clicked.connect(self._on_load_file)
        layout.addWidget(load_btn)

        self.parse_btn = QPushButton("Parse & Generate")
        self.parse_btn.clicked.connect(self._on_parse)
        layout.addWidget(self.parse_btn)

        layout.addStretch()

    def _on_load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Verilog File", "", "Verilog Files (*.v *.sv);;All Files (*)")
        if path:
            with open(path, "r") as f:
                self.text_edit.setText(f.read())

    def _on_parse(self):
        text = self.text_edit.toPlainText()
        if text.strip():
            self.parse_requested.emit(text)