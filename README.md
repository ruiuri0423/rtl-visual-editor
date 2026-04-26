# RTL Visual Editor

RTL 可視化編輯器 — 解析 Verilog RTL，透過 LLM 生成 RT 層級電路區塊圖，支援圖形化編輯並輸出修改後的 RTL Code。

## 功能特色

- **RTL 解析** — 解析 Verilog RTL 程式碼，建立結構化電路模型
- **LLM 驅動佈局** — 透過 OpenAI GPT-4 API 生成電路區塊圖（RT 層級）
- **圖形化編輯** — 新增/刪除/調整方塊和連線
- **RTL 輸出** — 從編輯後的電路結構直接生成 Verilog RTL Code
- **手動 LLM 重新生成** — 使用者可在重大架構變動時手動觸發 LLM 重新生成

## 安裝方式（Windows）

### 前置需求

- Python 3.11 或更高版本
- [Node.js](https://nodejs.org/)（用於視覺化伴侶，可選）

### 步驟

**1. 確認 Python 版本**

```powershell
python --version
# 確認為 3.11 或更高
```

**2. 建立虛擬環境（建議）**

```powershell
cd rtl_visual_editor
python -m venv venv
.\venv\Scripts\activate
```

**3. 安裝依賴**

```powershell
pip install -e .
```

**4. 設定 OpenAI API Key**

```powershell
# 設定環境變數
setx OPENAI_API_KEY "your-api-key-here"
```

或在 Python 中設定：
```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

**5. 執行應用程式**

```powershell
python -m src.main
```

## 開發模式安裝

```powershell
pip install -e ".[dev]"
pytest tests/ -v
```

## 測試

```powershell
pytest tests/ -v
```

## 專案結構

```
rtl_visual_editor/
├── src/
│   ├── main.py                    # 應用程式入口點
│   ├── backend/                   # 後端核心模組
│   │   ├── circuit_model.py       # 電路資料模型
│   │   ├── rtl_parser.py         # Verilog RTL 解析器
│   │   ├── timing_reasoner.py     # 時序資訊推理
│   │   └── rtl_exporter.py        # RTL 輸出
│   ├── llm/                       # LLM 通訊
│   │   └── layout_planner.py      # GPT-4 API 整合
│   ├── renderer/                   # Qt 圖形渲染
│   │   ├── circuit_renderer.py
│   │   ├── block_item.py
│   │   └── wire_item.py
│   ├── editor/                    # 編輯控制
│   │   └── editor_controller.py
│   └── ui/                        # Qt UI 元件
│       ├── main_window.py
│       ├── input_panel.py
│       ├── properties_panel.py
│       └── export_panel.py
└── tests/                         # 單元測試 + 整合測試
```

## 使用方式

1. **輸入 RTL** — 在左側面板粘貼 Verilog RTL 程式碼，或點選「Load File」載入 `.v` 檔案
2. **生成區塊圖** — 點選「Parse & Generate」，系統會呼叫 LLM 生成電路佈局
3. **編輯電路** — 在圖形視圖中拖曳方塊、調整連線、修改屬性
4. **輸出 RTL** — 點選「Export RTL...」下載修改後的 Verilog 程式碼

## 支援的 RTL 語法

- `module` / `endmodule`
- `input` / `output` / `wire` / `reg`
- `parameter` / `localparam`
- `always @(posedge clk)` — 時序電路（暫存器）
- `assign` — 組合邏輯（ALU、多工器等）
- 基本運算：`+`, `-`, `&`, `|`, `^`, `~`, `<<`, `>>`, `? :`

## 預計支援（未來版本）

- `generate` / `genvar` — 展開 generate 迴圈
- `FSM` 檢測與視覺化
- 階層化視圖（點選子模組鑽進去看內部）
- 匯出 PNG / PDF

## 授權

MIT License
