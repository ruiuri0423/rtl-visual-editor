import pytest
from src.backend.rtl_parser import RtlParser
from src.backend.circuit_model import CircuitModel, Block
from src.backend.timing_reasoner import TimingReasoner
from src.llm.layout_planner import LayoutPlanner
from src.backend.rtl_exporter import RtlExporter

RTL_COUNTER = """
module counter (
    input clk,
    input rst_n,
    output [7:0] count
);
    reg [7:0] cnt;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= 0;
        else
            cnt <= cnt + 1;
    end
    assign count = cnt;
endmodule
"""

RTL_ADDER = """
module adder #(
    parameter BITS = 8
) (
    input clk,
    input rst_n,
    input [BITS-1:0] a,
    input [BITS-1:0] b,
    output [BITS-1:0] sum
);
    reg [BITS-1:0] result;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            result <= 0;
        else
            result <= a + b;
    end
    assign sum = result;
endmodule
"""

def test_parse_counter_module():
    """Test parsing a counter module"""
    parser = RtlParser()
    model = parser.parse(RTL_COUNTER)
    assert model.module_name == "counter"
    assert len(model.blocks) >= 2  # at least registers and ports

def test_parse_adder_with_parameter():
    """Test parsing an adder with parameter"""
    parser = RtlParser()
    model = parser.parse(RTL_ADDER)
    assert model.module_name == "adder"
    # Should have registers, ALU operations detected
    block_types = [b.block_type for b in model.blocks.values()]
    assert "register" in block_types

def test_timing_extraction_from_counter():
    """Test timing extraction from counter RTL"""
    parser = RtlParser()
    model = parser.parse(RTL_COUNTER)
    reasoner = TimingReasoner()
    timing = reasoner.extract(model, RTL_COUNTER)
    assert timing.clock == "clk"
    assert timing.clock_edge == "posedge"
    assert timing.reset == "rst_n"
    assert timing.reset_active == "low"

def test_timing_extraction_from_adder():
    """Test timing extraction from adder RTL"""
    parser = RtlParser()
    model = parser.parse(RTL_ADDER)
    reasoner = TimingReasoner()
    timing = reasoner.extract(model, RTL_ADDER)
    assert timing.clock == "clk"
    assert timing.reset == "rst_n"
    assert timing.reset_active == "low"

def test_export_counter():
    """Test RTL export from counter model"""
    parser = RtlParser()
    model = parser.parse(RTL_COUNTER)
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "module counter" in code
    assert "endmodule" in code
    assert "reg" in code.lower() or "register" in code.lower()

def test_export_adder():
    """Test RTL export from adder model"""
    parser = RtlParser()
    model = parser.parse(RTL_ADDER)
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "module adder" in code
    assert "endmodule" in code

def test_circuit_model_roundtrip():
    """Test CircuitModel to_json and from_json roundtrip"""
    from src.backend.circuit_model import Wire
    parser = RtlParser()
    model = parser.parse(RTL_COUNTER)
    json_data = model.to_json()
    restored = CircuitModel.from_json(json_data)
    assert restored.module_name == model.module_name
    assert len(restored.blocks) == len(model.blocks)

def test_layout_planner_builds_correct_prompt():
    """Test LayoutPlanner prompt building"""
    parser = RtlParser()
    model = parser.parse(RTL_COUNTER)
    planner = LayoutPlanner(api_key="test-key")
    prompt = planner.build_prompt(model, "")
    assert "counter" in prompt or "blocks" in prompt
    assert "JSON" in prompt

def test_full_pipeline_no_llm():
    """Test the full pipeline without LLM (parse -> model -> export)"""
    parser = RtlParser()
    model = parser.parse(RTL_COUNTER)
    reasoner = TimingReasoner()
    timing = reasoner.extract(model, RTL_COUNTER)
    exporter = RtlExporter()
    code = exporter.export(model)

    # Verify exported code is valid Verilog
    assert "module counter" in code
    assert "endmodule" in code
    # Verify we can parse the exported code again
    reparsed = parser.parse(code)
    assert reparsed.module_name == "counter"