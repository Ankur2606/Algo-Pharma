"""
AlgoPharma — MCP Tools wrapper.
Exposes Reddit, Twitter, and Forum Onboarding as MCP-compatible tools.
These tools can be called via MCP protocol by language models.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RedditTool:
    """MCP Tool: Crawl Reddit for adverse events on specified drug."""
    
    name = "reddit_crawler"
    description = "Search Reddit for discussions about medicines and adverse effects"
    
    input_schema = {
        "type": "object",
        "properties": {
            "safe_query": {
                "type": "string",
                "description": "Medicine name or condition to search (e.g., 'dolo 650 side effects', 'paracetamol adverse reactions')"
            },
            "project_id": {
                "type": "integer",
                "description": "Project ID for organizing results (default: 1)",
                "default": 1
            }
        },
        "required": ["safe_query"]
    }
    
    @staticmethod
    async def execute(safe_query: str, project_id: int = 1) -> dict:
        """Execute Reddit crawler with keyword filtering."""
        try:
            from tasks.crawl_reddit import crawl_reddit
            result = crawl_reddit(project_id=project_id, query=safe_query)
            return {
                "success": True,
                "tool": "reddit_crawler",
                "query": safe_query,
                "result": result
            }
        except Exception as e:
            logger.error(f"Reddit crawler failed: {e}")
            return {
                "success": False,
                "tool": "reddit_crawler",
                "error": str(e)
            }


class TwitterTool:
    """MCP Tool: Crawl Twitter/X for adverse events on specified drug."""
    
    name = "twitter_crawler"
    description = "Search Twitter/X for real-time discussions about medicines and health issues"
    
    input_schema = {
        "type": "object",
        "properties": {
            "safe_query": {
                "type": "string",
                "description": "Medicine name or condition to search (e.g., 'dolo 650 reaction', 'paracetamol side effect')"
            },
            "project_id": {
                "type": "integer",
                "description": "Project ID for organizing results (default: 1)",
                "default": 1
            }
        },
        "required": ["safe_query"]
    }
    
    @staticmethod
    async def execute(safe_query: str, project_id: int = 1) -> dict:
        """Execute Twitter crawler with keyword filtering."""
        try:
            from tasks.crawl_twitter import crawl_twitter
            result = crawl_twitter(project_id=project_id, query=safe_query)
            return {
                "success": True,
                "tool": "twitter_crawler",
                "query": safe_query,
                "result": result
            }
        except Exception as e:
            logger.error(f"Twitter crawler failed: {e}")
            return {
                "success": False,
                "tool": "twitter_crawler",
                "error": str(e)
            }


class ForumOnboardingTool:
    """MCP Tool: Analyze a forum and auto-generate crawler config."""
    
    name = "forum_onboarding"
    description = "Analyze a forum URL to auto-generate a working crawler configuration"
    
    input_schema = {
        "type": "object",
        "properties": {
            "forum_url": {
                "type": "string",
                "description": "Forum URL to analyze (e.g., 'https://medicinalforum.com/threads')"
            },
            "project_id": {
                "type": "integer",
                "description": "Project ID for organizing config (default: 1)",
                "default": 1
            }
        },
        "required": ["forum_url"]
    }
    
    @staticmethod
    async def execute(forum_url: str, project_id: int = 1) -> dict:
        """Execute forum onboarding analysis."""
        try:
            from agentic.forum_onboarding import onboard_forum
            result = onboard_forum(forum_url)
            return {
                "success": result.get("success", False),
                "tool": "forum_onboarding",
                "url": forum_url,
                "config": result.get("config", {}),
                "samples": result.get("samples", []),
                "confidence": result.get("confidence", 0.0),
                "error": result.get("error", None)
            }
        except Exception as e:
            logger.error(f"Forum onboarding failed: {e}")
            return {
                "success": False,
                "tool": "forum_onboarding",
                "url": forum_url,
                "error": str(e)
            }


# Registry of all MCP tools
MCP_TOOLS = {
    "reddit_crawler": RedditTool,
    "twitter_crawler": TwitterTool,
    "forum_onboarding": ForumOnboardingTool,
}


def get_tools_list() -> list[dict]:
    """Return list of available MCP tools with schemas."""
    tools = []
    for tool_name, tool_class in MCP_TOOLS.items():
        tools.append({
            "name": tool_class.name,
            "description": tool_class.description,
            "inputSchema": tool_class.input_schema
        })
    return tools


async def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a tool by name with given arguments."""
    if tool_name not in MCP_TOOLS:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}. Available: {list(MCP_TOOLS.keys())}"
        }
    
    tool_class = MCP_TOOLS[tool_name]
    try:
        result = await tool_class.execute(**arguments)
        return result
    except TypeError as e:
        return {
            "success": False,
            "tool": tool_name,
            "error": f"Invalid arguments: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return {
            "success": False,
            "tool": tool_name,
            "error": str(e)
        }


if __name__ == "__main__":
    import asyncio
    
    # Test: List available tools
    print("=" * 60)
    print("AlgoPharma MCP Tools")
    print("=" * 60)
    tools = get_tools_list()
    for tool in tools:
        print(f"\n📌 {tool['name']}")
        print(f"   {tool['description']}")
        print(f"   Input schema: {json.dumps(tool['inputSchema'], indent=6)}")
    
    # Test execution
    print("\n" + "=" * 60)
    print("Test: Executing reddit_crawler tool")
    print("=" * 60)
    result = asyncio.run(execute_tool("reddit_crawler", {
        "safe_query": "dolo 650 side effects",
        "project_id": 1
    }))
    print(f"Result: {json.dumps(result, indent=2, default=str)}")
