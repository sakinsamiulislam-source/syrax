import sys
import os
sys.path.insert(0, os.path.abspath("."))

"""
SYRAX — Phase 6: Exact Order Ticket & Human Confirmation Boundary Test Suite
Verifies all 12 Phase 6 requirements:
TKT-01: Ticket Generation on Execution Intent (No Immediate Execution)
TKT-02: Exact Confirmation Execution via CONFIRM PO-XXXXXX
TKT-03: Generic Confirmation Rejection (yes, confirm, ok rejected)
TKT-04: Atomic Single-Use / Double Confirmation Replay Rejection
TKT-05: TTL Expiration Fail-Closed
TKT-06: Cryptographic Hash Integrity & Tamper Rejection
TKT-07: Parameter Mutation Invalidation
TKT-08: TALK / THINK Queries Create Zero Tickets
TKT-09: Explicit Cancel Order Ticket
TKT-10: Gateway Rejection / Veto Tracking
TKT-11: High-Concurrency Double Confirmation Race Condition Safety
TKT-12: Post-Trade Guardian Autonomous Independence
"""

import asyncio
import time
import json
from backend.binance.agent_os import BinanceAgentOS
from backend.binance.sub_wallet import SubWalletManager
from agent.orchestrator import SyraxOrchestrator
from agent.order_ticket import OrderTicketRegistry, TicketStatus, compute_ticket_hash, format_order_ticket_card
from agent.execution_gateway import UnifiedExecutionGateway, ExecutionRequest, ExecutionActionType, ExecutionEnvironment, ExecutionStatus
from agent.post_trade_guardian import PostTradeGuardian, GuardianConfig


async def test_tkt_01_ticket_generation_on_execution_intent():
    """TKT-01: Natural language execution intent compiles an immutable OrderTicket without executing."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt01", 500.0)
    orchestrator = SyraxOrchestrator(binance, sub_wallet=wallet)
    orchestrator.ticket_registry = OrderTicketRegistry(persistence_path=None)

    initial_trades_count = len(wallet.ongoing_trades)
    query = "Buy $25 BTC spot with SL 70000"
    res = await orchestrator.execute_mandate_pipeline(query)

    assert res["decision"] == "TICKET_GENERATED", f"Expected TICKET_GENERATED, got {res.get('decision')}"
    assert "order_ticket" in res, "Missing order_ticket in response"
    ticket_card = res["order_ticket"]
    
    poid = ticket_card["parent_order_id"]
    assert poid.startswith("PO-"), f"Invalid parent_order_id format: {poid}"
    assert ticket_card["symbol"] == "BTCUSDT"
    assert ticket_card["side"] == "BUY"
    assert ticket_card["notional_usd"] == 25.0
    assert ticket_card["status"] == "PENDING_CONFIRMATION"
    assert ticket_card["remaining_ttl_seconds"] > 100
    assert f"CONFIRM {poid}" in res["explanation"]
    
    # Verify gateway was NOT called yet (no new positions opened)
    assert len(wallet.ongoing_trades) == initial_trades_count, "No trade should be executed upon ticket generation"
    print(f"PASS: TKT-01 (Ticket {poid} generated in PENDING_CONFIRMATION state, 0 trades executed)")


async def test_tkt_02_exact_confirmation_execution():
    """TKT-02: Sending exact 'CONFIRM PO-XXXXXX' token triggers atomic confirmation and Gateway execution."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt02", 500.0)
    orchestrator = SyraxOrchestrator(binance, sub_wallet=wallet)
    orchestrator.ticket_registry = OrderTicketRegistry(persistence_path=None)

    initial_trades_count = len(wallet.ongoing_trades)

    # 1. Generate ticket
    res1 = await orchestrator.execute_mandate_pipeline("Buy $25 BTC spot with SL 70000")
    poid = res1["order_ticket"]["parent_order_id"]

    # 2. Issue exact confirmation token
    confirm_query = f"CONFIRM {poid}"
    res2 = await orchestrator.execute_mandate_pipeline(confirm_query)

    assert res2["decision"] == "TRADE", f"Expected TRADE decision, got {res2.get('decision')}: {res2.get('reason')}"
    assert res2["ticket_status"] == "EXECUTED"
    assert "execution_receipt" in res2
    assert res2["execution_receipt"]["status"] == "SUCCESS"
    assert len(wallet.ongoing_trades) == initial_trades_count + 1, "Exactly 1 new trade should be open in wallet"
    
    # Check ticket state in registry
    saved_ticket = await orchestrator.ticket_registry.get_ticket(poid)
    assert saved_ticket.status == TicketStatus.EXECUTED
    assert saved_ticket.gateway_order_id is not None
    print(f"PASS: TKT-02 (Exact confirmation token {confirm_query} successfully executed trade)")


