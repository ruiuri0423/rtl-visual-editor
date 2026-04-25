from typing import Dict, List
from .circuit_model import CircuitModel, Block, Wire

class RtlExporter:
    def export(self, model: CircuitModel) -> str:
        lines = []
        lines.append(f"module {model.module_name} (")

        # Collect input/output ports
        inputs = []
        outputs = []
        for block in model.blocks.values():
            if block.block_type == "input_port":
                inputs.append(block)
            elif block.block_type == "output_port":
                outputs.append(block)

        # Generate port declarations
        all_ports = inputs + outputs
        port_decls = []
        for i, block in enumerate(all_ports):
            direction = "input" if block.block_type == "input_port" else "output"
            bits_str = f"[{block.bits}-1:0] " if block.bits > 0 else ""
            comma = "," if i < len(all_ports) - 1 else ""
            port_decls.append(f"    {direction} {bits_str}{block.label}{comma}")
        lines.append(",\n".join(port_decls))
        lines.append(");")

        # Generate internal declarations
        regs = [b for b in model.blocks.values() if b.block_type == "register"]
        alus = [b for b in model.blocks.values() if b.block_type == "alu"]
        wires = [b for b in model.blocks.values() if b.block_type == "wire"]

        if regs:
            lines.append("")
            for reg in regs:
                bits_str = f"[{reg.bits}-1:0]" if reg.bits > 0 else ""
                lines.append(f"    reg {bits_str} {reg.label};")
        if wires:
            lines.append("")
            for wire in wires:
                bits_str = f"[{wire.bits}-1:0]" if wire.bits > 0 else ""
                lines.append(f"    wire {bits_str} {wire.label};")

        if alus:
            lines.append("")
            for alu in alus:
                bits_str = f"[{alu.bits}-1:0]" if alu.bits > 0 else ""
                op = alu.properties.get("operation", "add")
                op_map = {"add": "+", "sub": "-", "and": "&", "or": "|", "xor": "^", "not": "~", "shl": "<<", "shr": ">>"}
                op_str = op_map.get(op, "+")
                lines.append(f"    assign {alu.label}_result = a {op_str} b;")

        lines.append("")
        lines.append("endmodule")
        return "\n".join(lines)