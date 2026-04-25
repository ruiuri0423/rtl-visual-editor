from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QFormLayout, QScrollArea
from PyQt6.QtCore import Qt

class PropertiesPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Properties"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(150)

        self.content_widget = QWidget()
        self.form_layout = QFormLayout()
        self.content_widget.setLayout(self.form_layout)
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

    def show_properties(self, block_id: str, properties: dict):
        # Clear existing form
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for key, value in properties.items():
            edit = QLineEdit(str(value))
            edit.setReadOnly(True)
            self.form_layout.addRow(key, edit)