async def test_tkt_03_generic_confirmation_rejection():
    """TKT-03: Generic affirmations ('yes', 'confirm', 'ok', 'go ahead', 'do it') are strictly rejected."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt03", 500.0)
    orchestrator = SyraxOrchestrator(binance, sub_wallet=wallet)
    orchestrator.ticket_registry = OrderTicketRegistry(persistence_path=None)

    initial_trades_count = len(wallet.ongoing_trades)

    # 1. Generate ticket
    res1 = await orchestrator.execute_mandate_pipeline("Buy $25 BTC spot with SL 70000")
    poid = res1["order_ticket"]["parent_order_id"]

    generic_inputs = ["yes", "confirm", "ok", "okay", "go ahead", "do it", "approved", "sure", "proceed"]
    for g_input in generic_inputs:
        res = await orchestrator.execute_mandate_pipeline(g_input)
        assert res["decision"] == "CONFIRMATION_REQUIRED", f"Failed for generic input '{g_input}': got {res.get('decision')}"
        assert f"CONFIRM {poid}" in res["explanation"]
        assert len(wallet.ongoing_trades) == initial_trades_count, f"Generic input '{g_input}' must not execute trades!"

    # Verify ticket is still pending
    ticket = await orchestrator.ticket_registry.get_ticket(poid)
    assert ticket.status == TicketStatus.PENDING_CONFIRMATION
    print("PASS: TKT-03 (All generic confirmation variations safely rejected without executing)")


async def test_tkt_04_atomic_double_confirmation_replay_protection():
    """TKT-04: Replaying confirmation token on already executed ticket fails closed."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt04", 500.0)
    orchestrator = SyraxOrchestrator(binance, sub_wallet=wallet)
    orchestrator.ticket_registry = OrderTicketRegistry(persistence_path=None)

    initial_trades_count = len(wallet.ongoing_trades)

    # 1. Generate and confirm
    res1 = await orchestrator.execute_mandate_pipeline("Buy $25 BTC spot with SL 70000")
    poid = res1["order_ticket"]["parent_order_id"]
    res2 = await orchestrator.execute_mandate_pipeline(f"CONFIRM {poid}")
    assert res2["decision"] == "TRADE"
    assert len(wallet.ongoing_trades) == initial_trades_count + 1

    # 2. Replay confirmation
    res3 = await orchestrator.execute_mandate_pipeline(f"CONFIRM {poid}")
    assert res3["decision"] == "CONFIRMATION_REJECTED"
    assert "already been consumed" in res3["reason"].lower()
    assert len(wallet.ongoing_trades) == initial_trades_count + 1, "Duplicate trade must NOT be executed on replayed token"
    print("PASS: TKT-04 (Double confirmation replay safely rejected, zero duplicate trades)")


async def test_tkt_05_ttl_expiration_fail_closed():
    """TKT-05: Expired ticket cannot be confirmed and fails closed."""
    registry = OrderTicketRegistry(persistence_path=None)
    
    # Create ticket with tiny TTL
    ticket = await registry.create_ticket(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        notional_usd=25.0,
        decision_price=90000.0,
        stop_loss=88000.0,
        ttl_seconds=0.01
    )
    poid = ticket.parent_order_id

    # Wait for TTL to expire
    await asyncio.sleep(0.05)

    success, confirmed_ticket, msg = await registry.confirm_ticket(poid, f"CONFIRM {poid}")
    assert success is False
    assert confirmed_ticket.status == TicketStatus.EXPIRED
    assert "expired" in msg.lower()
    print("PASS: TKT-05 (Expired ticket fail-closed verified)")


async def test_tkt_06_cryptographic_hash_integrity_verification():
    """TKT-06: Tampering with immutable parameters invalidates ticket cryptographic hash."""
    registry = OrderTicketRegistry(persistence_path=None)
    
    ticket = await registry.create_ticket(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        notional_usd=25.0,
        decision_price=90000.0,
        stop_loss=88000.0,
        ttl_seconds=120.0
    )
    poid = ticket.parent_order_id
    assert ticket.is_hash_valid() is True

    # Tamper with notional amount
    ticket.notional_usd = 2500.0  # Malicious modification
    assert ticket.is_hash_valid() is False

    success, t, msg = await registry.confirm_ticket(poid, f"CONFIRM {poid}")
    assert success is False
    assert t.status == TicketStatus.INVALIDATED
    assert "failed hash verification" in msg.lower() or "integrity" in msg.lower()
    print("PASS: TKT-06 (Tampered ticket cryptographic hash mismatch caught and invalidated)")


