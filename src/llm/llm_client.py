import json
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM API connection."""
    key: str
    base_url: str = "https://api.minimax.io/v1"
    model: str = "MiniMax-M2.7"
    timeout_ms: int = 3000000

    @classmethod
    def from_dict(cls, data: dict) -> "LLMConfig":
        api = data.get("api", {})
        return cls(
            key=api.get("key", ""),
            base_url=api.get("base_url", "https://api.minimax.io/v1"),
            model=api.get("model", "MiniMax-M2.7"),
            timeout_ms=api.get("timeout_ms", 3000000),
        )


def load_config(config_path: Optional[str] = None) -> Optional[LLMConfig]:
    """Load LLM configuration from JSON file.

    Args:
        config_path: Path to config.json. If None, looks in project root.

    Returns:
        LLMConfig object if config file exists and has valid key, None otherwise.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config.json"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        return None

    with open(config_path, "r") as f:
        data = json.load(f)

    config = LLMConfig.from_dict(data)

    if not config.key:
        return None

    return config


class LLMClient:
    """LLM API client for generating circuit layouts.

    Supports OpenAI-compatible API endpoints (including MiniMax).
    """

    def __init__(self, config: Optional[LLMConfig] = None, api_key: str = "", base_url: str = "", model: str = ""):
        """Initialize LLM client.

        Args:
            config: LLMConfig object. If provided, other params are ignored.
            api_key: API key (used if config is None)
            base_url: API base URL (used if config is None)
            model: Model name (used if config is None)
        """
        if config is None:
            loaded = load_config()
            if loaded is not None:
                config = loaded

        if config is not None:
            self.config = config
        else:
            self.config = LLMConfig(key=api_key, base_url=base_url or "https://api.minimax.io/v1", model=model or "MiniMax-M2.7")

        if not self.config.key:
            raise ValueError("API key is required. Set it in config.json or pass api_key parameter.")

        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.key,
                base_url=self.config.base_url,
                timeout=self.config.timeout_ms / 1000,
            )
        return self._client

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate completion from LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)

        Returns:
            Generated text content
        """
        from openai import OpenAI

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=0.3,
        )

        return response.choices[0].message.content


# Default system prompt for circuit layout
DEFAULT_SYSTEM_PROMPT = """你是一個數位電路架構專家。請根據以下電路結構描述，產生區塊佈局規劃。

## 約束條件
1. 輸入埠放在左側，輸出埠放在右側
2. 資料流向從左到右
3. 時序相關的區塊（如暫存器）應相鄰擺放
4. 每個區塊需要有 x, y 座標（單位：像素，檢視區域 1200x800）
5. 輸出區塊需要有適當的宽度和高度

## 輸出格式
只輸出 JSON，不可摻雜其他文字：
{
  "blocks": [...],
  "wires": [...]
}
"""


class LayoutPlanner:
    """Plans circuit block layout using LLM."""

    DEFAULT_USER_PROMPT_TEMPLATE = """## 電路結構
{block_json}

{timing_info}

## 請產生區塊佈局（JSON格式）
"""

    def __init__(self, config: Optional[LLMConfig] = None, api_key: str = "", base_url: str = "", model: str = ""):
        self.llm_client = LLMClient(config=config, api_key=api_key, base_url=base_url, model=model)
        self.timing_reasoner = None  # Will be set if needed

    def build_prompt(self, circuit_json: str, timing_info: str = "") -> str:
        """Build user prompt for layout generation."""
        timing = timing_info if timing_info else "（無時序資訊）"
        return self.DEFAULT_USER_PROMPT_TEMPLATE.format(
            block_json=circuit_json,
            timing_info=timing
        )

    def generate_layout(self, circuit_json: str, timing_info: str = "", system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> dict:
        """Generate layout from circuit JSON.

        Args:
            circuit_json: JSON string of circuit model
            timing_info: Timing information string (optional)
            system_prompt: System prompt (optional)

        Returns:
            Parsed JSON response from LLM
        """
        prompt = self.build_prompt(circuit_json, timing_info)
        response_text = self.llm_client.generate(prompt, system_prompt)
        return json.loads(response_text)

    def parse_llm_response(self, response: dict) -> "CircuitModel":
        """Parse LLM JSON response into CircuitModel."""
        from src.backend.circuit_model import CircuitModel
        return CircuitModel.from_json(response)

    def generate_with_retry(self, circuit_json: str, timing_info: str = "", max_retries: int = 3) -> "CircuitModel":
        """Generate layout with retry logic.

        Args:
            circuit_json: JSON string of circuit model
            timing_info: Timing information string (optional)
            max_retries: Maximum number of retry attempts

        Returns:
            CircuitModel with layout coordinates
        """
        from src.backend.timing_reasoner import TimingReasoner

        if self.timing_reasoner is None:
            self.timing_reasoner = TimingReasoner()

        if not timing_info:
            timing_info = self.timing_reasoner.generate_promptSupplement(self._get_circuit_model_for_timing(circuit_json))

        for attempt in range(max_retries):
            try:
                response = self.generate_layout(circuit_json, timing_info)
                return self.parse_llm_response(response)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                continue

    def _get_circuit_model_for_timing(self, circuit_json: str) -> "CircuitModel":
        """Helper to create CircuitModel from JSON string for timing reasoner."""
        from src.backend.circuit_model import CircuitModel
        return CircuitModel.from_json(json.loads(circuit_json))
