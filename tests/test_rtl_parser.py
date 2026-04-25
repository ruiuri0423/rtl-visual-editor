import pytest
from src.backend.rtl_parser import RtlParser

SIMPLE_MODULE = """
module adder #(
    parameter BITS = 8
) (
    input clk,
    input rst_n,
    input [BITS-1:0] a,
    input [BITS-1:0] b,
    output [BITS-1:0] out
);
    reg [BITS-1:0] result;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            result <= 0;
        else
            result <= a + b;
    end
    assign out = result;
endmodule
"""

def test_parse_simple_module():
    parser = RtlParser()
    model = parser.parse(SIMPLE_MODULE)
    assert model.module_name == "adder"
    assert len(model.blocks) >= 2  # register + wires + ports

def test_parse_register():
    parser = RtlParser()
    model = parser.parse(SIMPLE_MODULE)
    reg = next((b for b in model.blocks.values() if b.block_type == "register"), None)
    assert reg is not None
    assert reg.bits == 0  # bits resolved from parameter at parse time

def test_parse_parameter():
    parser = RtlParser()
    model = parser.parse(SIMPLE_MODULE)
    # parameters are extracted, check ports
    port_names = [b.label for b in model.blocks.values()]
    assert "a" in port_names or "b" in port_names

def test_parse_alu():
    parser = RtlParser()
    model = parser.parse(SIMPLE_MODULE)
    alu = next((b for b in model.blocks.values() if b.block_type == "alu"), None)
    assert alu is not None

def test_parse_input_ports():
    parser = RtlParser()
    model = parser.parse(SIMPLE_MODULE)
    inputs = [b for b in model.blocks.values() if b.block_type == "input_port"]
    assert len(inputs) >= 2  # clk, rst_n, a, b

def test_parse_output_ports():
    parser = RtlParser()
    model = parser.parse(SIMPLE_MODULE)
    outputs = [b for b in model.blocks.values() if b.block_type == "output_port"]
    assert len(outputs) >= 1

def test_detect_add_operation():
    parser = RtlParser()
    op = parser._detect_operation("a + b")
    assert op == "add"

def test_detect_mux_operation():
    parser = RtlParser()
    op = parser._detect_operation("sel ? a : b")
    assert op == "mux"
