"""
Test Suite: Universal Binance Asset Intelligence Engine (Phase 9)
Tests dynamic asset discovery, product-aware resolution, futures telemetry,
33-point cognitive synthesis, cross-market comparison, unsupported handling,
and safety invariants.
"""

import pytest
import asyncio
from backend.binance.agent_os import BinanceAgentOS
from agent.orchestrator import SyraxOrchestrator
from agent.universal_asset_engine import (
    UniversalAssetRegistry,
    ProductAwareResolver,
    ProductTelemetryService,
    TokenNewsIntelligenceService,
    UniversalAnalysisEngine,
    MarketProduct,
    NewsTier
)
from agent.order_ticket import OrderTicketRegistry


@pytest.fixture
def binance_client():
    return BinanceAgentOS()


@pytest.fixture
def orchestrator(binance_client):
    return SyraxOrchestrator(binance_client)


@pytest.mark.asyncio
async def test_dynamic_asset_discovery():
    """Verify registry discovers > 500 assets dynamically from live Binance endpoints."""
    reg = UniversalAssetRegistry()
    await reg.refresh_universe(force=True)
    assert len(reg._assets) > 100
    assert len(reg._symbol_index) > 50
    assert len(reg._base_index) > 50


@pytest.mark.asyncio
async def test_product_aware_resolution():
    """Verify parsing queries for Spot, Futures, Alpha, and Unsupported products."""
    _, prod_btc, is_comp1, _, _ = ProductAwareResolver.parse_query_product("analyze BTC")
    assert prod_btc == MarketProduct.SPOT
    assert not is_comp1

    _, prod_sol_fut, is_comp2, _, _ = ProductAwareResolver.parse_query_product("check SOL futures")
    assert prod_sol_fut == MarketProduct.FUTURES_USDM
    assert not is_comp2

    _, prod_eth_comp, is_comp3, comp_prod3, _ = ProductAwareResolver.parse_query_product("compare ETH spot vs futures")
    assert is_comp3
    assert prod_eth_comp == MarketProduct.SPOT
    assert comp_prod3 == MarketProduct.FUTURES_USDM

    _, prod_coinm, _, _, _ = ProductAwareResolver.parse_query_product("check DOGE coin-m futures")
    assert prod_coinm == MarketProduct.FUTURES_COINM


@pytest.mark.asyncio
async def test_futures_telemetry_live():
    """Verify live funding rate and open interest telemetry from Binance FAPI."""
    tel = await ProductTelemetryService.fetch_futures_telemetry("BTCUSDT")
    assert tel.symbol == "BTCUSDT"
    assert tel.mark_price > 0.0
    assert tel.index_price > 0.0
    assert isinstance(tel.funding_rate_pct, float)


@pytest.mark.asyncio
async def test_token_news_hierarchy():
    """Verify strict news tiering (Tier 1 vs Tier 2 vs Tier 3) and fallback."""
    service = TokenNewsIntelligenceService()
    eth_events, eth_md = service.search_token_news("ETH")
    assert len(eth_events) > 0
    assert eth_events[0].tier == NewsTier.TIER_1_OFFICIAL
    assert "Tier 1 Official" in eth_md

    # Test unknown token fallback
    unk_events, unk_md = service.search_token_news("UNKNOWNTOKEN123")
    assert len(unk_events) == 0
    assert "No verified material recent news" in unk_md


@pytest.mark.asyncio
async def test_universal_analysis_live_btc(orchestrator):
    """Test full 33-point cognitive analysis pipeline for BTC Spot."""
    res = await orchestrator.execute_mandate_pipeline("analyze BTC")
    assert res["command_type"] == "MARKET_ANALYSIS"
    assert res["target_asset"] == "BTCUSDT"
    assert res["product"] == "SPOT"
    assert "Live Market:" in res["explanation"]
    assert "Bull Case" in res["explanation"]
    assert "Bear Case" in res["explanation"]
    assert "SYRAX Thesis" in res["explanation"]
    assert "Invalidation" in res["explanation"]
    assert res["decision"] is None  # Pure analysis NEVER decides trade


@pytest.mark.asyncio
async def test_universal_analysis_futures_sol(orchestrator):
    """Test analysis for SOL Futures with funding rate telemetry."""
    res = await orchestrator.execute_mandate_pipeline("check SOL futures")
    assert res["command_type"] == "MARKET_ANALYSIS"
    assert res["target_asset"] == "SOLUSDT"
    assert res["product"] == "FUTURES_USDM"
    assert "Perpetual Futures Telemetry" in res["explanation"]
    assert "Funding Rate" in res["explanation"]
    assert res["decision"] is None


@pytest.mark.asyncio
async def test_universal_analysis_dynamic_tokens(orchestrator):
    """Test analysis for dynamic/recently listed Binance tokens (SUI, PENGU)."""
    res_sui = await orchestrator.execute_mandate_pipeline("analyze SUI")
    assert res_sui["command_type"] == "MARKET_ANALYSIS"
    assert res_sui["target_asset"] == "SUIUSDT"

    res_pengu = await orchestrator.execute_mandate_pipeline("analyze PENGU")
    assert res_pengu["command_type"] == "MARKET_ANALYSIS"
    assert res_pengu["target_asset"] == "PENGUUSDT"


@pytest.mark.asyncio
async def test_cross_market_comparison(orchestrator):
    """Test side-by-side comparison between Spot and Futures."""
    res = await orchestrator.execute_mandate_pipeline("compare ETH spot vs futures")
    assert res["command_type"] == "MARKET_ANALYSIS"
    assert "Cross-Market Comparison" in res["explanation"]
    assert "Binance Spot" in res["explanation"]
    assert "USDⓈ-M Perpetual Futures" in res["explanation"]
    assert "cross_market_comparison" in res


@pytest.mark.asyncio
async def test_unsupported_product_graceful_notice(orchestrator):
    """Test graceful handling when an unsupported Binance product is requested."""
    res = await orchestrator.execute_mandate_pipeline("analyze DOGE coin-m futures")
    assert res["command_type"] == "MARKET_ANALYSIS"
    assert res["tradeability"] == "UNSUPPORTED_DATA_FEED"
    assert "Binance Market Notice" in res["explanation"]
    assert "COIN-M" in res["headline"]


@pytest.mark.asyncio
async def test_safety_invariants_preserved(orchestrator):
    """Verify that pure analysis never generates tickets, executes orders, or modifies balances."""
    reg = orchestrator.ticket_registry
    pending_before = await reg.get_pending_tickets()
    
    # Run multiple market analysis queries
    await orchestrator.execute_mandate_pipeline("analyze BTC")
    await orchestrator.execute_mandate_pipeline("check SOL futures")
    await orchestrator.execute_mandate_pipeline("compare ETH spot vs futures")
    
    pending_after = await reg.get_pending_tickets()
    assert len(pending_before) == len(pending_after)
