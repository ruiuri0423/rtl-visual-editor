import re
from typing import List, Tuple, Optional
from .circuit_model import CircuitModel, Block, Wire, Port

class RtlParser:
    def parse(self, rtl_code: str) -> CircuitModel:
        model = CircuitModel()

        # Extract module name and ports
        module_match = re.search(r'module\s+(\w+)\s*(?:#\s*\([^)]*\))?\s*\(', rtl_code, re.MULTILINE)
        if not module_match:
            return model
        model.module_name = module_match.group(1)

        # Parse module ports
        port_match = re.search(r'module\s+\w+\s*(?:#\s*\([^)]*\))?\s*\(([\s\S]*?)\)\s*;', rtl_code, re.MULTILINE)
        if port_match:
            port_list = self._parse_port_list(port_match.group(1))
            for direction, name, bits in port_list:
                block = Block(
                    id=name,
                    block_type="input_port" if direction == "input" else "output_port",
                    label=name,
                    bits=bits,
                    ports=[Port(name=name, direction="in" if direction == "input" else "out", offset=0)]
                )
                model.add_block(block)

        # Parse parameter declarations
        param_pattern = re.compile(r'parameter\s+(\w+)\s*=\s*([^;]+);', re.MULTILINE)
        params = {}
        for m in param_pattern.finditer(rtl_code):
            params[m.group(1)] = m.group(2).strip()

        # Parse always blocks for registers
        always_pattern = re.compile(
            r'always\s+@\(\s*posedge\s+(\w+)\s*(?:or\s+negedge\s+(\w+))?\)\s*begin\s*([\s\S]*?)end',
            re.MULTILINE
        )
        for m in always_pattern.finditer(rtl_code):
            clk = m.group(1)
            rst = m.group(2)
            body = m.group(3)
            # Extract register assignments: reg <= expr
            reg_assign = re.findall(r'(\w+)\s*<=', body)
            for reg_name in reg_assign:
                reg_block = Block(
                    id=reg_name,
                    block_type="register",
                    label=reg_name,
                    bits=0,
                    ports=[
                        Port(name="D", direction="in", offset=0),
                        Port(name="Q", direction="out", offset=0),
                    ]
                )
                model.add_block(reg_block)

            # Detect operations inside always blocks (for parameterized BITS)
            for line in body.split(';'):
                for match in re.finditer(r'(\w+)\s*<=', line):
                    lhs = match.group(1)
                expr_match = re.search(r'<=?\s*([^;]+)', line)
                if expr_match:
                    expr = expr_match.group(1).strip()
                    op = self._detect_operation(expr)
                    if op:
                        alu_block = Block(
                            id=f"alu_{expr[:10].replace(' ', '_')}",
                            block_type="alu",
                            label=f"ALU_{op}",
                            bits=0,
                            properties={"operation": op, "expression": expr},
                            ports=[
                                Port(name="A", direction="in", offset=0),
                                Port(name="B", direction="in", offset=1),
                                Port(name="Result", direction="out", offset=0),
                            ]
                        )
                        model.add_block(alu_block)

        # Parse assign statements for combinational logic
        assign_pattern = re.compile(r'assign\s+(\w+)\s*=\s*([^;]+);', re.MULTILINE)
        for m in assign_pattern.finditer(rtl_code):
            lhs = m.group(1)
            rhs = m.group(2).strip()
            op = self._detect_operation(rhs)
            if op:
                alu_block = Block(
                    id=f"alu_{lhs}",
                    block_type="alu",
                    label=f"ALU_{lhs}",
                    bits=0,
                    properties={"operation": op, "expression": rhs},
                    ports=[
                        Port(name="A", direction="in", offset=0),
                        Port(name="B", direction="in", offset=1),
                        Port(name="Result", direction="out", offset=0),
                    ]
                )
                model.add_block(alu_block)
                model.add_wire(Wire(from_port=f"alu_{lhs}.Result", to_port=lhs))

        # Parse wire declarations
        wire_pattern = re.compile(r'wire\s+(?:\[(\d+)-1:0\])?\s*([\w]+);', re.MULTILINE)
        for m in wire_pattern.finditer(rtl_code):
            bits = int(m.group(1)) if m.group(1) else 0
            wire_name = m.group(2)
            wire_block = Block(
                id=wire_name,
                block_type="wire",
                label=wire_name,
                bits=bits,
                ports=[
                    Port(name="in", direction="in", offset=0),
                    Port(name="out", direction="out", offset=0),
                ]
            )
            model.add_block(wire_block)

        return model

    def _parse_port_list(self, port_text: str) -> List[Tuple[str, str, int]]:
        ports = []
        for line in port_text.split(','):
            line = line.strip()
            if not line:
                continue
            # Handle both simple ports and parameterized bit ranges like [BITS-1:0]
            input_match = re.match(r'input\s+(?:\[([^\]]+)-1:0\])?\s*(\w+)', line)
            output_match = re.match(r'output\s+(?:\[([^\]]+)-1:0\])?\s*(\w+)', line)
            if input_match:
                bits_expr = input_match.group(1)
                # If it's a numeric expression like "8", use it; otherwise 0 (parameterized)
                try:
                    bits = int(bits_expr) if bits_expr else 0
                except ValueError:
                    bits = 0
                ports.append(("input", input_match.group(2), bits))
            elif output_match:
                bits_expr = output_match.group(1)
                try:
                    bits = int(bits_expr) if bits_expr else 0
                except ValueError:
                    bits = 0
                ports.append(("output", output_match.group(2), bits))
        return ports

    def _detect_operation(self, expr: str) -> Optional[str]:
        expr = expr.replace(" ", "")
        if "+" in expr: return "add"
        if "-" in expr and expr.count("-") == 1 and expr.index("-") > 0: return "sub"
        if "&" in expr: return "and"
        if "|" in expr: return "or"
        if "^" in expr: return "xor"
        if "~" in expr: return "not"
        if "<<" in expr: return "shl"
        if ">>" in expr: return "shr"
        if "==" in expr: return "eq"
        if "!=" in expr: return "ne"
        if "<" in expr: return "lt"
        if ">" in expr: return "gt"
        if "?" in expr: return "mux"
        return None
