import pytest
from src.backend.circuit_model import CircuitModel, Block
from src.renderer.circuit_renderer import CircuitRenderer

def test_renderer_initialization():
    renderer = CircuitRenderer()
    assert renderer.scene is not None
    assert renderer.scene.sceneRect().width() == 1200

def test_render_empty_model():
    renderer = CircuitRenderer()
    model = CircuitModel()
    scene = renderer.render(model)
    assert scene is not None
    assert len(renderer.block_items) == 0

def test_render_blocks():
    renderer = CircuitRenderer()
    model = CircuitModel()
    model.add_block(Block(id="reg_a", block_type="register", label="RegA", x=50, y=100, width=80, height=40))
    model.add_block(Block(id="alu_0", block_type="alu", label="ALU", x=200, y=100, width=100, height=60))
    scene = renderer.render(model)
    assert len(renderer.block_items) == 2
    assert "reg_a" in renderer.block_items
    assert "alu_0" in renderer.block_items

def test_get_scene():
    renderer = CircuitRenderer()
    scene = renderer.get_scene()
    assert scene is renderer.scene
