import asyncio
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
    print("[*] AlgoPharma MCP Server Starting...")
    asyncio.run(main())
