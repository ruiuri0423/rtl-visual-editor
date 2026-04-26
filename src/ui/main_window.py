from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter, QGraphicsView,
    QGraphicsScene, QVBoxLayout, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter

from .input_panel import InputPanel
from .properties_panel import PropertiesPanel
from .export_panel import ExportPanel
from ..backend.rtl_parser import RtlParser
from ..backend.timing_reasoner import TimingReasoner
from ..llm.layout_planner import LayoutPlanner
from ..renderer.circuit_renderer import CircuitRenderer


class MainWindow(QMainWindow):
    parse_requested = pyqtSignal(str)

    def __init__(self, api_key: str = ""):
        super().__init__()
        self.setWindowTitle("RTL Visual Editor")
        self.setGeometry(100, 100, 1400, 900)

        self.api_key = api_key
        self.circuit_renderer = CircuitRenderer()
        self.current_model = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left: Input panel
        self.input_panel = InputPanel()
        self.input_panel.parse_requested.connect(self._on_parse_requested)
        main_layout.addWidget(self.input_panel, 1)

        # Right: circuit view + panels
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Circuit GraphicsView
        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graphics_view.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate
        )
        self._update_graphics_view_scene()

        self.properties_panel = PropertiesPanel()
        self.export_panel = ExportPanel()
        self.export_panel.export_rtl_btn.clicked.connect(self._on_export_rtl)
        self.export_panel.export_png_btn.clicked.connect(self._on_export_png)
        self.export_panel.export_pdf_btn.clicked.connect(self._on_export_pdf)

        right_splitter.addWidget(self.graphics_view)
        right_splitter.addWidget(self.properties_panel)
        right_splitter.addWidget(self.export_panel)
        right_splitter.setSizes([600, 150, 150])

        main_layout.addWidget(right_splitter, 2)

        self._create_menu()

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        view_menu = menubar.addMenu("View")
        export_menu = menubar.addMenu("Export")
        help_menu = menubar.addMenu("Help")

    def _update_graphics_view_scene(self):
        self.graphics_view.setScene(self.circuit_renderer.get_scene())

    def _on_parse_requested(self, rtl_code: str):
        try:
            # Parse RTL
            parser = RtlParser()
            model = parser.parse(rtl_code)

            if not model.blocks:
                QMessageBox.warning(
                    self, "Parse Error",
                    "No circuit blocks found in the RTL code.\nPlease check the syntax."
                )
                return

            self.current_model = model

            # Generate timing info for prompt
            reasoner = TimingReasoner()
            timing_info = reasoner.generate_promptSupplement(model)

            # Try LLM layout, fallback to auto-layout if LLM fails
            self._generate_layout_with_llm(model, timing_info)

            # Render
            self.circuit_renderer.render(model)
            self._update_graphics_view_scene()

            # Update export panel
            from ..backend.rtl_exporter import RtlExporter
            exporter = RtlExporter()
            rtl_output = exporter.export(model)
            self.export_panel.set_preview(rtl_output)

            QMessageBox.information(
                self, "Success",
                f"Parsed {len(model.blocks)} blocks, {len(model.wires)} wires"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse RTL:\n{str(e)}")

    def _generate_layout_with_llm(self, model, timing_info: str):
        try:
            planner = LayoutPlanner(api_key=self.api_key)
            layout_model = planner.generate_with_retry(model)
            # Copy layout coordinates back to original model
            for bid, block in layout_model.blocks.items():
                if bid in model.blocks:
                    model.blocks[bid].x = block.x
                    model.blocks[bid].y = block.y
                    model.blocks[bid].width = block.width
                    model.blocks[bid].height = block.height
            model.wires = layout_model.wires
        except ValueError as e:
            # No API key configured, use auto-layout
            self._auto_layout(model)
        except Exception as e:
            QMessageBox.warning(
                self, "LLM Layout Failed",
                f"Could not generate layout with LLM:\n{str(e)}\nUsing auto-layout instead."
            )
            self._auto_layout(model)

    def _auto_layout(self, model):
        """Simple auto-layout without LLM."""
        x = 50
        y = 50
        max_y = 0
        col_width = 150
        row_height = 100

        for bid, block in model.blocks.items():
            block.x = x
            block.y = y
            block.width = 100
            block.height = 60
            y += row_height
            max_y = max(max_y, y)
            if y > 600:
                y = 50
                x += col_width

        # Auto-wire from input ports through sequential blocks to output ports
        from ..backend.circuit_model import Wire
        model.wires = []
        prev_block = None
        for bid, block in model.blocks.items():
            if prev_block and block.block_type not in ["input_port"]:
                model.wires.append(Wire(
                    from_port=f"{prev_block}.Q",
                    to_port=f"{block.id}.D" if block.block_type == "register" else f"{block.id}.A"
                ))
            if block.block_type == "register":
                prev_block = block.id

    def _on_export_rtl(self):
        if not self.current_model:
            QMessageBox.warning(self, "No Data", "No circuit to export.")
            return
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Export RTL", "", "Verilog Files (*.v);;All Files (*)"
        )
        if path:
            from ..backend.rtl_exporter import RtlExporter
            exporter = RtlExporter()
            code = exporter.export(self.current_model)
            with open(path, "w") as f:
                f.write(code)

    def _on_export_png(self):
        if not self.current_model:
            QMessageBox.warning(self, "No Data", "No circuit to export.")
            return
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtGui import QPixmap
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", "", "PNG Files (*.png);;All Files (*)"
        )
        if path:
            pixmap = self.graphics_view.grab()
            pixmap.save(path)

    def _on_export_pdf(self):
        if not self.current_model:
            QMessageBox.warning(self, "No Data", "No circuit to export.")
            return
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if path:
            pixmap = self.graphics_view.grab()
            pixmap.save(path)
