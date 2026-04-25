from PyQt6.QtWidgets import QGraphicsScene
from src.backend.circuit_model import CircuitModel
from .block_item import BlockItem
from .wire_item import WireItem

class CircuitRenderer:
    def __init__(self):
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 1200, 800)
        self.block_items = {}
        self.wire_items = []

    def render(self, model: CircuitModel) -> QGraphicsScene:
        self.scene.clear()
        self.block_items = {}
        self.wire_items = []

        # Render blocks
        for block in model.blocks.values():
            item = BlockItem(
                block_id=block.id,
                block_type=block.block_type,
                label=block.label,
                x=block.x,
                y=block.y,
                width=block.width,
                height=block.height,
            )
            self.scene.addItem(item)
            self.block_items[block.id] = item

        # Render wires
        for wire in model.wires:
            from_block = wire.from_port.split(".")[0]
            to_block = wire.to_port.split(".")[0]
            from_item = self.block_items.get(from_block)
            to_item = self.block_items.get(to_block)
            if from_item and to_item:
                x1 = from_item.x() + from_item.boundingRect().width()
                y1 = from_item.y() + from_item.boundingRect().height() / 2
                x2 = to_item.x()
                y2 = to_item.y() + to_item.boundingRect().height() / 2
                wire_item = WireItem(x1, y1, x2, y2, wire.label)
                self.scene.addItem(wire_item)
                self.wire_items.append(wire_item)

        return self.scene

    def get_scene(self) -> QGraphicsScene:
        return self.scene
