import os
import asyncio
import sys
import json
from google import genai
from pydantic import BaseModel, Field
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from dotenv import load_dotenv
load_dotenv()

class ToolCallDecision(BaseModel):
    tool_name: str = Field(description="The name of the tool to call. E.g. 'reddit_crawler', 'twitter_crawler', or 'forum_onboarding'.")
    safe_query: str = Field(description="The safe_query or forum_url parameter to pass to the tool.")

async def llm_agent(user_prompt: str):
    # Ensure API Key is set for the GenAI SDK
    if not os.environ.get("GEMINI_API_KEY"):
        print("[-] GEMINI_API_KEY environment variable is not set.")
        print("[-] Ensure you export your API key before running this script.")
        return

    # Initialize Gemini Client
    client = genai.Client()

    # Configure the MCP server command to run our local server
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Fetch available tools dynamically from MCP server
            tools_response = await session.list_tools()
            tools_desc = []
            valid_tool_names = []
            for t in tools_response.tools:
                tools_desc.append(f"Tool: {t.name}\nDescription: {t.description}\nSchema: {json.dumps(t.inputSchema)}\n")
                valid_tool_names.append(t.name)
            
            tools_context = "\n".join(tools_desc)
            
            # 2. Ask Gemini to decide the tool and formulate the query
            system_instruction = f"""
You are an intelligent agent that selects the appropriate tool to call based on the user's request.
Here are the available tools and their schemas:
{tools_context}

Based on the user's request, decide which tool to call from the valid options: {valid_tool_names}.
Formulate the `safe_query` (or `forum_url` if using forum_onboarding) argument appropriately.
Return the output in JSON format.
"""
            
            print(f"[*] Sending request to Gemini: '{user_prompt}'")
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ToolCallDecision,
                )
            )
            
            decision = json.loads(response.text)
            tool_name = decision.get("tool_name")
            query_arg = decision.get("safe_query")
            
            print(f"[*] LLM Decision: Call tool '{tool_name}' with argument='{query_arg}'")
            
            if tool_name not in valid_tool_names:
                print(f"[-] LLM returned an invalid tool name: {tool_name}")
                return

            # Note: forum_onboarding expects 'forum_url' instead of 'safe_query'
            tool_args = {}
            if tool_name == "forum_onboarding":
                tool_args = {"forum_url": query_arg}
            else:
                tool_args = {"safe_query": query_arg}
            
            # 3. Call the tool via MCP
            print(f"[*] Executing '{tool_name}' via MCP Server...")
            try:
                result = await session.call_tool(tool_name, tool_args)
                print("\n[+] Result from MCP Server:")
                # result is an object from the MCP SDK containing the content
                for content in result.content:
                    print(content.text)
            except Exception as e:
                print(f"\n[-] Tool execution failed: {e}")

if __name__ == "__main__":
    print("=============================================")
    print(" AlgoPharma LLM-MCP Integration Test")
    print("=============================================")
    user_input = input("Enter your query (e.g., 'Find paracetamol side effects on Twitter'): ")
    if user_input.strip():
        asyncio.run(llm_agent(user_input))
    else:
        print("No query provided. Exiting.")
