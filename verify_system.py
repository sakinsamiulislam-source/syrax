import httpx
import asyncio
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_BACKEND = "http://127.0.0.1:8001"
BASE_FRONTEND = "http://127.0.0.1:3001"

async def test_full_system():
    async with httpx.AsyncClient(timeout=15.0) as client:
        print("=== 1. Testing Frontend (Next.js 14) ===")
        res = await client.get(BASE_FRONTEND)
        print(f"Frontend Status: {res.status_code}")
        assert res.status_code == 200, "Frontend is not returning 200"

        print("\n=== 2. Testing Sub-Wallet Telemetry ===")
        res = await client.get(f"{BASE_BACKEND}/api/subwallet")
        data = res.json()
        analysis = data.get("analysis", {})
        print(f"Sub-Wallet ID: {analysis.get('sub_wallet_id')}")
        print(f"Total Portfolio Value: ${analysis.get('total_portfolio_value_usd')}")
        print(f"Available Cash: ${analysis.get('available_cash_usd')}")
        print(f"Ongoing Trades Count: {len(data.get('ongoing_trades', []))}")
        print(f"Holdings Count: {len(analysis.get('holdings', []))}")

        print("\n=== 3. Testing Sub-Wallet Order Execution ===")
        order_payload = {
            "symbol": "1000PEPEUSDT",
            "side": "BUY",
            "notional_usd": 20.0
        }
        res = await client.post(f"{BASE_BACKEND}/api/subwallet/order", json=order_payload)
        order_res = res.json()
        print("Order Placement Result:", order_res)
        assert order_res.get("success") == True, "Failed to place sub-wallet order"
        trade = order_res.get("trade")
        trade_id = trade["trade_id"]
        print(f"Placed Trade ID: {trade_id}, Symbol: {trade['symbol']}, Qty: {trade['quantity']}")

        print("\n=== 4. Testing Sub-Wallet Telemetry After Order ===")
        res = await client.get(f"{BASE_BACKEND}/api/subwallet")
        data = res.json()
        trade_ids = [t["trade_id"] for t in data.get("ongoing_trades", [])]
        print(f"Ongoing Trade IDs: {trade_ids}")
        assert trade_id in trade_ids, f"Trade {trade_id} not found in ongoing trades"

        print("\n=== 5. Testing Sub-Wallet Trade Close ===")
        res = await client.post(f"{BASE_BACKEND}/api/subwallet/trade/close", json={"trade_id": trade_id, "reason": "Verification Close"})
        close_res = res.json()
        print("Close Trade Result:", close_res)
        assert close_res.get("success") == True, "Failed to close trade"

        print("\n=== 6. Testing 24/7 Autonomous Sentinel Status ===")
        res = await client.get(f"{BASE_BACKEND}/api/monitor/status")
        mon = res.json()
        print(f"Sentinel Running: {mon.get('is_running')}, Paused: {mon.get('is_paused')}")
        print(f"Total Checks: {mon.get('total_checks')}, Active Monitored: {mon.get('active_monitored_trades')}")
        print(f"Recent Events Buffered: {len(mon.get('events', []))}")
        if mon.get("events"):
            print("Latest Event:", mon["events"][0]["message"])

        print("\n=== 7. Testing 24/7 Sentinel Pause / Resume Toggle ===")
        res = await client.post(f"{BASE_BACKEND}/api/monitor/toggle")
        toggled = res.json()
        print(f"After Toggle 1 (Paused): {toggled.get('is_paused')}")
        res = await client.post(f"{BASE_BACKEND}/api/monitor/toggle")
        resumed = res.json()
        print(f"After Toggle 2 (Resumed): {resumed.get('is_paused')}")
        assert resumed.get("is_paused") == False, "Sentinel did not resume"

        print("\n=== 8. Testing Model Context Protocol (MCP) Info ===")
        res = await client.get(f"{BASE_BACKEND}/api/mcp/info")
        mcp = res.json()
        print(f"MCP URL: {mcp.get('mcp_url')}")
        print(f"Exposed Tools: {[t['name'] for t in mcp.get('tools', [])]}")
        assert len(mcp.get("tools", [])) >= 7, "Missing expected MCP tools"

        print("\n=== 9. Testing MCP SSE Stream Connection ===")
        async with client.stream("GET", f"{BASE_BACKEND}/mcp/sse") as stream:
            print(f"SSE Status Code: {stream.status_code}")
            print(f"SSE Content-Type: {stream.headers.get('content-type')}")
            assert stream.status_code == 200, "SSE endpoint did not return 200"
            lines_read = 0
            async for line in stream.aiter_lines():
                if line:
                    print(f"SSE Stream Chunk: {line}")
                    lines_read += 1
                    if lines_read >= 2:
                        break

    print("\n✅ ALL SYSTEM VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_full_system())
