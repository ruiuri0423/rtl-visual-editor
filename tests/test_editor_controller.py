import pytest
from src.backend.circuit_model import CircuitModel, Block, Wire
from src.editor.editor_controller import EditorController

def test_add_block():
    model = CircuitModel()
    controller = EditorController(model)
    block = Block(id="alu_0", block_type="alu", label="ALU", bits=8)
    controller.add_block(block)
    assert "alu_0" in model.blocks
    assert controller.is_dirty is True

def test_remove_block():
    model = CircuitModel()
    model.add_block(Block(id="reg_a", block_type="register", label="RegA", bits=8))
    controller = EditorController(model)
    controller.remove_block("reg_a")
    assert "reg_a" not in model.blocks

def test_remove_block_removes_connected_wires():
    model = CircuitModel()
    model.add_block(Block(id="reg_a", block_type="register", label="RegA", bits=8))
    model.add_block(Block(id="alu_0", block_type="alu", label="ALU", bits=8))
    model.add_wire(Wire(from_port="reg_a.Q", to_port="alu_0.A"))
    controller = EditorController(model)
    controller.remove_block("reg_a")
    assert len(model.wires) == 0

def test_add_wire():
    model = CircuitModel()
    controller = EditorController(model)
    wire = Wire(from_port="reg_a.Q", to_port="alu_0.A")
    controller.add_wire(wire)
    assert len(model.wires) == 1

def test_remove_wire():
    model = CircuitModel()
    model.add_wire(Wire(from_port="reg_a.Q", to_port="alu_0.A"))
    controller = EditorController(model)
    controller.remove_wire("reg_a.Q", "alu_0.A")
    assert len(model.wires) == 0

def test_update_block_position():
    model = CircuitModel()
    model.add_block(Block(id="alu_0", block_type="alu", label="ALU", bits=8))
    controller = EditorController(model)
    controller.update_block_position("alu_0", 100, 200)
    assert model.blocks["alu_0"].x == 100
    assert model.blocks["alu_0"].y == 200

def test_update_block_property():
    model = CircuitModel()
    model.add_block(Block(id="alu_0", block_type="alu", label="ALU", bits=8))
    controller = EditorController(model)
    controller.update_block_property("alu_0", "operation", "sub")
    assert model.blocks["alu_0"].properties["operation"] == "sub"

def test_get_block():
    model = CircuitModel()
    model.add_block(Block(id="alu_0", block_type="alu", label="ALU", bits=8))
    controller = EditorController(model)
    block = controller.get_block("alu_0")
    assert block is not None
    assert block.id == "alu_0"

def test_is_dirty_flag():
    model = CircuitModel()
    controller = EditorController(model)
    assert controller.is_dirty is False
    controller.add_block(Block(id="alu_0", block_type="alu", label="ALU", bits=8))
    assert controller.is_dirty is True

def test_mark_clean():
    model = CircuitModel()
    controller = EditorController(model)
    controller.add_block(Block(id="alu_0", block_type="alu", label="ALU", bits=8))
    controller.mark_clean()
    assert controller.is_dirty is False