from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsTextItem
from PyQt6.QtGui import QPen, QColor

class WireItem(QGraphicsLineItem):
    def __init__(self, x1: float, y1: float, x2: float, y2: float, label: str = ""):
        super().__init__(x1, y1, x2, y2)
        self.label = label
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(QPen(QColor("#455A64"), 2))

        if label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            self.label_item = QGraphicsTextItem(label, self)
            self.label_item.setPos(mid_x, mid_y)
