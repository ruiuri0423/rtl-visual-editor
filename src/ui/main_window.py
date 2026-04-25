from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal

class MainWindow(QMainWindow):
    parse_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RTL Visual Editor")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left: Input panel
        from .input_panel import InputPanel
        self.input_panel = InputPanel()
        self.input_panel.parse_requested.connect(self._on_parse_requested)
        main_layout.addWidget(self.input_panel, 1)

        # Right: placeholder for circuit view + panels
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.properties_panel = self._create_properties_panel()
        self.export_panel = self._create_export_panel()
        right_splitter.addWidget(self.properties_panel)
        right_splitter.addWidget(self.export_panel)
        main_layout.addWidget(right_splitter, 2)

        self._create_menu()

    def _create_properties_panel(self):
        from .properties_panel import PropertiesPanel
        return PropertiesPanel()

    def _create_export_panel(self):
        from .export_panel import ExportPanel
        return ExportPanel()

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        view_menu = menubar.addMenu("View")
        export_menu = menubar.addMenu("Export")
        help_menu = menubar.addMenu("Help")

    def _on_parse_requested(self, rtl_code: str):
        self.parse_requested.emit(rtl_code)