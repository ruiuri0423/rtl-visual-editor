import re
from dataclasses import dataclass, field
from typing import List, Optional
from .circuit_model import CircuitModel

@dataclass
class TimingInfo:
    clock: Optional[str] = None
    clock_edge: str = "posedge"
    reset: Optional[str] = None
    reset_active: str = "high"
    data_path: List[str] = field(default_factory=list)
    combinational_blocks: List[str] = field(default_factory=list)
    sequential_blocks: List[str] = field(default_factory=list)

class TimingReasoner:
    def extract(self, model: CircuitModel, rtl_code: str) -> TimingInfo:
        info = TimingInfo()

        # Extract clock from always @(posedge clk) pattern
        clk_match = re.search(r'always\s+@\(\s*posedge\s+(\w+)', rtl_code)
        if clk_match:
            info.clock = clk_match.group(1)
            info.clock_edge = "posedge"
        else:
            clk_match = re.search(r'always\s+@\(\s*negedge\s+(\w+)', rtl_code)
            if clk_match:
                info.clock = clk_match.group(1)
                info.clock_edge = "negedge"

        # Extract reset signal
        rst_match = re.search(r'or\s+negedge\s+(\w+)', rtl_code)
        if rst_match:
            info.reset = rst_match.group(1)
            info.reset_active = "low"
        else:
            rst_match = re.search(r'or\s+posedge\s+(\w+)', rtl_code)
            if rst_match:
                info.reset = rst_match.group(1)
                info.reset_active = "high"

        # Classify blocks by type
        for block in model.blocks.values():
            if block.block_type == "register":
                info.sequential_blocks.append(block.id)
            elif block.block_type in ["alu", "mux", "wire"]:
                info.combinational_blocks.append(block.id)

        # Build data path from wires
        for wire in model.wires:
            src_block = wire.from_port.split(".")[0]
            dst_block = wire.to_port.split(".")[0]
            if src_block not in info.data_path:
                info.data_path.append(src_block)
            if dst_block not in info.data_path:
                info.data_path.append(dst_block)

        return info

    def generate_promptSupplement(self, model: CircuitModel) -> str:
        info = self.extract(model, "")
        lines = ["## 時序資訊"]

        if info.clock:
            lines.append(f"- 時脈: {info.clock} ({info.clock_edge}觸發)")
        if info.reset:
            lines.append(f"- 重置: {info.reset} ({info.reset_active}態有效)")
        if info.data_path:
            path_str = " → ".join(info.data_path)
            lines.append(f"- 資料路徑: {path_str}")

        combinational = ", ".join(info.combinational_blocks)
        if combinational:
            lines.append(f"- 組合邏輯區塊: {combinational}")

        sequential = ", ".join(info.sequential_blocks)
        if sequential:
            lines.append(f"- 時序區塊: {sequential}")

        if info.data_path and len(info.sequential_blocks) >= 2:
            lines.append(f"- 區塊擺放建議: {'和'.join(info.sequential_blocks[:2])} 應相鄰擺放")

        return "\n".join(lines) if lines else ""