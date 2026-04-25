from PyQt6.QtWidgets import QGraphicsPolygonItem, QGraphicsTextItem
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPolygonF, QPen, QBrush, QColor

BLOCK_COLORS = {
    "register": "#4FC3F7",
    "alu": "#FFB74D",
    "mux": "#81C784",
    "counter": "#CE93D8",
    "ram": "#F48FB1",
    "decoder": "#90CAF9",
    "encoder": "#A5D6A7",
    "wire": "#BDBDBD",
    "input_port": "#66BB6A",
    "output_port": "#EF5350",
    "gnd": "#212121",
    "vcc": "#F44336",
    "submodule": "#B0BEC5",
    "default": "#90A4AE",
}

class BlockItem(QGraphicsPolygonItem):
    def __init__(self, block_id: str, block_type: str, label: str, x: float, y: float, width: float, height: float):
        super().__init__()
        self.block_id = block_id
        self.block_type = block_type
        self.label = label
        self.setPos(QPointF(x, y))
        self.setFlag(QGraphicsPolygonItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsPolygonItem.GraphicsItemFlag.ItemIsMovable, True)

        polygon = QPolygonF([
            QPointF(0, 0),
            QPointF(width, 0),
            QPointF(width, height),
            QPointF(0, height),
        ])
        self.setPolygon(polygon)

        color = QColor(BLOCK_COLORS.get(block_type, BLOCK_COLORS["default"]))
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#37474F"), 2))

        # Add label
        self.label_item = QGraphicsTextItem(label, self)
        self.label_item.setDefaultTextColor(QColor("#FFFFFF"))
        self.label_item.setPos(4, 4)
