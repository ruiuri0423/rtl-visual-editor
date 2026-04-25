import pytest
from src.backend.circuit_model import CircuitModel, Block, Wire, Port

def test_block_creation():
    block = Block(id="reg_a", block_type="register", label="RegA", bits=8)
    assert block.id == "reg_a"
    assert block.block_type == "register"
    assert block.bits == 8

def test_port_direction():
    port_in = Port(name="D", direction="in", offset=0)
    port_out = Port(name="Q", direction="out", offset=0)
    assert port_in.direction == "in"
    assert port_out.direction == "out"

def test_wire_connection():
    wire = Wire(from_port="reg_a.Q", to_port="alu_0.A")
    assert wire.from_port == "reg_a.Q"
    assert wire.to_port == "alu_0.A"

def test_circuit_model_add_block():
    model = CircuitModel()
    block = Block(id="alu_0", block_type="alu", label="ALU", bits=8, x=200, y=100)
    model.add_block(block)
    assert "alu_0" in model.blocks
    assert model.blocks["alu_0"].label == "ALU"

def test_circuit_model_add_wire():
    model = CircuitModel()
    model.add_wire(Wire(from_port="reg_a.Q", to_port="alu_0.A"))
    assert len(model.wires) == 1
    assert model.wires[0].from_port == "reg_a.Q"

def test_circuit_model_to_json():
    model = CircuitModel()
    model.add_block(Block(id="reg_a", block_type="register", label="RegA", bits=8, x=50, y=100))
    json_data = model.to_json()
    assert "blocks" in json_data
    assert len(json_data["blocks"]) == 1
    assert json_data["blocks"][0]["id"] == "reg_a"

def test_circuit_model_from_json():
    data = {
        "blocks": [
            {"id": "reg_a", "type": "register", "label": "RegA", "bits": 8, "x": 50, "y": 100, "width": 80, "height": 40, "ports": []}
        ],
        "wires": []
    }
    model = CircuitModel.from_json(data)
    assert "reg_a" in model.blocks
    assert model.blocks["reg_a"].block_type == "register"