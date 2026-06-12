import asyncio
from mcp import types as mcp_types
from acc.mcp.tools_cli import cli_run_tool
from acc.mcp.tools_compaction import compress_context_tool

async def run_tests():
    print("Testing compress_context_tool...")
    # Mock a python file
    code = '''
def test_mock():
    """This docstring should be deleted"""
    x = 1 + 1
    return x
'''
    input_data = {"text": code, "profile": "python_code"}
    res = await compress_context_tool(input_data)
    out = res[0].text
    assert "docstring" not in out
    assert "pass" in out
    print("compress_context_tool passed!")

    print("Testing cli_run_tool (auto-routing)...")
    cli_input = {"cmd": ["python", "-c", "print('INFO  this is noise\\nError this is real')"]}
    cli_res = await cli_run_tool(cli_input)
    cli_out = cli_res[0].text
    # echo doesn't have a profile, falls back to default which strips INFO
    assert "INFO" not in cli_out
    assert "Error" in cli_out
    print("cli_run_tool passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())
