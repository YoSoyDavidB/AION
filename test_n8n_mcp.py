"""Test N8N MCP integration."""
import asyncio
from src.infrastructure.mcp import MCPN8NClient
from src.config.settings import get_settings


async def test():
    print("=" * 70)
    print("N8N MCP Integration Test")
    print("=" * 70)

    settings = get_settings()

    # Remove /sse from URL for N8N client
    base_url = settings.mcp.n8n_mcp_gmail_base_url.replace("/sse", "")

    print("\n1. Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   Header: {settings.mcp.n8n_mcp_header_name}")
    print(f"   Has Auth: {bool(settings.mcp.n8n_mcp_header_value)}")

    # Create N8N MCP client
    print("\n2. Creating N8N MCP client...")
    client = MCPN8NClient(
        base_url=base_url,
        auth_header_name=settings.mcp.n8n_mcp_header_name,
        auth_header_value=settings.mcp.n8n_mcp_header_value,
    )
    print("   ✓ Client created")

    # Test initialization
    print("\n3. Initializing session...")
    try:
        async with client:
            print(f"   ✓ Session initialized!")
            print(f"   Session ID: {client.session_id}")
            print(f"   MCP Session ID: {client.mcp_session_id[:20]}...")

            # List tools
            print("\n4. Listing tools...")
            tools = await client.list_tools()
            print(f"   ✓ Found {len(tools)} tools:")
            for tool in tools[:5]:
                print(f"     - {tool.get('name')}")

            # Test search tool
            print("\n5. Testing 'search' tool (get unread emails)...")
            result = await client.call_tool(
                tool_name="search",
                arguments={
                    "Return_All": False,
                    "Search": "is:unread",
                    "Received_After": "",
                    "Received_Before": "",
                    "Sender": "",
                }
            )

            content = result.get("content", [])
            is_error = result.get("isError", False)

            print(f"   Status: {'ERROR' if is_error else 'SUCCESS'}")
            print(f"   Content items: {len(content)}")

            if content:
                for i, item in enumerate(content, 1):
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        print(f"   [{i}] Text length: {len(text)} chars")

                        # Try to parse JSON
                        import json
                        try:
                            emails = json.loads(text)
                            if isinstance(emails, list):
                                print(f"   ✓ Parsed {len(emails)} emails!")
                                if emails:
                                    email = emails[0]
                                    print(f"\n   Sample email:")
                                    print(f"     Subject: {email.get('Subject', 'N/A')[:60]}")
                                    print(f"     From: {email.get('From', 'N/A')}")
                                    print(f"     Snippet: {email.get('snippet', 'N/A')[:80]}")
                        except json.JSONDecodeError:
                            print(f"   Text preview: {text[:200]}...")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test())
