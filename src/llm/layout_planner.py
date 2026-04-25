import json
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

class LayoutPlanner:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
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
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = response.choices[0].message.content
        return self.parse_llm_response(json.loads(content))

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
