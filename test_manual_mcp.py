"""Test manual MCP calls to match the working curl sequence."""
import asyncio
import httpx

async def test():
    API_KEY = "IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ"
    BASE_URL = "https://n8n.davidbuitrago.dev/mcp/gmail"

    print("=" * 70)
    print("Manual MCP Test - Replicating curl sequence")
    print("=" * 70)

    # Step 1: GET /sse to get sessionId
    print("\n1. GET /sse")
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(
            f"{BASE_URL}/sse",
            headers={"X-API-KEY": API_KEY},
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        # Extract sessionId
        session_id = None
        if "sessionId=" in response.text:
            session_id = response.text.split("sessionId=")[1].split()[0].strip()
            print(f"   ✓ Session ID: {session_id}")

    if not session_id:
        print("   ✗ Failed to get sessionId")
        return

    # Step 2: POST initialize
    print("\n2. POST /messages?sessionId={session_id} - Initialize")
    messages_url = f"{BASE_URL}/messages?sessionId={session_id}"

    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            messages_url,
            json=init_request,
            headers={
                "X-API-KEY": API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Response: {response.text[:300]}")

        # Extract Mcp-Session-Id
        mcp_session_id = response.headers.get("Mcp-Session-Id") or response.headers.get("mcp-session-id")
        if mcp_session_id:
            print(f"   ✓ MCP Session ID: {mcp_session_id[:20]}...")
        else:
            print("   ✗ No MCP Session ID in headers")
            return

    # Step 3: POST tools/list
    print("\n3. POST /messages?sessionId={session_id} - List Tools")

    list_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            messages_url,
            json=list_request,
            headers={
                "X-API-KEY": API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": mcp_session_id,
            },
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:500]}")

        if response.status_code == 200:
            print("   ✓ SUCCESS!")
        else:
            print(f"   ✗ FAILED with status {response.status_code}")

    print("\n" + "=" * 70)
    print("Test completed")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test())
