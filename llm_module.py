import os
import asyncio
import sys
import json
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from dotenv import load_dotenv

load_dotenv()


async def llm_agent(user_prompt: str, project_id: int = 1):
    if not os.environ.get("GEMINI_API_KEY"):
        print("[-] GEMINI_API_KEY is not set.")
        return

    # Initialize Gemini Client
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # Start our MCP server as a subprocess
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Fetch tools from MCP server
            tools_response = await session.list_tools()

            # 2. Convert MCP tool schemas → Gemini FunctionDeclaration format
            gemini_tools = []
            valid_tool_names = []

            for t in tools_response.tools:
                valid_tool_names.append(t.name)
                gemini_tools.append(
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name=t.name,
                                description=t.description,
                                parameters=t.inputSchema  # MCP schema is already JSON Schema
                            )
                        ]
                    )
                )

            print(f"[*] Available tools: {valid_tool_names}")
            print(f"[*] User query: '{user_prompt}'")

            # 3. Send to Gemini with native tool calling (no Pydantic schema hack needed)
            response = client.models.generate_content(
                model="gemini-2.5-flash",   # ✅ Free tier, not deprecated
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an agent that selects the right tool to search for "
                        "pharmaceutical adverse events. Use the tools provided to fulfill "
                        "the user's request. Always call a tool — don't answer from memory."
                    ),
                    tools=gemini_tools,
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(
                            mode="ANY"  # Force it to always call a tool
                        )
                    )
                )
            )

            # 4. Extract the function call Gemini decided to make
            function_call = None
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_call = part.function_call
                    break

            if not function_call:
                print("[-] Gemini did not return a tool call.")
                print(f"    Response: {response.text}")
                return

            tool_name = function_call.name
            tool_args = dict(function_call.args)  # Already a dict from Gemini

            # Inject project_id so Celery workers tag all DB rows correctly
            tool_args["project_id"] = project_id

            print(f"[*] Gemini chose tool: '{tool_name}' with args: {tool_args}")

            if tool_name not in valid_tool_names:
                print(f"[-] Invalid tool name returned: {tool_name}")
                return None

            # 5. Execute via MCP
            print(f"[*] Executing '{tool_name}' via MCP...")
            try:
                result = await session.call_tool(tool_name, tool_args)
                print("\n[+] Result from MCP:")
                result_text = None
                for content in result.content:
                    print(content.text)
                    result_text = content.text
                return result_text
            except Exception as e:
                print(f"[-] Tool execution failed: {e}")
                return None


if __name__ == "__main__":
    print("=" * 50)
    print(" AlgoPharma — Gemini + MCP Agent")
    print("=" * 50)
    user_input = input("Enter query (e.g., 'Find paracetamol side effects on Reddit'): ")
    if user_input.strip():
        asyncio.run(llm_agent(user_input))
    else:
        print("No query provided.")
