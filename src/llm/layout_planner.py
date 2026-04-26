import json
from pathlib import Path
from typing import Optional
from openai import OpenAI
from src.backend.circuit_model import CircuitModel
from src.backend.timing_reasoner import TimingReasoner

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

DEFAULT_USER_PROMPT_TEMPLATE = """## 電路結構
{block_json}

{timing_info}

## 請產生區塊佈局（JSON格式）
"""


def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config.json"
    else:
        config_path = Path(config_path)

    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


class LayoutPlanner:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        config_path: Optional[str] = None
    ):
        config = load_config(config_path)
        api_config = config.get("api", {}) if config else {}

        self.api_key = (api_key or api_config.get("key", "")).strip()
        self.base_url = base_url or api_config.get("base_url", "https://api.minimax.io/v1")
        self.model = model or api_config.get("model", "MiniMax-M2.7")
        self.timeout_ms = api_config.get("timeout_ms", 60000)

        if not self.api_key:
            raise ValueError(
                "API key is required. Set it in config.json or pass api_key parameter.\n"
                f"Config file location: {Path(__file__).parent.parent.parent / 'config.json'}"
            )

        # Validate API key doesn't contain invalid characters for HTTP headers
        if '\n' in self.api_key or '\r' in self.api_key:
            raise ValueError(
                f"API key contains invalid characters (newline). "
                f"Please check your config.json or API key configuration."
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_ms / 1000,
        )
        self.timing_reasoner = TimingReasoner()

    def build_prompt(self, model: CircuitModel, timing_prompt: str = "") -> str:
        block_json = json.dumps(model.to_json(), ensure_ascii=False, indent=2)
        timing_info = timing_prompt if timing_prompt else "（無時序資訊）"
        return DEFAULT_USER_PROMPT_TEMPLATE.format(
            block_json=block_json,
            timing_info=timing_info
        )

    def generate_layout(self, model: CircuitModel, timing_info: str = "") -> CircuitModel:
        prompt = self.build_prompt(model, timing_info)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
        )
        content = response.choices[0].message.content
        # MiniMax-M2.7 returns content inside 【...】 tags, extract JSON from it
        json_str = self._extract_json(content)
        return self.parse_llm_response(json.loads(json_str))

    def _extract_json(self, content: str) -> str:
        """Extract JSON from MiniMax model response that may contain thinking tags or markdown."""
        if not content:
            raise ValueError("Empty response from LLM")
        import re
        # Remove thinking tags like 【...】
        cleaned = re.sub(r'【.*?】', '', content, flags=re.DOTALL)
        # Remove <think>...</think> blocks
        cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)
        # Remove markdown code blocks like ```json ... ```
        cleaned = re.sub(r'```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        cleaned = cleaned.strip()
        if not cleaned:
            raise ValueError(f"No JSON found in response: {content[:200]}")
        return cleaned

    def parse_llm_response(self, response: dict) -> CircuitModel:
        return CircuitModel.from_json(response)

    def generate_with_retry(self, model: CircuitModel, max_retries: int = 3) -> CircuitModel:
        timing_info = self.timing_reasoner.generate_promptSupplement(model)
        for attempt in range(max_retries):
            try:
                return self.generate_layout(model, timing_info)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                continue
