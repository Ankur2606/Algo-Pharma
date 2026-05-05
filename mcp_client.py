import asyncio
import sys
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def test():
    print("Initializing MCP Client Test...")
    
    # Configure the MCP server command
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )
    
    print(f"Connecting to server: {server_params.command} {' '.join(server_params.args)}")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            print("\n[+] Session Initialized Successfully")
            
            # List available tools
            tools = await session.list_tools()
            print("\n[+] Available Tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Call the reddit_crawler tool
            print("\n[+] Calling Tool 'reddit_crawler' with args: {'safe_query': 'dolo 650 side effects'}")
            try:
                result = await session.call_tool("reddit_crawler", {
                    "safe_query": "dolo 650 side effects"
                })
                print(f"\n[+] Tool Result:\n{result}")
            except Exception as e:
                print(f"\n[-] Tool Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