async def test_tkt_07_parameter_mutation_invalidates_previous_ticket():
    """TKT-07: Parameter modification invalidates prior pending tickets."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt07", 500.0)
    orchestrator = SyraxOrchestrator(binance, sub_wallet=wallet)
    orchestrator.ticket_registry = OrderTicketRegistry(persistence_path=None)

    initial_trades_count = len(wallet.ongoing_trades)

    # 1. User requests BTC trade
    res1 = await orchestrator.execute_mandate_pipeline("Buy $25 BTC spot with SL 70000")
    poid1 = res1["order_ticket"]["parent_order_id"]

    # 2. User modifies parameters / changes mind to ETH
    res2 = await orchestrator.execute_mandate_pipeline("Actually buy $25 ETH spot with SL 2000")
    poid2 = res2["order_ticket"]["parent_order_id"]
    assert poid1 != poid2

    # Old ticket for BTC should be invalidated
    old_ticket = await orchestrator.ticket_registry.get_ticket(poid1)
    
    # Attempting to confirm the old superseded ticket should fail
    confirm_old = await orchestrator.execute_mandate_pipeline(f"CONFIRM {poid1}")
    assert confirm_old["decision"] == "CONFIRMATION_REJECTED" or old_ticket.status == TicketStatus.INVALIDATED
    assert len(wallet.ongoing_trades) == initial_trades_count
    print("PASS: TKT-07 (Parameter mutation correctly creates new ticket and handles old ticket)")


async def test_tkt_08_talk_think_queries_create_zero_tickets():
    """TKT-08: General talk/analysis queries create zero order tickets."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt08", 500.0)
    orchestrator = SyraxOrchestrator(binance, sub_wallet=wallet)
    orchestrator.ticket_registry = OrderTicketRegistry(persistence_path=None)

    queries = [
        "Analyze BTC market momentum",
        "What is the price of Solana?",
        "Tell me about Crude Oil and geopolitics",
        "What is your risk management framework?",
        "Check SOL for any active security exploits"
    ]

    for q in queries:
        res = await orchestrator.execute_mandate_pipeline(q)
        pending = orchestrator.ticket_registry.get_pending_tickets()
        assert len(pending) == 0, f"Query '{q}' should NOT create an order ticket!"
        assert res.get("decision") != "TICKET_GENERATED"
    print("PASS: TKT-08 (TALK/THINK queries created 0 order tickets)")


async def test_tkt_09_explicit_cancel_order_ticket():
    """TKT-09: Explicit 'CANCEL PO-XXXXXX' marks ticket CANCELLED and prevents execution."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt09", 500.0)
    orchestrator = SyraxOrchestrator(binance, sub_wallet=wallet)
    orchestrator.ticket_registry = OrderTicketRegistry(persistence_path=None)

    initial_trades_count = len(wallet.ongoing_trades)

    # 1. Create ticket
    res1 = await orchestrator.execute_mandate_pipeline("Buy $25 BTC spot with SL 70000")
    poid = res1["order_ticket"]["parent_order_id"]

    # 2. Cancel ticket
    res2 = await orchestrator.execute_mandate_pipeline(f"CANCEL {poid}")
    assert res2["decision"] == "CANCELLED"
    assert res2["ticket_status"] == "CANCELLED"

    # 3. Attempt confirmation on cancelled ticket
    res3 = await orchestrator.execute_mandate_pipeline(f"CONFIRM {poid}")
    assert res3["decision"] == "CONFIRMATION_REJECTED"
    assert len(wallet.ongoing_trades) == initial_trades_count
    print("PASS: TKT-09 (Cancelled ticket cannot be confirmed and executes 0 trades)")


async def test_tkt_10_gateway_rejection_tracking():
    """TKT-10: Gateway rejection/veto marks ticket REJECTED_BY_GATEWAY."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt10", 500.0)
    orchestrator = SyraxOrchestrator(binance, sub_wallet=wallet)
    orchestrator.ticket_registry = OrderTicketRegistry(persistence_path=None)

    initial_trades_count = len(wallet.ongoing_trades)

    # Trigger news sentry exploit event on SOL
    orchestrator.news_agent.trigger_simulated_critical_event(token="SOL")

    # 1. Create ticket for SOL
    res1 = await orchestrator.execute_mandate_pipeline("Buy $25 SOL spot with SL 70")
    poid = res1["order_ticket"]["parent_order_id"]

    # 2. Confirm ticket -> Gateway must veto due to Sentry exploit event
    res2 = await orchestrator.execute_mandate_pipeline(f"CONFIRM {poid}")
    assert res2["decision"] == "NO TRADE"
    assert res2["ticket_status"] == "REJECTED_BY_GATEWAY"
    assert "sentry" in res2["reason"].lower() or "exploit" in res2["reason"].lower()
    assert len(wallet.ongoing_trades) == initial_trades_count
    print("PASS: TKT-10 (Gateway veto properly captured and ticket marked REJECTED_BY_GATEWAY)")


