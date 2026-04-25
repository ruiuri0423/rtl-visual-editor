import pytest
from src.backend.circuit_model import CircuitModel, Block, Wire, Port
from src.backend.rtl_exporter import RtlExporter

def test_export_simple_module():
    model = CircuitModel()
    model.module_name = "test_mod"
    model.add_block(Block(id="in_a", block_type="input_port", label="a", bits=8, ports=[Port(name="a", direction="in", offset=0)]))
    model.add_block(Block(id="out_b", block_type="output_port", label="b", bits=8, ports=[Port(name="b", direction="out", offset=0)]))
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "module test_mod" in code
    assert "endmodule" in code

def test_export_input_port():
    model = CircuitModel()
    model.module_name = "test_ports"
    model.add_block(Block(id="a", block_type="input_port", label="a", bits=8))
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "input [8-1:0] a" in code

def test_export_output_port():
    model = CircuitModel()
    model.module_name = "test_ports"
    model.add_block(Block(id="b", block_type="output_port", label="b", bits=8))
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "output [8-1:0] b" in code

def test_export_register():
    model = CircuitModel()
    model.module_name = "test_reg"
    model.add_block(Block(id="cnt", block_type="register", label="cnt", bits=8))
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "reg [8-1:0] cnt" in code

def test_export_alu():
    model = CircuitModel()
    model.module_name = "test_alu"
    model.add_block(Block(id="alu0", block_type="alu", label="alu0", bits=8, properties={"operation": "add"}))
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "assign alu0_result = a + b;" in code

def test_export_wire():
    model = CircuitModel()
    model.module_name = "test_wire"
    model.add_block(Block(id="w", block_type="wire", label="w", bits=8))
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "wire [8-1:0] w" in code

def test_empty_module_name():
    model = CircuitModel()
    model.module_name = ""
    model.add_block(Block(id="a", block_type="input_port", label="a", bits=0))
    exporter = RtlExporter()
    code = exporter.export(model)
    assert "module" in code