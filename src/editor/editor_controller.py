from typing import Optional
from src.backend.circuit_model import CircuitModel, Block, Wire

class EditorController:
    def __init__(self, model: CircuitModel):
        self.model = model
        self._dirty = False

    def add_block(self, block: Block) -> None:
        self.model.add_block(block)
        self._dirty = True

    def remove_block(self, block_id: str) -> None:
        if block_id in self.model.blocks:
            del self.model.blocks[block_id]
            # Remove connected wires
            self.model.wires = [
                w for w in self.model.wires
                if not w.from_port.startswith(block_id + ".") and not w.to_port.startswith(block_id + ".")
            ]
            self._dirty = True

    def add_wire(self, wire: Wire) -> None:
        self.model.add_wire(wire)
        self._dirty = True

    def remove_wire(self, from_port: str, to_port: str) -> None:
        self.model.wires = [
            w for w in self.model.wires
            if not (w.from_port == from_port and w.to_port == to_port)
        ]
        self._dirty = True

    def update_block_position(self, block_id: str, x: float, y: float) -> None:
        if block_id in self.model.blocks:
            self.model.blocks[block_id].x = x
            self.model.blocks[block_id].y = y
            self._dirty = True

    def update_block_property(self, block_id: str, key: str, value) -> None:
        if block_id in self.model.blocks:
            self.model.blocks[block_id].properties[key] = value
            self._dirty = True

    def get_block(self, block_id: str) -> Optional[Block]:
        return self.model.blocks.get(block_id)

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        self._dirty = False