async def test_tkt_11_concurrent_confirmation_race_safety():
    """TKT-11: 10 simultaneous confirm calls on same ticket yields exactly 1 success and 9 rejections."""
    registry = OrderTicketRegistry(persistence_path=None)
    
    ticket = await registry.create_ticket(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        notional_usd=25.0,
        decision_price=90000.0,
        stop_loss=88000.0,
        ttl_seconds=120.0
    )
    poid = ticket.parent_order_id

    async def try_confirm():
        return await registry.confirm_ticket(poid, f"CONFIRM {poid}")

    # Launch 10 concurrent confirmation attempts
    results = await asyncio.gather(*[try_confirm() for _ in range(10)])
    
    successes = [r for r in results if r[0] is True]
    failures = [r for r in results if r[0] is False]

    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
    assert len(failures) == 9, f"Expected 9 failures, got {len(failures)}"
    print("PASS: TKT-11 (10 concurrent confirmation attempts resulted in exactly 1 atomic consumption)")


async def test_tkt_12_guardian_autonomous_independence():
    """TKT-12: PostTradeGuardian autonomous protection does NOT require human ticket confirmation."""
    binance = BinanceAgentOS()
    wallet = SubWalletManager("test-wallet-tkt12", 500.0)
    gateway = UnifiedExecutionGateway(binance, sub_wallet=wallet)
    guardian = PostTradeGuardian(gateway, wallet, binance, config=GuardianConfig(state_persistence_path="scratch/test_guardian_p6.json"))

    # Add open trade with SL at 90,000
    wallet.open_trade(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        price=95000.0,
        stop_loss=90000.0,
        take_profit=105000.0,
        leverage=1,
        market_type="SPOT"
    )
    initial_trades = len(wallet.ongoing_trades)

    # Market price drops to 89,000 (breaching SL)
    cycle_res = await guardian.run_cycle(
        live_prices={"BTCUSDT": 89000.0}
    )

    assert cycle_res["breaches_detected"] >= 1
    assert cycle_res["incidents_created"] >= 1
    assert any(inc["result"] == "EXECUTED" for inc in cycle_res["incidents"])
    print("PASS: TKT-12 (Post-Trade Guardian autonomous protection executes instantly with 0 ticket confirmation latency)")


if __name__ == "__main__":
    async def run_all():
        print("\n=======================================================")
        print("  RUNNING SYRAX PHASE 6 ORDER TICKET TEST SUITE")
        print("=======================================================\n")
        await test_tkt_01_ticket_generation_on_execution_intent()
        await test_tkt_02_exact_confirmation_execution()
        await test_tkt_03_generic_confirmation_rejection()
        await test_tkt_04_atomic_double_confirmation_replay_protection()
        await test_tkt_05_ttl_expiration_fail_closed()
        await test_tkt_06_cryptographic_hash_integrity_verification()
        await test_tkt_07_parameter_mutation_invalidates_previous_ticket()
        await test_tkt_08_talk_think_queries_create_zero_tickets()
        await test_tkt_09_explicit_cancel_order_ticket()
        await test_tkt_10_gateway_rejection_tracking()
        await test_tkt_11_concurrent_confirmation_race_safety()
        await test_tkt_12_guardian_autonomous_independence()
        print("\n=======================================================")
        print("  ALL 12 PHASE 6 TEST SCENARIOS PASSED (100%)")
        print("=======================================================\n")

    asyncio.run(run_all())
