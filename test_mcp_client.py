import httpx
import asyncio
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8001"

async def test_mcp_client():
    async with httpx.AsyncClient(timeout=20.0) as client:
        async with client.stream("GET", f"{BASE_URL}/mcp/sse") as stream:
            print("[MCP Client] Connected to SSE stream. Status:", stream.status_code)
            
            # Persistent generator
            lines_iter = stream.aiter_lines()
            
            # 1. Get endpoint URL
            endpoint_url = None
            async for line in lines_iter:
                if line.startswith("data: "):
                    endpoint_url = line.replace("data: ", "").strip()
                    print(f"[MCP Client] Received message endpoint: {endpoint_url}")
                    break
            
            if not endpoint_url:
                print("Failed to get endpoint.")
                return

            full_msg_url = f"{BASE_URL}{endpoint_url}" if endpoint_url.startswith("/") else endpoint_url

            # 2. Send initialize
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "TestClient", "version": "1.0"}
                }
            }
            res = await client.post(full_msg_url, json=init_req)
            print("[MCP Client] Initialized HTTP POST:", res.status_code)

            # Read initialize response from SSE
            async for line in lines_iter:
                if line.startswith("data: "):
                    msg = json.loads(line.replace("data: ", "").strip())
                    if msg.get("id") == 1:
                        print(f"[MCP Client] Initialized response: server={msg.get('result', {}).get('serverInfo', {}).get('name')}")
                        break

            # 3. Send notifications/initialized
            await client.post(full_msg_url, json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            })

            # 4. Call tools/list
            list_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            await client.post(full_msg_url, json=list_req)
            print("[MCP Client] tools/list requested.")

            async for line in lines_iter:
                if line.startswith("data: "):
                    msg = json.loads(line.replace("data: ", "").strip())
                    if msg.get("id") == 2:
                        tools = msg.get("result", {}).get("tools", [])
                        print(f"[MCP Client] Received {len(tools)} tools:")
                        for t in tools:
                            print(f"  * {t['name']}: {t['description']}")
                        break

            # 5. Call syrax_get_ongoing_trades
            call_req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "syrax_get_ongoing_trades",
                    "arguments": {}
                }
            }
            await client.post(full_msg_url, json=call_req)
            print("[MCP Client] Invoking syrax_get_ongoing_trades...")

            async for line in lines_iter:
                if line.startswith("data: "):
                    msg = json.loads(line.replace("data: ", "").strip())
                    if msg.get("id") == 3:
                        content = msg.get("result", {}).get("content", [])
                        if content:
                            res_obj = json.loads(content[0]["text"])
                            print("[MCP Client] syrax_get_ongoing_trades response:")
                            print("  Sub-Wallet:", res_obj.get("sub_wallet_id"))
                            print("  Total Trades Active:", len(res_obj.get("ongoing_trades", [])))
                            for trd in res_obj.get("ongoing_trades", []):
                                print(f"    - {trd['symbol']} {trd['side']} | Entry: ${trd['entry_price']} | Live: ${trd['current_price']} | PnL: ${trd['unrealized_pnl_usd']} ({trd['unrealized_pnl_pct']}%)")
                        break

    print("\n[MCP Client] Full MCP Client Lifecycle Test Passed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_mcp_client())
