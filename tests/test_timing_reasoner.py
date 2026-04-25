import pytest
from src.backend.circuit_model import CircuitModel, Block
from src.backend.timing_reasoner import TimingReasoner

SIMPLE_RTL = """
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

def test_extract_clock():
    model = CircuitModel()
    model.add_block(Block(id="cnt", block_type="register", label="cnt", bits=8))
    reasoner = TimingReasoner()
    timing_info = reasoner.extract(model, SIMPLE_RTL)
    assert timing_info.clock == "clk"
    assert timing_info.clock_edge == "posedge"

def test_extract_reset():
    model = CircuitModel()
    model.add_block(Block(id="cnt", block_type="register", label="cnt", bits=8))
    reasoner = TimingReasoner()
    timing_info = reasoner.extract(model, SIMPLE_RTL)
    assert timing_info.reset == "rst_n"
    assert timing_info.reset_active == "low"

def test_sequential_blocks():
    model = CircuitModel()
    model.add_block(Block(id="cnt", block_type="register", label="cnt", bits=8))
    reasoner = TimingReasoner()
    timing_info = reasoner.extract(model, SIMPLE_RTL)
    assert "cnt" in timing_info.sequential_blocks

def test_combinational_blocks():
    model = CircuitModel()
    model.add_block(Block(id="alu_0", block_type="alu", label="ALU", bits=8))
    reasoner = TimingReasoner()
    timing_info = reasoner.extract(model, SIMPLE_RTL)
    assert "alu_0" in timing_info.combinational_blocks

def test_data_path_from_wires():
    from src.backend.circuit_model import Wire
    model = CircuitModel()
    model.add_block(Block(id="cnt", block_type="register", label="cnt", bits=8))
    model.add_wire(Wire(from_port="cnt.Q", to_port="count"))
    reasoner = TimingReasoner()
    timing_info = reasoner.extract(model, SIMPLE_RTL)
    assert len(timing_info.data_path) >= 1

def test_generate_prompt_supplement():
    reasoner = TimingReasoner()
    model = CircuitModel()
    model.add_block(Block(id="cnt", block_type="register", label="cnt", bits=8))
    model.add_block(Block(id="alu_0", block_type="alu", label="ALU", bits=8))
    # When called without RTL, extract gets empty string and no timing info is extracted
    # Just verify it returns a valid string structure
    prompt = reasoner.generate_promptSupplement(model)
    assert isinstance(prompt, str)

def test_no_timing_info():
    reasoner = TimingReasoner()
    model = CircuitModel()
    model.add_block(Block(id="wire_0", block_type="wire", label="wire0", bits=8))
    timing_info = reasoner.extract(model, "")
    assert timing_info.clock is None
    assert len(timing_info.data_path) == 0