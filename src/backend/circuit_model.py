from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Port:
    name: str
    direction: str  # "in" or "out"
    offset: int = 0

@dataclass
class Block:
    id: str
    block_type: str
    label: str
    bits: int = 0
    x: float = 0.0
    y: float = 0.0
    width: float = 80.0
    height: float = 40.0
    ports: List[Port] = field(default_factory=list)
    properties: Dict = field(default_factory=dict)

@dataclass
class Wire:
    from_port: str
    to_port: str
    label: str = ""

@dataclass
class CircuitModel:
    blocks: Dict[str, Block] = field(default_factory=dict)
    wires: List[Wire] = field(default_factory=list)
    module_name: str = ""

    def add_block(self, block: Block) -> None:
        self.blocks[block.id] = block

    def add_wire(self, wire: Wire) -> None:
        self.wires.append(wire)

    def to_json(self) -> dict:
        return {
            "blocks": [
                {
                    "id": b.id,
                    "type": b.block_type,
                    "label": b.label,
                    "bits": b.bits,
                    "x": b.x,
                    "y": b.y,
                    "width": b.width,
                    "height": b.height,
                    "ports": [{"name": p.name, "direction": p.direction, "offset": p.offset} for p in b.ports]
                } for b in self.blocks.values()
            ],
            "wires": [{"from": w.from_port, "to": w.to_port, "label": w.label} for w in self.wires]
        }

    @classmethod
    def from_json(cls, data: dict) -> "CircuitModel":
        model = cls()
        for b in data.get("blocks", []):
            block = Block(
                id=b["id"],
                block_type=b["type"],
                label=b["label"],
                bits=b.get("bits", 0),
                x=b.get("x", 0),
                y=b.get("y", 0),
                width=b.get("width", 80),
                height=b.get("height", 40),
                ports=[Port(name=p["name"], direction=p["direction"], offset=p.get("offset", 0)) for p in b.get("ports", [])],
            )
            model.add_block(block)
        for w in data.get("wires", []):
            model.add_wire(Wire(from_port=w["from"], to_port=w["to"], label=w.get("label", "")))
        return model