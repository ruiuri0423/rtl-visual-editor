import pytest
from unittest.mock import patch, MagicMock
from src.backend.circuit_model import CircuitModel, Block
from src.llm.layout_planner import LayoutPlanner

def test_build_prompt():
    planner = LayoutPlanner(api_key="test-key")
    model = CircuitModel()
    model.add_block(Block(id="reg_a", block_type="register", label="RegA", bits=8))
    prompt = planner.build_prompt(model, "")
    assert "reg_a" in prompt
    assert "JSON" in prompt

def test_parse_llm_response():
    planner = LayoutPlanner(api_key="test-key")
    response_json = {
        "blocks": [
            {"id": "reg_a", "type": "register", "label": "RegA", "bits": 8, "x": 50, "y": 100, "width": 80, "height": 40, "ports": []}
        ],
        "wires": []
    }
    model = planner.parse_llm_response(response_json)
    assert "reg_a" in model.blocks
    assert model.blocks["reg_a"].x == 50
    assert model.blocks["reg_a"].y == 100

def test_build_prompt_with_timing():
    planner = LayoutPlanner(api_key="test-key")
    model = CircuitModel()
    model.add_block(Block(id="reg_a", block_type="register", label="RegA", bits=8))
    prompt = planner.build_prompt(model, "## 時序資訊\n- 時脈: clk")
    assert "時序資訊" in prompt
    assert "clk" in prompt

def test_default_model():
    planner = LayoutPlanner(api_key="test-key")
    assert planner.model == "gpt-4o"

@patch('src.llm.layout_planner.OpenAI')
def test_generate_layout_calls_api(mock_openai):
    # Mock the OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"blocks":[],"wires":[]}'
    mock_client.chat.completions.create.return_value = mock_response

    planner = LayoutPlanner(api_key="test-key")
    model = CircuitModel()
    model.add_block(Block(id="reg_a", block_type="register", label="RegA", bits=8))

    result = planner.generate_layout(model, "")
    mock_client.chat.completions.create.assert_called_once()
