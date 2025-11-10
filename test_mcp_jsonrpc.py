"""Test MCP JSON-RPC integration with N8N."""
import asyncio
from src.infrastructure.mcp import MCPJsonRpcClient
from src.config.settings import get_settings


async def test():
    print("=" * 70)
    print("MCP JSON-RPC Integration Test with N8N")
    print("=" * 70)

    settings = get_settings()

    # Create MCP JSON-RPC client
    print("\n1. Creating MCP JSON-RPC client...")
    mcp_client = MCPJsonRpcClient(
        base_url=settings.mcp.n8n_mcp_gmail_base_url,
        auth_header_name=settings.mcp.n8n_mcp_header_name,
        auth_header_value=settings.mcp.n8n_mcp_header_value,
    )
    print(f"   ✓ Client created for: {settings.mcp.n8n_mcp_gmail_base_url}")

    # Test 1: List available tools
    print("\n2. Listing available tools (JSON-RPC: tools/list)...")
    try:
        tools = await mcp_client.list_tools()
        print(f"   ✓ Found {len(tools)} tools:")
        for tool in tools:
            tool_name = tool.get("name", "unknown")
            tool_desc = tool.get("description", "")[:80]
            print(f"     - {tool_name}")
            print(f"       {tool_desc}...")

            # Show input schema if available
            input_schema = tool.get("inputSchema", {})
            if input_schema:
                properties = input_schema.get("properties", {})
                if properties:
                    print(f"       Parameters: {list(properties.keys())}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("\n⚠️  If you see a 404 error, check:")
        print("   1. Is the N8N workflow ACTIVE?")
        print("   2. Is the MCP Server Trigger node configured?")
        print("   3. Is the URL correct in your .env?")
        return

    # Test 2: Call get_emails tool
    print("\n3. Testing get_emails tool (JSON-RPC: tools/call)...")
    try:
        result = await mcp_client.call_tool(
            tool_name="get_emails",
            arguments={
                "user_id": "me",
                "max_results": 5,
                "only_unread": False,
            }
        )

        content = result.get("content", [])
        is_error = result.get("isError", False)

        print(f"   Status: {'ERROR' if is_error else 'SUCCESS'}")
        print(f"   Content items: {len(content)}")

        if content:
            print("\n   Response content:")
            for i, item in enumerate(content[:2], 1):
                item_type = item.get("type", "unknown")
                if item_type == "text":
                    text = item.get("text", "")[:200]
                    print(f"   [{i}] Type: {item_type}")
                    print(f"       Text: {text}...")
                else:
                    print(f"   [{i}] Type: {item_type}")
                    print(f"       Data: {str(item)[:100]}...")

            # Try to parse as emails
            import json
            for item in content:
                if item.get("type") == "text":
                    try:
                        parsed = json.loads(item.get("text", ""))
                        if isinstance(parsed, dict) and "messages" in parsed:
                            messages = parsed["messages"]
                            print(f"\n   ✓ Successfully parsed {len(messages)} email messages!")
                            if messages:
                                print("\n   Sample email:")
                                msg = messages[0]
                                print(f"     From: {msg.get('from', 'N/A')}")
                                print(f"     Subject: {msg.get('subject', 'N/A')[:60]}")
                                print(f"     Date: {msg.get('date', 'N/A')}")
                        break
                    except Exception:
                        pass
        else:
            print("   ⚠️  No content returned")

    except Exception as e:
        print(f"   ✗ Error calling tool: {e}")

    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test())
