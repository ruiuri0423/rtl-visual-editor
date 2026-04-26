import pytest
from unittest.mock import patch, MagicMock
import json
from src.llm.llm_client import LLMClient, LayoutPlanner, LLMConfig, load_config


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_from_dict_full(self):
        data = {
            "api": {
                "key": "test-key",
                "base_url": "https://api.minimax.io/v1",
                "model": "MiniMax-M2.7",
                "timeout_ms": 5000,
            }
        }
        config = LLMConfig.from_dict(data)
        assert config.key == "test-key"
        assert config.base_url == "https://api.minimax.io/v1"
        assert config.model == "MiniMax-M2.7"
        assert config.timeout_ms == 5000

    def test_from_dict_partial(self):
        data = {"api": {"key": "test-key"}}
        config = LLMConfig.from_dict(data)
        assert config.key == "test-key"
        assert config.base_url == "https://api.minimax.io/v1"  # default
        assert config.model == "MiniMax-M2.7"  # default
        assert config.timeout_ms == 3000000  # default

    def test_from_dict_empty(self):
        data = {}
        config = LLMConfig.from_dict(data)
        assert config.key == ""
        assert config.base_url == "https://api.minimax.io/v1"


class TestLLMClient:
    """Tests for LLMClient."""

    @patch("src.llm.llm_client.load_config")
    def test_init_with_config(self, mock_load_config):
        mock_config = LLMConfig(key="test-key", base_url="https://api.minimax.io/v1")
        mock_load_config.return_value = mock_config

        client = LLMClient()
        assert client.config.key == "test-key"

    @patch("src.llm.llm_client.load_config")
    def test_init_without_config(self, mock_load_config):
        mock_load_config.return_value = None

        client = LLMClient(api_key="direct-key")
        assert client.config.key == "direct-key"

    @patch("src.llm.llm_client.load_config")
    def test_init_no_key_raises(self, mock_load_config):
        mock_load_config.return_value = None

        with pytest.raises(ValueError, match="API key is required"):
            LLMClient()

    @patch("src.llm.llm_client.load_config")
    @patch("openai.OpenAI")
    def test_generate(self, mock_openai_class, mock_load_config):
        mock_load_config.return_value = None
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text"

        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = LLMClient(api_key="test-key", base_url="https://api.minimax.io/v1")
        result = client.generate("Hello", system_prompt="You are helpful")

        assert result == "Generated text"
        mock_client_instance.chat.completions.create.assert_called_once()


class TestLayoutPlanner:
    """Tests for LayoutPlanner."""

    def test_build_prompt(self):
        planner = LayoutPlanner(api_key="test-key")
        circuit_json = '{"blocks": [], "wires": []}'
        prompt = planner.build_prompt(circuit_json, "timing info")
        assert "## 電路結構" in prompt
        assert "## 請產生區塊佈局" in prompt
        assert "timing info" in prompt

    def test_build_prompt_no_timing(self):
        planner = LayoutPlanner(api_key="test-key")
        circuit_json = '{"blocks": [], "wires": []}'
        prompt = planner.build_prompt(circuit_json, "")
        assert "（無時序資訊）" in prompt

    @patch.object(LLMClient, "generate")
    def test_generate_layout(self, mock_generate):
        mock_generate.return_value = json.dumps({
            "blocks": [
                {"id": "reg_a", "type": "register", "label": "RegA", "bits": 8, "x": 50, "y": 100, "width": 80, "height": 40, "ports": []}
            ],
            "wires": []
        })

        planner = LayoutPlanner(api_key="test-key")
        circuit_json = '{"blocks": [], "wires": []}'
        result = planner.generate_layout(circuit_json, "")

        assert "blocks" in result
        assert len(result["blocks"]) == 1
        assert result["blocks"][0]["id"] == "reg_a"

    def test_parse_llm_response(self):
        planner = LayoutPlanner(api_key="test-key")
        response = {
            "blocks": [{"id": "alu", "type": "alu", "label": "ALU", "bits": 8, "x": 200, "y": 100, "width": 100, "height": 60, "ports": []}],
            "wires": []
        }
        model = planner.parse_llm_response(response)
        assert "alu" in model.blocks
        assert model.blocks["alu"].x == 200


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_missing_file(self, tmp_path):
        result = load_config(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_load_config_no_key(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text('{"api": {"key": ""}}')

        result = load_config(str(config_file))
        assert result is None

    def test_load_config_valid(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text('{"api": {"key": "valid-key", "base_url": "https://api.minimax.io/v1", "model": "MiniMax-M2.7"}}')

        result = load_config(str(config_file))
        assert result is not None
        assert result.key == "valid-key"
