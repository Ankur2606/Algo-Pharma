import asyncio
import sys
import os

# Enable FAST_MODE to prevent downloading 2GB+ of HuggingFace models during MCP tool calls
os.environ["FAST_MODE"] = "true"

# Redirect stderr to a file to prevent OS pipe deadlocks on Windows
# We use Python-level redirection as os.dup2 can fail with 'Invalid Handle' in some Windows environments
try:
    error_log = open("mcp_server_stderr.log", "a", encoding="utf-8", buffering=1)
    sys.stderr = error_log
except Exception:
    # If we can't open the log, at least don't crash
    pass

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp_tools import MCP_TOOLS, execute_tool

app = Server("algopharma-mcp")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name=cls.name,
            description=cls.description,
            inputSchema=cls.input_schema
        )
        for cls in MCP_TOOLS.values()
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    result = await execute_tool(name, arguments)
    return [TextContent(type="text", text=str(result))]

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    import sys
    print("[*] AlgoPharma MCP Server Starting...", file=sys.stderr)
    
    # MCP server does NOT need to load models - crawlers only do Phase 1 (raw data collection)
    # Phase 2 (NLP processing) happens in Celery workers
    print("[*] MCP server ready (models will be loaded by Celery workers)", file=sys.stderr)
    
    asyncio.run(main())
