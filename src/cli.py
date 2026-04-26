#!/usr/bin/env python
"""RTL Parser CLI - Parse Verilog RTL and print circuit model info."""

import argparse
import sys
import json
from src.backend.rtl_parser import RtlParser
from src.backend.timing_reasoner import TimingReasoner


def main():
    parser = argparse.ArgumentParser(description="Parse Verilog RTL and display circuit model")
    parser.add_argument("file", nargs="?", help="Verilog file to parse (or use stdin)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--timing", action="store_true", help="Include timing info")
    args = parser.parse_args()

    # Read RTL code
    if args.file:
        with open(args.file, "r") as f:
            rtl_code = f.read()
    else:
        rtl_code = sys.stdin.read()
        if not rtl_code.strip():
            print("Error: No RTL code provided", file=sys.stderr)
            print("Usage: python -m src.cli parse <file.v>", file=sys.stderr)
            print("   or: echo 'module ...' | python -m src.cli", file=sys.stderr)
            sys.exit(1)

    # Parse
    rtl_parser = RtlParser()
    model = rtl_parser.parse(rtl_code)

    if args.json:
        output = model.to_json()
        output["timing"] = None
        if args.timing:
            reasoner = TimingReasoner()
            timing = reasoner.extract(model, rtl_code)
            output["timing"] = {
                "clock": timing.clock,
                "clock_edge": timing.clock_edge,
                "reset": timing.reset,
                "reset_active": timing.reset_active,
                "data_path": timing.data_path,
                "sequential_blocks": timing.sequential_blocks,
                "combinational_blocks": timing.combinational_blocks,
            }
        print(json.dumps(output, indent=2))
    else:
        print(f"Module: {model.module_name}")
        print(f"Blocks: {len(model.blocks)}")
        print(f"Wires: {len(model.wires)}")
        print()
        print("Blocks:")
        for bid, block in model.blocks.items():
            print(f"  [{block.block_type:12}] {block.id:20} label='{block.label}' bits={block.bits}")
            if block.properties:
                print(f"    properties: {block.properties}")
        print()
        print("Wires:")
        for wire in model.wires:
            print(f"  {wire.from_port} → {wire.to_port}")

        if args.timing:
            print()
            reasoner = TimingReasoner()
            timing = reasoner.extract(model, rtl_code)
            print("Timing Info:")
            print(f"  Clock: {timing.clock} ({timing.clock_edge})")
            print(f"  Reset: {timing.reset} ({timing.reset_active})")
            print(f"  Sequential blocks: {', '.join(timing.sequential_blocks)}")
            print(f"  Combinational blocks: {', '.join(timing.combinational_blocks)}")
            if timing.data_path:
                print(f"  Data path: {' → '.join(timing.data_path)}")


if __name__ == "__main__":
    main()
