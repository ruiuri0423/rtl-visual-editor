import pytest
from src.ui.main_window import MainWindow
from src.ui.input_panel import InputPanel
from src.ui.properties_panel import PropertiesPanel
from src.ui.export_panel import ExportPanel

def test_main_window_creation():
    window = MainWindow()
    assert window.windowTitle() == "RTL Visual Editor"

def test_input_panel_creation():
    panel = InputPanel()
    assert panel.parse_btn.text() == "Parse & Generate"

def test_properties_panel_show():
    panel = PropertiesPanel()
    panel.show_properties("reg_a", {"bits": 8, "type": "register"})

def test_export_panel_creation():
    panel = ExportPanel()
    assert panel.export_rtl_btn.text() == "Export RTL..."
    assert panel.export_png_btn.text() == "Export PNG..."
    assert panel.export_pdf_btn.text() == "Export PDF..."

def test_export_panel_preview():
    panel = ExportPanel()
    panel.set_preview("module test; endmodule")
    assert "module test" in panel.preview.toPlainText()