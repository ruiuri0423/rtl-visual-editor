import logging
from pathlib import Path
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


def setup_logging():
    """設定 logging，輸出到 log 檔"""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "gui.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


class MainWindow(QMainWindow):
    parse_requested = pyqtSignal(str)

    def __init__(self, api_key: str = ""):
        super().__init__()
        self.logger = setup_logging()
        self.logger.info("MainWindow 初始化")

        self.setWindowTitle("RTL Visual Editor")
        self.setGeometry(100, 100, 1400, 900)

        self.api_key = api_key
        self.logger.info(f"API key 已設定: {'Yes' if api_key else 'No (將從 config.json 讀取)'}")
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
        self.export_panel.show_circuit_btn.clicked.connect(self._on_show_circuit_model)

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
        self.logger.info("=== 開始解析 RTL ===")
        try:
            # Parse RTL
            self.logger.info("步驟 1/5: 解析 RTL 程式碼...")
            parser = RtlParser()
            model = parser.parse(rtl_code)
            self.logger.info(f"步驟 1 完成: 找到 {len(model.blocks)} 個區塊, {len(model.wires)} 條連線")

            if not model.blocks:
                QMessageBox.warning(
                    self, "Parse Error",
                    "No circuit blocks found in the RTL code.\nPlease check the syntax."
                )
                return

            self.current_model = model

            # Generate timing info for prompt
            self.logger.info("步驟 2/5: 產生時序資訊...")
            reasoner = TimingReasoner()
            timing_info = reasoner.generate_promptSupplement(model)
            self.logger.info(f"步驟 2 完成: {len(timing_info)} 字元時序資訊")

            # Try LLM layout, fallback to auto-layout if LLM fails
            self.logger.info("步驟 3/5: 嘗試 LLM 布局...")
            self._generate_layout_with_llm(model, timing_info)
            self.logger.info("步驟 3 完成")

            # Render
            self.logger.info("步驟 4/5: 渲染電路圖...")
            self.circuit_renderer.render(model)
            self._update_graphics_view_scene()
            self.logger.info("步驟 4 完成")

            # Update export panel
            self.logger.info("步驟 5/5: 產生 RTL 輸出...")
            from ..backend.rtl_exporter import RtlExporter
            exporter = RtlExporter()
            rtl_output = exporter.export(model)
            self.export_panel.set_preview(rtl_output)
            self.logger.info("步驟 5 完成")

            self.logger.info(f"=== RTL 解析完成: {len(model.blocks)} 區塊, {len(model.wires)} 連線 ===")
            QMessageBox.information(
                self, "Success",
                f"Parsed {len(model.blocks)} blocks, {len(model.wires)} wires"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse RTL:\n{str(e)}")

    def _generate_layout_with_llm(self, model, timing_info: str):
        self.logger.info("建立 LayoutPlanner 連線...")
        try:
            planner = LayoutPlanner(api_key=self.api_key)
            self.logger.info("LayoutPlanner 建立成功，呼叫 generate_with_retry...")
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
            self.logger.warning(f"ValueError: {e} — 降級到 auto-layout")
            self._auto_layout(model)
        except Exception as e:
            self.logger.error(f"LLM 布局失敗: {e} — 降級到 auto-layout")
            QMessageBox.warning(
                self, "LLM Layout Failed",
                f"Could not generate layout with LLM:\n{str(e)}\nUsing auto-layout instead."
            )
            self._auto_layout(model)

    def _auto_layout(self, model):
        """Simple auto-layout without LLM."""
        self.logger.info("執行 auto-layout...")
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
        self.logger.info("點擊 Export RTL 按鈕")
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
        self.logger.info("點擊 Export PNG 按鈕")
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
            self.logger.info(f"PNG 已匯出: {path}")

    def _on_export_pdf(self):
        self.logger.info("點擊 Export PDF 按鈕")
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
            self.logger.info(f"PDF 已匯出: {path}")

    def _on_show_circuit_model(self):
        self.logger.info("點擊 Show Circuit Model 按鈕")
        if not self.current_model:
            QMessageBox.warning(self, "No Data", "No circuit to show.")
            return
        import json
        circuit_json = json.dumps(self.current_model.to_json(), indent=2, ensure_ascii=False)
        self.export_panel.set_circuit_model(circuit_json)
        self.logger.info(f"Circuit model 已顯示: {len(self.current_model.blocks)} 區塊, {len(self.current_model.wires)} 連線")
