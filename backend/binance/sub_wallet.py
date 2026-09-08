"""

SYRAX — Agentic Sub-Wallet & Position Engine

Manages delegated sub-wallet capital, pending limit orders, ongoing derivative trades,

event-based partial and full fills, asset/cash reservation accounting, and live Unrealized PnL.

"""

import time

import uuid

import logging

from typing import Dict, Any, List, Optional

logger = logging.getLogger("syrax.sub_wallet")

class SubWalletManager:

    """

    Agentic Sub-Wallet & Position Manager.

    Isolates delegated trading funds, enforces strict order reservation accounting,

    executes discrete event-driven fills, and provides transparent portfolio telemetry.

    """

    def __init__(self, sub_wallet_id: str = "SUB-AGENT-01-ALPHA", allocated_budget_usd: float = 500.0):

        self.sub_wallet_id = sub_wallet_id

        self.allocated_budget_usd = allocated_budget_usd

        self.cash_usd = 250.0  # Liquid free USDT cash margin

        # Holdings in the sub-wallet (asset -> {free, locked})

        self.holdings: Dict[str, Dict[str, float]] = {

            "USDT": {"free": 250.0, "locked": 0.0},

            "BTC": {"free": 0.0016, "locked": 0.0},   # ~$126

            "ETH": {"free": 0.028, "locked": 0.0},    # ~$69

            "SOL": {"free": 0.20, "locked": 0.0},     # ~$21

            "USDC": {"free": 12.50, "locked": 0.0},   # Idle cash

        }

        # Multi-Wallet Binance Ecosystem Accounting (Spot, Funding, USD-M Futures, Coin-M Futures, Margin, Earn)

        self.wallets: Dict[str, Dict[str, Any]] = {

            "SPOT": {

                "wallet_id": "SPOT",

                "name": "Fiat & Spot",

                "badge": "SPOT",

                "description": "Main Spot trading, deposits, and token conversion account",

                "icon": "Wallet",

                "balances": {

                    "USDT": {"free": 250.0, "locked": 0.0},

                    "BTC": {"free": 0.0016, "locked": 0.0},

                    "ETH": {"free": 0.028, "locked": 0.0},

                    "SOL": {"free": 0.20, "locked": 0.0},

                    "USDC": {"free": 12.50, "locked": 0.0},

                }

            },

            "FUNDING": {

                "wallet_id": "FUNDING",

                "name": "Funding Wallet",

                "badge": "FUNDING",

                "description": "P2P trading, Binance Pay, crypto card, and merchant settlements",

                "icon": "Coins",

                "balances": {

                    "USDT": {"free": 50.0, "locked": 0.0},

                    "FDUSD": {"free": 25.0, "locked": 0.0},

                    "BNB": {"free": 0.08, "locked": 0.0},

                }

            },

            "USDT_FUTURES": {

                "wallet_id": "USDT_FUTURES",

                "name": "USD(S)-M Futures",

                "badge": "USD-M",

                "description": "Perpetual & delivery contracts with USDT/USDC collateral",

                "icon": "TrendingUp",

                "balances": {

                    "USDT": {"free": 40.0, "locked": 7.89},

                    "USDC": {"free": 10.0, "locked": 0.0},

                }

            },

            "COIN_FUTURES": {

                "wallet_id": "COIN_FUTURES",

                "name": "Coin-M Futures",

                "badge": "COIN-M",

                "description": "Coin-margined contracts settled directly in underlying crypto",

                "icon": "Zap",

                "balances": {

                    "BTC": {"free": 0.00045, "locked": 0.0},

                    "ETH": {"free": 0.008, "locked": 0.0},

                }

            },

            "CROSS_MARGIN": {
                "wallet_id": "CROSS_MARGIN",
                "name": "Cross Margin (3x/5x)",
                "badge": "MARGIN",
                "description": "Unified collateral risk pool for leveraged spot margin trading",
                "icon": "Layers",
                "balances": {
                    "USDT": {"free": 20.0, "locked": 0.0},
                    "BTC": {"free": 0.0002, "locked": 0.0},
                }
            }
        }

        # Internal transfer history

        self.internal_transfers: List[Dict[str, Any]] = [

            {

                "transfer_id": "XFER-INIT-001",

                "from_wallet": "SPOT",

                "to_wallet": "USDT_FUTURES",

                "asset": "USDT",

                "amount": 40.0,

                "fee": 0.0,

                "status": "CONFIRMED",

                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time() - 86400)),

                "tx_hash": "INT-983172640192"

            }

        ]

        # Target portfolio allocation percentages

        self.target_allocations: Dict[str, float] = {

            "USDT": 0.40,

            "BTC": 0.30,

            "ETH": 0.15,

            "SOL": 0.10,

            "USDC": 0.05,

        }

        # Active Pending Orders (Limit Orders awaiting market fill)

        self.pending_orders: List[Dict[str, Any]] = []

        # Ongoing active derivative trades / positions (FUTURES / MARGIN)

        self.ongoing_trades: List[Dict[str, Any]] = [

            {

                "trade_id": "TRD-FUT-BTC-INIT",

                "symbol": "BTCUSDT",

                "side": "BUY",

                "entry_price": 78200.00,

                "quantity": 0.001,

                "current_price": 78920.00,

                "notional_usd": 78.92,

                "margin_usd": 7.89,

                "leverage": 10,

                "margin_type": "ISOLATED",

                "liquidation_price": 70771.00,

                "funding_rate": 0.0001,

                "unrealized_pnl_usd": 0.72,

                "unrealized_pnl_pct": 0.92,

                "roe_pct": 9.20,

                "stop_loss": 76500.00,

                "take_profit": 81500.00,

                "market_type": "FUTURES",

                "status": "OPEN",

                "health": "IN_PROFIT",

                "opened_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time() - 3600)),

                "strategy": "Futures Momentum Trend Rider"

            },

            {

                "trade_id": "TRD-SPT-SOL-INIT",

                "symbol": "SOLUSDT",

                "side": "BUY",

                "entry_price": 102.50,

                "quantity": 0.20,

                "current_price": 104.67,

                "notional_usd": 20.93,

                "margin_usd": 20.93,

                "leverage": 1,

                "margin_type": "CROSS",

                "liquidation_price": 0.0,

                "funding_rate": None,

                "unrealized_pnl_usd": 0.43,

                "unrealized_pnl_pct": 2.12,

                "roe_pct": 2.12,

                "stop_loss": 99.80,

                "take_profit": 109.50,

                "market_type": "SPOT",

                "status": "OPEN",

                "health": "HEALTHY",

                "opened_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time() - 7200)),

                "strategy": "Spot Accumulation"

            },

            {

                "trade_id": "TRD-MRG-ETH-INIT",

                "symbol": "ETHUSDT",

                "side": "BUY",

                "entry_price": 2465.00,

                "quantity": 0.015,

                "current_price": 2483.10,

                "notional_usd": 37.25,

                "margin_usd": 12.42,

                "leverage": 3,

                "margin_type": "ISOLATED",

                "liquidation_price": 1655.00,

                "funding_rate": None,

                "unrealized_pnl_usd": 0.27,

                "unrealized_pnl_pct": 0.73,

                "roe_pct": 2.19,

                "stop_loss": 2415.00,

                "take_profit": 2580.00,

                "market_type": "MARGIN",

                "status": "OPEN",

                "health": "HEALTHY",

                "opened_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time() - 14400)),

                "strategy": "Margin Mean Reversion"

            }

        ]

        # Closed trade and cancelled order history

        self.closed_trades: List[Dict[str, Any]] = []

        # Chronological executed trade & order activity log

        self.trade_history: List[Dict[str, Any]] = [

            {

                "order_id": "ORD-FUT-BTC-9A4B21",

                "trade_id": "TRD-FUT-BTC-INIT",

                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time() - 3600)),

                "symbol": "BTCUSDT",

                "market_type": "FUTURES",

                "side": "BUY",

                "term": "LONG 10x",

                "price": 78200.00,

                "quantity": 0.001,

                "notional_usd": 78.20,

                "margin_usd": 7.82,

                "leverage": 10,

                "fee_usd": 0.0391,

                "fee_rate_pct": 0.05,

                "fee_breakdown": "$0.0391 USDT (0.05% Futures Taker Fee)",

                "status": "FILLED",

                "type": "OPEN",

                "notes": "Futures 10x Long order filled @ $78,200.00"

            },

            {

                "order_id": "ORD-SPO-SOL-3C81D2",

                "trade_id": "TRD-SPT-SOL-INIT",

                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time() - 7200)),

                "symbol": "SOLUSDT",

                "market_type": "SPOT",

                "side": "BUY",

                "term": "SPOT BUY",

                "price": 102.50,

                "quantity": 0.20,

                "notional_usd": 20.50,

                "margin_usd": 20.50,

                "leverage": 1,

                "fee_usd": 0.0205,

                "fee_rate_pct": 0.10,

                "fee_breakdown": "$0.0205 USDT (0.10% Binance Spot Fee)",

                "status": "FILLED",

                "type": "OPEN",

                "notes": "Spot Buy order filled @ $102.50"

            },

            {

                "order_id": "ORD-MRG-ETH-5E7F90",

                "trade_id": "TRD-MRG-ETH-INIT",

                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(time.time() - 14400)),

                "symbol": "ETHUSDT",

                "market_type": "MARGIN",

                "side": "BUY",

                "term": "MARGIN BUY 3x",

                "price": 2465.00,

                "quantity": 0.015,

                "notional_usd": 36.98,

                "margin_usd": 12.33,

                "leverage": 3,

                "fee_usd": 0.0370,

                "fee_rate_pct": 0.10,

                "fee_breakdown": "$0.0370 USDT (0.10% Margin Fee)",

                "status": "FILLED",

                "type": "OPEN",

                "notes": "Margin 3x Isolated Buy order filled @ $2,465.00"

            }

        ]

    def update_live_prices(self, price_map: Dict[str, float]):

        """

        Updates ongoing trades and pending orders with live prices from Binance.

        Recalculates mark-to-market Unrealized PnL, ROE%, and order distance.

        """

        for trade in self.ongoing_trades:

            sym = trade["symbol"]

            curr_price = price_map.get(sym, trade.get("current_price", trade.get("entry_price", 100.0)))

            trade["current_price"] = curr_price

            entry = trade["entry_price"]

            qty = trade["quantity"]

            side = trade["side"]

            if side == "BUY":

                pnl_usd = (curr_price - entry) * qty

                pnl_pct = ((curr_price - entry) / entry) * 100 if entry > 0 else 0.0

            else:

                pnl_usd = (entry - curr_price) * qty

                pnl_pct = ((entry - curr_price) / entry) * 100 if entry > 0 else 0.0

            lev = trade.get("leverage", 1)

            margin_usd = trade.get("margin_usd", trade["notional_usd"] / lev if lev > 0 else trade["notional_usd"])

            roe_pct = (pnl_usd / margin_usd * 100) if margin_usd > 0 else pnl_pct

            trade["unrealized_pnl_usd"] = round(pnl_usd, 4 if abs(pnl_usd) < 1 else 2)

            trade["unrealized_pnl_pct"] = round(pnl_pct, 2)

            trade["roe_pct"] = round(roe_pct, 2)

            trade["notional_usd"] = round(curr_price * qty, 2)

            # Evaluate health and liquidation checks

            sl = trade.get("stop_loss")

            tp = trade.get("take_profit")

            liq = trade.get("liquidation_price")

            if liq and liq > 0:

                if side == "BUY" and curr_price <= liq:

                    trade["health"] = "LIQUIDATION_BREACHED"

                    continue

                elif side == "SELL" and curr_price >= liq:

                    trade["health"] = "LIQUIDATION_BREACHED"

                    continue

            if sl and ((side == "BUY" and curr_price <= sl) or (side == "SELL" and curr_price >= sl)):

                trade["health"] = "STOP_LOSS_BREACHED"

            elif tp and ((side == "BUY" and curr_price >= tp) or (side == "SELL" and curr_price <= tp)):

                trade["health"] = "TAKE_PROFIT_REACHED"

            elif roe_pct < -15.0 or pnl_pct < -3.0:

                trade["health"] = "AT_RISK"

            elif roe_pct > 5.0 or pnl_pct > 2.0:

                trade["health"] = "IN_PROFIT"

            else:

                trade["health"] = "HEALTHY"

        # Update pending orders distance to market

        for order in self.pending_orders:

            sym = order["symbol"]

            curr_price = price_map.get(sym, order.get("live_price_at_placement", order["limit_price"]))

            order["current_market_price"] = curr_price

            if curr_price > 0:

                order["distance_to_market_pct"] = round(((order["limit_price"] - curr_price) / curr_price) * 100.0, 2)

    # =========================================================================

    # 1. CANONICAL LIMIT ORDER LIFECYCLE (Place -> Partial Fill -> Fill / Cancel)

    # =========================================================================

    def place_limit_order(

        self,

        symbol: str,

        side: str,

        quantity: float,

        limit_price: float,

        stop_loss: Optional[float] = None,

        take_profit: Optional[float] = None,

        market_type: str = "SPOT",

        leverage: int = 1,

        margin_type: str = "ISOLATED",

        strategy: str = "Agentic Limit Order",

        offset_pct: Optional[float] = None,

        live_price: Optional[float] = None,

        environment: str = "BINANCE AGENTIC SUB-ACCOUNT"

    ) -> Dict[str, Any]:

        """

        Registers a new canonical Limit Order with deterministic capital reservation.

        - For BUY: Locks required quote currency (USDT) in reserve. DOES NOT add token to holdings.

        - For SELL: Locks base asset quantity in reserve. Prevents double-spending/overselling.

        """

        side = side.upper()

        market_type = market_type.upper()

        leverage = max(1, min(int(leverage), 20))

        base_asset = symbol.replace("USDT", "").replace("USDC", "")

        notional_usd = quantity * limit_price

        if side in ("BUY", "LONG"):
            if market_type in ("FUTURES", "MARGIN") and leverage > 1:
                margin_required = notional_usd / leverage
            else:
                margin_required = notional_usd

            fee_rate_pct = 0.10 if market_type == "SPOT" else (0.05 if market_type == "FUTURES" else 0.10)
            fee_usd = round(notional_usd * (fee_rate_pct / 100.0), 4)
            total_required_usd = round(margin_required + fee_usd, 4)

            if total_required_usd > self.cash_usd:
                return {
                    "success": False,
                    "error": f"Insufficient sub-wallet cash. Required (Margin + Fee): ${total_required_usd:.4f} (Margin: ${margin_required:.2f}, Est. Fee: ${fee_usd:.4f}), Available Cash: ${self.cash_usd:.2f}"
                }

            # Deduct margin + trading fee from liquid cash
            self.cash_usd = max(0.0, round(self.cash_usd - total_required_usd, 4))
            if "USDT" not in self.holdings:
                self.holdings["USDT"] = {"free": 0.0, "locked": 0.0}
            self.holdings["USDT"]["free"] = max(0.0, round(self.holdings["USDT"]["free"] - total_required_usd, 4))
            self.holdings["USDT"]["locked"] = self.holdings["USDT"].get("locked", 0.0) + margin_required

            reserved_usd = margin_required
            reserved_asset_qty = 0.0

        else:

            # For SELL orders: verify available base asset

            avail_base = self.holdings.get(base_asset, {}).get("free", 0.0)

            if quantity > avail_base:

                return {

                    "success": False,

                    "error": f"Insufficient available {base_asset} holding. Requested to sell: {quantity:.6f}, Available: {avail_base:.6f} {base_asset}."

                }

            # Lock base asset

            self.holdings[base_asset]["free"] = max(0.0, self.holdings[base_asset]["free"] - quantity)

            self.holdings[base_asset]["locked"] = self.holdings[base_asset].get("locked", 0.0) + quantity

            reserved_asset_qty = quantity

            reserved_usd = 0.0

        order_id = f"ORD-LIM-{base_asset}-{uuid.uuid4().hex[:6].upper()}"

        trade_id = f"TRD-LIM-{base_asset}-{uuid.uuid4().hex[:5].upper()}"

        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        # Calculate estimated distance

        ref_price = live_price or limit_price

        dist_pct = offset_pct if offset_pct is not None else (round(((limit_price - ref_price) / ref_price) * 100.0, 2) if ref_price > 0 else 0.0)

        term = f"LIMIT {side}" if market_type == "SPOT" else f"LIMIT {'LONG' if side in ('BUY', 'LONG') else 'SHORT'} {leverage}x"

        fee_rate_pct = 0.10 if market_type == "SPOT" else (0.05 if market_type == "FUTURES" else 0.10)

        fee_usd = round(notional_usd * (fee_rate_pct / 100.0), 4)

        order_record: Dict[str, Any] = {

            "order_id": order_id,

            "trade_id": trade_id,

            "symbol": symbol,

            "side": "BUY" if side in ("BUY", "LONG") else "SELL",

            "term": term,

            "order_type": "LIMIT",

            "market_type": market_type,

            "status": "PENDING",

            "requested_quantity": quantity,

            "filled_quantity": 0.0,

            "remaining_quantity": quantity,

            "fill_percentage": 0.0,

            "limit_price": limit_price,

            "live_price_at_placement": ref_price,

            "current_market_price": ref_price,

            "distance_to_market_pct": dist_pct,

            "average_fill_price": None,

            "fills": [],

            "notional_usd": round(notional_usd, 2),

            "margin_usd": round(margin_required, 2),

            "reserved_usd": round(reserved_usd, 2),

            "reserved_asset_qty": round(reserved_asset_qty, 6),

            "leverage": leverage,

            "margin_type": margin_type.upper(),

            "fee_rate_pct": fee_rate_pct,

            "estimated_fee_usd": fee_usd,

            "stop_loss": stop_loss,

            "take_profit": take_profit,

            "environment": environment,

            "strategy": strategy,

            "created_at": now_ts,

            "updated_at": now_ts,

        }

        self.pending_orders.insert(0, order_record)

        # Log into trade activity history

        self.trade_history.insert(0, {

            "order_id": order_id,

            "trade_id": trade_id,

            "timestamp": now_ts,

            "symbol": symbol,

            "market_type": market_type,

            "side": order_record["side"],

            "term": term,

            "order_type": "LIMIT",

            "price": limit_price,

            "quantity": quantity,

            "notional_usd": round(notional_usd, 2),

            "margin_usd": round(margin_required, 2),

            "leverage": leverage,

            "fee_usd": fee_usd,

            "fee_rate_pct": fee_rate_pct,

            "fee_breakdown": f"${fee_usd:.4f} USDT ({fee_rate_pct:.2f}% Binance Fee)",

            "status": "PENDING",

            "type": "LIMIT",

            "notes": f"Submitted Limit Order {term} @ ${limit_price:,.4f} ({dist_pct:+.1f}% vs market). Reserved {'$' + str(round(reserved_usd, 2)) + ' USDT' if reserved_usd > 0 else str(round(reserved_asset_qty, 4)) + ' ' + base_asset}."

        })

        return {"success": True, "order": order_record}

    def process_fill(

        self,

        order_id: str,

        fill_qty: Optional[float] = None,

        fill_price: Optional[float] = None

    ) -> Dict[str, Any]:

        """

        Executes a discrete fill event (partial or full fill) against a pending limit order.

        Strictly updates holdings ONLY based on the filled amount and computes weighted average fill price.

        """

        order = next((o for o in self.pending_orders if o["order_id"] == order_id or o["trade_id"] == order_id), None)

        if not order:

            return {"success": False, "error": f"Pending order {order_id} not found."}

        rem_qty = order["remaining_quantity"]

        if rem_qty <= 0:

            return {"success": False, "error": f"Order {order_id} has no remaining quantity to fill."}

        actual_fill_qty = min(fill_qty if fill_qty and fill_qty > 0 else rem_qty, rem_qty)

        exec_price = fill_price if fill_price and fill_price > 0 else order["limit_price"]

        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        base_asset = order["symbol"].replace("USDT", "").replace("USDC", "")

        fee_rate = order.get("fee_rate_pct", 0.10)

        fill_notional = actual_fill_qty * exec_price

        fee_usd = round(fill_notional * (fee_rate / 100.0), 4)

        fill_event = {

            "fill_id": f"FILL-{uuid.uuid4().hex[:8].upper()}",

            "timestamp": now_ts,

            "quantity": actual_fill_qty,

            "price": exec_price,

            "notional_usd": round(fill_notional, 2),

            "fee_usd": fee_usd,

            "fee_breakdown": f"${fee_usd:.4f} USDT ({fee_rate:.2f}% Binance Fee)"

        }

        order["fills"].append(fill_event)

        # Update cumulative fill metrics

        new_filled_qty = round(order["filled_quantity"] + actual_fill_qty, 6)

        new_rem_qty = max(0.0, round(order["requested_quantity"] - new_filled_qty, 6))

        order["filled_quantity"] = new_filled_qty

        order["remaining_quantity"] = new_rem_qty

        order["fill_percentage"] = round((new_filled_qty / order["requested_quantity"]) * 100.0, 2)

        # Weighted average fill price

        total_fill_cost = sum(f["quantity"] * f["price"] for f in order["fills"])

        order["average_fill_price"] = round(total_fill_cost / new_filled_qty, 6 if exec_price < 1 else 2)

        order["updated_at"] = now_ts

        # Event-based balance and holding updates

        if order["side"] == "BUY":

            # Unlock the filled portion of reserved USDT

            fill_margin = (actual_fill_qty * order["limit_price"]) / order["leverage"]

            self.holdings["USDT"]["locked"] = max(0.0, self.holdings["USDT"].get("locked", 0.0) - fill_margin)

            order["reserved_usd"] = max(0.0, round(order["reserved_usd"] - fill_margin, 2))

            if order["market_type"] == "SPOT":

                if base_asset not in self.holdings:

                    self.holdings[base_asset] = {"free": 0.0, "locked": 0.0}

                self.holdings[base_asset]["free"] += actual_fill_qty

            else:

                # FUTURES / MARGIN position: register in ongoing_trades

                pos = next((t for t in self.ongoing_trades if t.get("order_id") == order["order_id"]), None)

                if not pos:

                    pos = {

                        "trade_id": order["trade_id"],

                        "order_id": order["order_id"],

                        "symbol": order["symbol"],

                        "side": "BUY",

                        "entry_price": order["average_fill_price"],

                        "quantity": new_filled_qty,

                        "current_price": exec_price,

                        "notional_usd": round(new_filled_qty * exec_price, 2),

                        "margin_usd": round((new_filled_qty * exec_price) / order["leverage"], 2),

                        "leverage": order["leverage"],

                        "margin_type": order["margin_type"],

                        "liquidation_price": round(exec_price * 0.90, 2),

                        "funding_rate": 0.0001 if order["market_type"] == "FUTURES" else None,

                        "unrealized_pnl_usd": 0.0,

                        "unrealized_pnl_pct": 0.0,

                        "roe_pct": 0.0,

                        "stop_loss": order.get("stop_loss"),

                        "take_profit": order.get("take_profit"),

                        "market_type": order["market_type"],

                        "status": "OPEN",

                        "health": "HEALTHY",

                        "opened_at": now_ts,

                        "strategy": order.get("strategy", "Limit Order Fill")

                    }

                    self.ongoing_trades.insert(0, pos)

                else:

                    pos["quantity"] = new_filled_qty

                    pos["entry_price"] = order["average_fill_price"]

                    pos["notional_usd"] = round(new_filled_qty * exec_price, 2)

                    pos["margin_usd"] = round((new_filled_qty * exec_price) / order["leverage"], 2)

        else:

            # SELL order fill

            self.holdings[base_asset]["locked"] = max(0.0, self.holdings[base_asset].get("locked", 0.0) - actual_fill_qty)

            order["reserved_asset_qty"] = max(0.0, round(order["reserved_asset_qty"] - actual_fill_qty, 6))

            net_proceeds = round(fill_notional - fee_usd, 2)

            self.cash_usd += net_proceeds

            if "USDT" not in self.holdings:

                self.holdings["USDT"] = {"free": 0.0, "locked": 0.0}

            self.holdings["USDT"]["free"] += net_proceeds

        # Final order status determination

        is_full_fill = new_rem_qty <= 1e-7

        if is_full_fill:

            order["status"] = "FILLED"

            order["completed_at"] = now_ts

            self.pending_orders.remove(order)

            self.closed_trades.insert(0, order)

            history_status = "FILLED"

        else:

            order["status"] = "PARTIALLY_FILLED"

            history_status = "PARTIAL_FILL"

        # Record fill event in trade history

        self.trade_history.insert(0, {

            "order_id": order["order_id"],

            "trade_id": order["trade_id"],

            "timestamp": now_ts,

            "symbol": order["symbol"],

            "market_type": order["market_type"],

            "side": order["side"],

            "term": order["term"],

            "price": exec_price,

            "quantity": actual_fill_qty,

            "notional_usd": round(fill_notional, 2),

            "margin_usd": round((actual_fill_qty * exec_price) / order["leverage"], 2),

            "leverage": order["leverage"],

            "fee_usd": fee_usd,

            "fee_rate_pct": fee_rate,

            "fee_breakdown": f"${fee_usd:.4f} USDT ({fee_rate:.2f}% Binance Fee)",

            "status": history_status,

            "type": "FILL",

            "notes": f"Filled {actual_fill_qty:.6f} {base_asset} @ ${exec_price:,.4f} ({order['fill_percentage']:.1f}% cumulative). Remaining: {new_rem_qty:.6f} {base_asset}."

        })

        return {"success": True, "order": order, "fill": fill_event, "is_full_fill": is_full_fill}

    def cancel_pending_order(self, order_id_or_symbol: Optional[str] = None, order_id: Optional[str] = None, reason: str = "Manual User Cancellation") -> Dict[str, Any]:

        """

        Cancels an active pending or partially filled limit order and releases remaining reservations.

        Already filled quantities remain safely in holdings!

        """

        raw_target = order_id_or_symbol or order_id or ""

        target = raw_target.strip().upper()

        found = None

        for o in self.pending_orders:

            if o["order_id"].upper() == target or o["trade_id"].upper() == target or o["symbol"].upper() == target or o["symbol"].replace("USDT", "") == target:

                found = o

                break

        if not found:

            return {"success": False, "error": f"No active pending limit order found matching '{order_id_or_symbol}'."}

        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        base_asset = found["symbol"].replace("USDT", "").replace("USDC", "")

        released_usd = 0.0

        released_asset_qty = 0.0

        if found["side"] == "BUY":

            released_usd = found["reserved_usd"]

            self.holdings["USDT"]["locked"] = max(0.0, round(self.holdings["USDT"].get("locked", 0.0) - released_usd, 2))

            self.holdings["USDT"]["free"] += released_usd

            self.cash_usd += released_usd

            found["reserved_usd"] = 0.0

        else:

            released_asset_qty = found["reserved_asset_qty"]

            self.holdings[base_asset]["locked"] = max(0.0, round(self.holdings[base_asset].get("locked", 0.0) - released_asset_qty, 6))

            self.holdings[base_asset]["free"] += released_asset_qty

            found["reserved_asset_qty"] = 0.0

        if found["filled_quantity"] > 0:

            found["status"] = "CANCELED_REMAINDER"

        else:

            found["status"] = "CANCELED"

        found["closed_at"] = now_ts

        found["cancel_reason"] = reason

        self.pending_orders.remove(found)

        self.closed_trades.insert(0, found)

        # Log cancellation

        self.trade_history.insert(0, {

            "order_id": found["order_id"],

            "trade_id": found["trade_id"],

            "timestamp": now_ts,

            "symbol": found["symbol"],

            "market_type": found["market_type"],

            "side": "CANCEL",

            "term": f"CANCEL {found['term']}",

            "price": found["limit_price"],

            "quantity": found["remaining_quantity"],

            "notional_usd": round(found["remaining_quantity"] * found["limit_price"], 2),

            "margin_usd": released_usd,

            "leverage": found["leverage"],

            "fee_usd": 0.0,

            "fee_rate_pct": 0.0,

            "fee_breakdown": "$0.00 USDT",

            "status": "CANCELED",

            "type": "CANCEL_LIMIT",

            "notes": f"Cancelled order {found['order_id']} on {found['symbol']}. Released {'$' + str(round(released_usd, 2)) + ' USDT' if released_usd > 0 else str(round(released_asset_qty, 4)) + ' ' + base_asset}. Retained {found['filled_quantity']:.4f} filled tokens."

        })

        return {

            "success": True,

            "canceled_order": found,

            "released_usd": released_usd,

            "released_asset_qty": released_asset_qty,

            "retained_filled_qty": found["filled_quantity"],

            "new_cash_usd": round(self.cash_usd, 2)

        }

    # =========================================================================

    # 2. MARKET TRADES & SPOT LIQUIDATION

    # =========================================================================

    def open_trade(

        self,

        symbol: str,

        side: str,

        quantity: float,

        price: float,

        stop_loss: Optional[float] = None,

        take_profit: Optional[float] = None,

        market_type: str = "SPOT",

        leverage: int = 1,

        margin_type: str = "ISOLATED",

        strategy: str = "Agentic Rule-Based",

        order_type: str = "MARKET",

        offset_pct: Optional[float] = None,

        live_price: Optional[float] = None

    ) -> Dict[str, Any]:

        """

        Opens a market trade immediately or forwards to place_limit_order if order_type == 'LIMIT'.

        """

        if order_type.upper() == "LIMIT":

            return self.place_limit_order(

                symbol=symbol,

                side=side,

                quantity=quantity,

                limit_price=price,

                stop_loss=stop_loss,

                take_profit=take_profit,

                market_type=market_type,

                leverage=leverage,

                margin_type=margin_type,

                strategy=strategy,

                offset_pct=offset_pct,

                live_price=live_price

            )

        side = side.upper()

        market_type = market_type.upper()

        leverage = max(1, min(int(leverage), 20))

        notional_cost = quantity * price

        if market_type in ("FUTURES", "MARGIN") and leverage > 1:

            margin_required = notional_cost / leverage

        else:

            margin_required = notional_cost

        if margin_required > self.cash_usd:

            return {

                "success": False,

                "error": f"Insufficient sub-wallet cash. Required Margin: ${margin_required:.2f}, Available Cash: ${self.cash_usd:.2f}"

            }

        # Deduct margin from liquid cash

        self.cash_usd -= margin_required

        if "USDT" not in self.holdings:

            self.holdings["USDT"] = {"free": 0.0, "locked": 0.0}

        self.holdings["USDT"]["free"] = max(0.0, self.holdings["USDT"]["free"] - margin_required)

        base_asset = symbol.replace("USDT", "").replace("USDC", "")

        # For Market Orders: Immediately execute and credit spot asset

        if market_type == "SPOT" and side in ("BUY", "LONG"):

            if base_asset not in self.holdings:

                self.holdings[base_asset] = {"free": 0.0, "locked": 0.0}

            self.holdings[base_asset]["free"] += quantity

        # Calculate estimated liquidation price for Futures / Margin

        mmr = 0.005

        if market_type in ("FUTURES", "MARGIN") and leverage > 1:

            if side in ("BUY", "LONG"):

                liq_price = round(price * (1.0 - (1.0 / leverage) + mmr), 4 if price < 10 else 2)

            else:

                liq_price = round(price * (1.0 + (1.0 / leverage) - mmr), 4 if price < 10 else 2)

        else:

            liq_price = 0.0 if side in ("BUY", "LONG") else round(price * 2.0, 2)

        fee_rate_pct = 0.10 if market_type == "SPOT" else (0.05 if market_type == "FUTURES" else 0.10)

        fee_usd = round(notional_cost * (fee_rate_pct / 100.0), 4)

        fee_breakdown = f"${fee_usd:.4f} USDT ({fee_rate_pct:.2f}% Binance {market_type.capitalize()} Fee)"

        order_id = f"ORD-{market_type[:3]}-{base_asset}-{uuid.uuid4().hex[:6].upper()}"

        trade_id = f"TRD-{market_type[:3]}-{base_asset}-{uuid.uuid4().hex[:5].upper()}"

        term = f"LONG {leverage}x" if (market_type == "FUTURES" and side in ("BUY", "LONG")) else (f"SHORT {leverage}x" if (market_type == "FUTURES" and side in ("SELL", "SHORT")) else f"SPOT {side}")

        new_trade = {

            "order_id": order_id,

            "trade_id": trade_id,

            "symbol": symbol,

            "side": "BUY" if side in ("BUY", "LONG") else "SELL",

            "term": term,

            "order_type": "MARKET",

            "entry_price": price,

            "current_price": price,

            "quantity": quantity,

            "notional_usd": round(notional_cost, 2),

            "margin_usd": round(margin_required, 2),

            "leverage": leverage,

            "margin_type": margin_type.upper(),

            "liquidation_price": liq_price,

            "funding_rate": 0.0001 if market_type == "FUTURES" else None,

            "fee_usd": fee_usd,

            "fee_rate_pct": fee_rate_pct,

            "fee_breakdown": fee_breakdown,

            "unrealized_pnl_usd": 0.0,

            "unrealized_pnl_pct": 0.0,

            "roe_pct": 0.0,

            "stop_loss": stop_loss,

            "take_profit": take_profit,

            "market_type": market_type,

            "status": "OPEN",

            "health": "HEALTHY",

            "opened_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),

            "strategy": strategy

        }

        self.ongoing_trades.insert(0, new_trade)

        self.trade_history.insert(0, {

            "order_id": order_id,

            "trade_id": trade_id,

            "timestamp": new_trade["opened_at"],

            "symbol": symbol,

            "market_type": market_type,

            "side": new_trade["side"],

            "term": term,

            "order_type": "MARKET",

            "price": price,

            "quantity": quantity,

            "notional_usd": round(notional_cost, 2),

            "margin_usd": round(margin_required, 2),

            "leverage": leverage,

            "fee_usd": fee_usd,

            "fee_rate_pct": fee_rate_pct,

            "fee_breakdown": fee_breakdown,

            "status": "FILLED",

            "type": "OPEN",

            "notes": f"Market order filled {term} on {symbol} @ ${price:,.4f}"

        })

        return {"success": True, "trade": new_trade}

    def close_trade(self, trade_id: str, exit_price: Optional[float] = None, reason: str = "Manual Exit") -> Dict[str, Any]:

        """

        Closes an ongoing derivative position or cancels a pending limit order.

        """

        # First check if this is in pending_orders

        pending = next((o for o in self.pending_orders if o["order_id"] == trade_id or o["trade_id"] == trade_id), None)

        if pending:

            return self.cancel_pending_order(trade_id, reason=reason)

        found = next((t for t in self.ongoing_trades if t["trade_id"] == trade_id), None)

        if not found:

            return {"success": False, "error": f"Trade {trade_id} not found."}

        price = exit_price or found["current_price"]

        entry = found["entry_price"]

        qty = found["quantity"]

        side = found["side"]

        base_asset = found["symbol"].replace("USDT", "").replace("USDC", "")

        mkt = found.get("market_type", "SPOT")

        if side == "BUY":

            realized_pnl = (price - entry) * qty

        else:

            realized_pnl = (entry - price) * qty

        margin_used = found.get("margin_usd", qty * entry)

        returned_cash = max(0.0, margin_used + realized_pnl)

        self.cash_usd += returned_cash

        self.holdings["USDT"]["free"] += returned_cash

        if found.get("market_type") == "SPOT" and base_asset in self.holdings:

            self.holdings[base_asset]["free"] = max(0.0, self.holdings[base_asset]["free"] - qty)

        fee_rate_pct = 0.10 if mkt == "SPOT" else (0.05 if mkt == "FUTURES" else 0.10)

        close_notional = qty * price

        close_fee_usd = round(close_notional * (fee_rate_pct / 100.0), 4)

        close_fee_breakdown = f"${close_fee_usd:.4f} USDT ({fee_rate_pct:.2f}% Binance Fee)"

        close_order_id = f"ORD-CLS-{base_asset}-{uuid.uuid4().hex[:6].upper()}"

        found["status"] = "CLOSED"

        found["closed_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        found["exit_price"] = price

        found["realized_pnl_usd"] = round(realized_pnl, 2)

        found["close_reason"] = reason

        found["close_order_id"] = close_order_id

        found["close_fee_usd"] = close_fee_usd

        found["close_fee_breakdown"] = close_fee_breakdown

        self.ongoing_trades.remove(found)

        self.closed_trades.insert(0, found)

        self.trade_history.insert(0, {

            "order_id": close_order_id,

            "trade_id": trade_id,

            "timestamp": found["closed_at"],

            "symbol": found["symbol"],

            "market_type": mkt,

            "side": "SELL" if found["side"] == "BUY" else "BUY",

            "term": "CLOSE " + found.get("term", found["side"]),

            "price": price,

            "quantity": qty,

            "notional_usd": round(close_notional, 2),

            "margin_usd": found.get("margin_usd", 0.0),

            "leverage": found.get("leverage", 1),

            "fee_usd": close_fee_usd,

            "fee_rate_pct": fee_rate_pct,

            "fee_breakdown": close_fee_breakdown,

            "realized_pnl_usd": round(realized_pnl, 2),

            "status": "CLOSED",

            "type": "CLOSE",

            "notes": f"Closed position @ ${price:,.2f}. Realized PnL: ${realized_pnl:+.2f} USDT"

        })

        return {

            "success": True,

            "closed_trade": found,

            "realized_pnl_usd": round(realized_pnl, 2),

            "return_capital": round(returned_cash, 2),

            "new_cash_usd": round(self.cash_usd, 2)

        }

    def sell_asset_holding(self, asset: str, quantity: Optional[float] = None, price: Optional[float] = None) -> Dict[str, Any]:

        """

        Sells available spot holdings into liquid USDT cash.

        """

        base_asset = asset.upper().replace("USDT", "").replace("USDC", "")

        if base_asset not in self.holdings or self.holdings[base_asset]["free"] <= 0.0:

            return {"success": False, "error": f"No available free {base_asset} holdings to sell."}

        available_qty = self.holdings[base_asset]["free"]

        sell_qty = min(available_qty, quantity) if (quantity and quantity > 0) else available_qty

        if sell_qty <= 0:

            return {"success": False, "error": f"Invalid sell quantity: {sell_qty}."}

        if not price or price <= 0:

            default_prices = {"BTC": 78920.0, "ETH": 2483.0, "SOL": 104.5, "PUMP": 0.0028, "BNB": 585.0}

            price = default_prices.get(base_asset, 1.0)

        notional_usd = round(sell_qty * price, 2)

        fee_rate_pct = 0.10

        fee_usd = round(notional_usd * (fee_rate_pct / 100.0), 4)

        net_proceeds = round(notional_usd - fee_usd, 2)

        self.holdings[base_asset]["free"] = max(0.0, self.holdings[base_asset]["free"] - sell_qty)

        self.cash_usd += net_proceeds

        if "USDT" not in self.holdings:

            self.holdings["USDT"] = {"free": 0.0, "locked": 0.0}

        self.holdings["USDT"]["free"] += net_proceeds

        order_id = f"ORD-SPT-{base_asset}-SELL-{uuid.uuid4().hex[:6].upper()}"

        fee_breakdown = f"${fee_usd:.4f} USDT (0.10% Binance Spot Fee)"

        trade_item = {

            "order_id": order_id,

            "trade_id": f"TRD-SPT-{base_asset}-{uuid.uuid4().hex[:5].upper()}",

            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),

            "symbol": f"{base_asset}USDT",

            "market_type": "SPOT",

            "side": "SELL",

            "term": "SPOT SELL",

            "price": price,

            "quantity": sell_qty,

            "notional_usd": notional_usd,

            "margin_usd": notional_usd,

            "leverage": 1,

            "fee_usd": fee_usd,

            "fee_rate_pct": fee_rate_pct,

            "fee_breakdown": fee_breakdown,

            "status": "FILLED",

            "type": "SELL",

            "notes": f"Sold {sell_qty} {base_asset} @ ${price:,.2f} on Binance Spot. Credited ${net_proceeds:.2f} to liquid cash."

        }

        self.trade_history.insert(0, trade_item)

        return {

            "success": True,

            "order_id": order_id,

            "asset": base_asset,

            "quantity_sold": sell_qty,

            "price": price,

            "notional_usd": notional_usd,

            "fee_usd": fee_usd,

            "fee_breakdown": fee_breakdown,

            "net_proceeds_usd": net_proceeds,

            "new_cash_usd": round(self.cash_usd, 2),

            "trade": trade_item,

        }

    def record_convert_history(self, from_asset: str, to_asset: str, from_amount: float, to_amount: float, quote_id: str):

        """Logs a zero-fee Binance Convert swap into trade history and synchronizes sub-wallet holdings."""

        from_asset = from_asset.upper().strip()

        to_asset = to_asset.upper().strip()

        order_id = f"ORD-CNV-{from_asset}{to_asset}-{uuid.uuid4().hex[:6].upper()}"

        # Update from_asset in sub_wallet

        if from_asset == "USDT":

            self.cash_usd = max(0.0, round(self.cash_usd - from_amount, 2))

            if "USDT" in self.holdings:

                self.holdings["USDT"]["free"] = self.cash_usd

        else:

            if from_asset in self.holdings:

                self.holdings[from_asset]["free"] = max(0.0, round(self.holdings[from_asset]["free"] - from_amount, 8))

            else:

                self.holdings[from_asset] = {"free": 0.0, "locked": 0.0}

        # Update to_asset in sub_wallet

        if to_asset == "USDT":

            self.cash_usd = round(self.cash_usd + to_amount, 2)

            if "USDT" in self.holdings:

                self.holdings["USDT"]["free"] = self.cash_usd

        else:

            if to_asset not in self.holdings:

                self.holdings[to_asset] = {"free": 0.0, "locked": 0.0}

            self.holdings[to_asset]["free"] = round(self.holdings[to_asset]["free"] + to_amount, 8)

        self.trade_history.insert(0, {

            "order_id": order_id,

            "trade_id": quote_id,

            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),

            "symbol": f"{from_asset}/{to_asset}",

            "market_type": "CONVERT",

            "side": "SWAP",

            "term": f"CONVERT {from_asset}->{to_asset}",

            "price": round(from_amount / to_amount, 6) if to_amount > 0 else 1.0,

            "quantity": to_amount,

            "notional_usd": round(from_amount, 4),

            "margin_usd": round(from_amount, 4),

            "leverage": 1,

            "fee_usd": 0.0,

            "fee_rate_pct": 0.0,

            "fee_breakdown": "0.00 USDT (0.00% Zero-Fee Binance Convert)",

            "status": "FILLED",

            "type": "CONVERT",

            "notes": f"Zero-fee instant swap {from_amount} {from_asset} -> {to_amount} {to_asset}"

        })

    def update_trade_levels(self, trade_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict[str, Any]:

        """Updates protective stop loss or profit target on an ongoing trade or pending order."""

        found = next((t for t in self.ongoing_trades if t["trade_id"] == trade_id or t.get("order_id") == trade_id), None)

        if not found:

            found = next((o for o in self.pending_orders if o["trade_id"] == trade_id or o["order_id"] == trade_id), None)

        if not found:

            return {"success": False, "error": f"Trade/Order {trade_id} not found."}

        if stop_loss is not None:

            found["stop_loss"] = stop_loss

        if take_profit is not None:

            found["take_profit"] = take_profit

        return {"success": True, "trade": found}

    # =========================================================================

    # 3. PORTFOLIO & HOLDINGS DRIFT ANALYSIS

    # =========================================================================

    def get_holdings_analysis(self, price_map: Dict[str, float]) -> Dict[str, Any]:

        """

        Analyzes actual holdings (free + locked), active reservations, and pending orders without double counting.

        """

        total_val = 0.0

        details = []

        for asset, bal in self.holdings.items():

            free_qty = bal.get("free", 0.0)

            locked_qty = bal.get("locked", 0.0)

            total_qty = free_qty + locked_qty

            if total_qty <= 0.0:

                continue

            if asset in ("USDT", "USDC", "USD", "FDUSD"):

                p = 1.0

            else:

                p = price_map.get(f"{asset}USDT", 100.0)

            val = total_qty * p

            total_val += val

            details.append({

                "asset": asset,

                "free_quantity": round(free_qty, 6 if free_qty < 1 else 4),

                "locked_quantity": round(locked_qty, 6 if locked_qty < 1 else 4),

                "total_quantity": round(total_qty, 6 if total_qty < 1 else 4),

                "quantity": round(total_qty, 6 if total_qty < 1 else 4),

                "price_usd": p,

                "value_usd": round(val, 2),

                "free_value_usd": round(free_qty * p, 2),

                "locked_value_usd": round(locked_qty * p, 2),

            })

        # Calculate actual vs target allocations and drift

        analyzed_holdings = []

        for item in details:

            actual_pct = (item["value_usd"] / total_val * 100) if total_val > 0 else 0.0

            target_pct = self.target_allocations.get(item["asset"], 0.0) * 100

            drift_pct = round(actual_pct - target_pct, 2)

            if abs(drift_pct) <= 2.5:

                drift_status = "BALANCED"

                verdict = "Allocation compliant with mandate corridor."

            elif drift_pct > 2.5:

                drift_status = "OVERWEIGHT"

                verdict = f"Over target by {drift_pct}%. Consider trimming into USDT reserves."

            else:

                drift_status = "UNDERWEIGHT"

                verdict = f"Under target by {abs(drift_pct)}%. Potential rebalance accumulation zone."

            analyzed_holdings.append({

                **item,

                "actual_allocation_pct": round(actual_pct, 2),

                "target_allocation_pct": round(target_pct, 2),

                "drift_pct": drift_pct,

                "drift_status": drift_status,

                "verdict": verdict

            })

        analyzed_holdings.sort(key=lambda x: x["value_usd"], reverse=True)

        locked_cash = self.holdings.get("USDT", {}).get("locked", 0.0)

        return {

            "sub_wallet_id": self.sub_wallet_id,

            "allocated_budget_usd": self.allocated_budget_usd,

            "total_portfolio_value_usd": round(total_val, 2),

            "available_cash_usd": round(self.cash_usd, 2),

            "reserved_cash_usd": round(locked_cash, 2),

            "cash_ratio_pct": round((self.cash_usd / total_val * 100) if total_val > 0 else 0, 2),

            "holdings": analyzed_holdings,

            "pending_orders": self.pending_orders,

            "pending_orders_count": len(self.pending_orders),

            "ongoing_trades_count": len(self.ongoing_trades),

            "total_unrealized_pnl_usd": round(sum(t.get("unrealized_pnl_usd", 0) for t in self.ongoing_trades), 2),

            "mandate_compliance": "PASS" if any(h["drift_status"] == "BALANCED" for h in analyzed_holdings) else "MONITOR",

            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        }

    def rebalance_to_corridor(self, price_map: Optional[Dict[str, float]] = None) -> Dict[str, Any]:

        """Alias for rebalance_holdings."""

        return self.rebalance_holdings(price_map)

    def rebalance_holdings(self, price_map: Optional[Dict[str, float]] = None) -> Dict[str, Any]:

        """

        Executes an instant portfolio rebalance across sub-wallet assets to restore

        allocations exactly to target weights (USDT: 40%, BTC: 30%, ETH: 15%, SOL: 10%, USDC: 5%).

        """

        if not price_map:

            price_map = {

                "BTCUSDT": 78900.0,

                "ETHUSDT": 2483.0,

                "SOLUSDT": 104.5,

            }

        total_val = 0.0

        for asset, data in self.holdings.items():

            qty = data.get("free", 0.0) + data.get("locked", 0.0)

            if asset in ("USDT", "USDC", "USD", "FDUSD"):

                p = 1.0

            else:

                p = price_map.get(f"{asset}USDT", 100.0)

            total_val += qty * p

        rebalanced_orders = []

        for asset, target_weight in self.target_allocations.items():

            target_usd = total_val * target_weight

            if asset in ("USDT", "USDC", "USD", "FDUSD"):

                new_qty = target_usd

            else:

                p = price_map.get(f"{asset}USDT", 100.0)

                new_qty = target_usd / p if p > 0 else 0.0

            old_qty = self.holdings.get(asset, {}).get("free", 0.0)

            delta_qty = new_qty - old_qty

            self.holdings[asset] = {

                "free": round(new_qty, 6 if new_qty < 1 else 4),

                "locked": 0.0

            }

            if abs(delta_qty) > 1e-4:

                rebalanced_orders.append({

                    "asset": asset,

                    "target_weight_pct": target_weight * 100,

                    "target_value_usd": round(target_usd, 2),

                    "new_quantity": self.holdings[asset]["free"]

                })

        self.cash_usd = self.holdings.get("USDT", {}).get("free", 0.0)

        return {

            "success": True,

            "message": "Sub-wallet portfolio successfully rebalanced to target allocations.",

            "rebalanced_orders": rebalanced_orders,

            "analysis": self.get_holdings_analysis(price_map)

        }

    def get_today_pnl_breakdown(self, price_map: Optional[Dict[str, float]] = None) -> Dict[str, Any]:

        """

        Calculates Today's Realized and Unrealized PnL for the Sub-Wallet (UTC 00:00:00 to present).

        """

        if price_map:

            self.update_live_prices(price_map)

        unrealized_usd = sum(float(t.get("unrealized_pnl_usd", 0.0)) for t in self.ongoing_trades)

        # Realized PnL from closed trades

        realized_usd = sum(float(t.get("realized_pnl_usd", 0.0)) for t in self.closed_trades)

        fees_usd = sum(float(t.get("fee_usd", 0.0)) for t in self.trade_history)

        net_pnl_usd = realized_usd + unrealized_usd - fees_usd

        total_val = self.get_holdings_analysis(price_map).get("total_portfolio_value_usd", 500.0)

        pnl_pct = round((net_pnl_usd / total_val * 100) if total_val > 0 else 0.0, 2)

        return {

            "total_pnl_usd": round(net_pnl_usd, 2),

            "pnl_pct": pnl_pct,

            "realized_pnl_usd": round(realized_usd, 2),

            "unrealized_pnl_usd": round(unrealized_usd, 2),

            "fees_usd": round(fees_usd, 4),

            "funding_usd": 0.0,

            "status": "PROFIT" if net_pnl_usd > 0 else ("LOSS" if net_pnl_usd < 0 else "NEUTRAL"),

            "timezone": "UTC (Binance Day Cycle)",

            "reset_time_utc": "00:00:00 UTC",

            "is_live_mcp": False,

            "sub_account_id": self.sub_wallet_id

        }

    # =========================================================================

    # MULTI-WALLET & INTERNAL TRANSFER ENGINE

    # =========================================================================

    def get_wallets_summary(self, price_map: Optional[Dict[str, float]] = None) -> Dict[str, Any]:

        """

        Returns comprehensive valuation and asset breakdown for all Binance internal wallets:

        Spot, Funding, USD-M Futures, Coin-M Futures, Cross Margin, and Earn.

        """

        default_prices = {

            "USDT": 1.0, "USDC": 1.0, "FDUSD": 1.0, "USD": 1.0,

            "BTC": 79000.0, "ETH": 2500.0, "SOL": 105.0, "BNB": 580.0

        }

        prices = default_prices.copy()

        if price_map:

            for k, v in price_map.items():

                clean_k = k.replace("USDT", "").replace("USDC", "")

                prices[clean_k] = float(v)

                prices[k] = float(v)

        # Sync Spot wallet with main sub-wallet holdings

        self.wallets["SPOT"]["balances"] = {

            k: {"free": float(v["free"]), "locked": float(v["locked"])}

            for k, v in self.holdings.items()

        }

        total_ecosystem_usd = 0.0

        wallets_summary = []

        for w_key, w_data in self.wallets.items():

            wallet_usd = 0.0

            items = []

            for asset, bal in w_data["balances"].items():

                p = prices.get(asset, default_prices.get(asset, 1.0))

                free_qty = float(bal["free"])

                locked_qty = float(bal["locked"])

                tot_qty = free_qty + locked_qty

                val_usd = round(tot_qty * p, 2)

                wallet_usd += val_usd

                items.append({

                    "asset": asset,

                    "free": free_qty,

                    "locked": locked_qty,

                    "total": tot_qty,

                    "price_usd": p,

                    "value_usd": val_usd

                })

            total_ecosystem_usd += wallet_usd

            wallets_summary.append({

                "wallet_id": w_key,

                "name": w_data["name"],

                "badge": w_data["badge"],

                "description": w_data["description"],

                "icon": w_data["icon"],

                "total_value_usd": round(wallet_usd, 2),

                "assets": sorted(items, key=lambda x: x["value_usd"], reverse=True),

                "asset_count": len(items)

            })

        for w in wallets_summary:

            w["allocation_pct"] = round((w["total_value_usd"] / total_ecosystem_usd * 100) if total_ecosystem_usd > 0 else 0.0, 1)

        return {

            "total_ecosystem_value_usd": round(total_ecosystem_usd, 2),

            "wallet_count": len(wallets_summary),

            "wallets": wallets_summary,

            "recent_transfers": self.internal_transfers[:10],

            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        }

    def execute_internal_transfer(self, from_wallet: str, to_wallet: str, asset: str, amount: float) -> Dict[str, Any]:

        """

        Executes a zero-fee deterministic internal transfer between Binance account wallets.

        Supported: SPOT, FUNDING, USDT_FUTURES, COIN_FUTURES, CROSS_MARGIN, EARN.

        """

        from_w = from_wallet.upper().replace(" ", "_")

        to_w = to_wallet.upper().replace(" ", "_")

        asset = asset.upper()

        amount = float(amount)

        if from_w not in self.wallets:

            return {"success": False, "error": f"Source wallet '{from_wallet}' does not exist."}

        if to_w not in self.wallets:

            return {"success": False, "error": f"Destination wallet '{to_wallet}' does not exist."}

        if from_w == to_w:

            return {"success": False, "error": "Source and destination wallets cannot be identical."}

        if amount <= 0:

            return {"success": False, "error": "Transfer amount must be greater than zero."}

        # Check source wallet balance

        src_balances = self.wallets[from_w]["balances"]

        if asset not in src_balances or src_balances[asset]["free"] < amount:

            avail = src_balances.get(asset, {}).get("free", 0.0)

            return {

                "success": False,

                "error": f"Insufficient available balance in {self.wallets[from_w]['name']}. Available: {avail} {asset}, Requested: {amount} {asset}."

            }

        # Deduct from source wallet

        src_balances[asset]["free"] = round(src_balances[asset]["free"] - amount, 8)

        # Credit to destination wallet

        dest_balances = self.wallets[to_w]["balances"]

        if asset not in dest_balances:

            dest_balances[asset] = {"free": 0.0, "locked": 0.0}

        dest_balances[asset]["free"] = round(dest_balances[asset]["free"] + amount, 8)

        # Sync Spot wallet with main holdings if involved

        if from_w == "SPOT":

            if asset in self.holdings:

                self.holdings[asset]["free"] = src_balances[asset]["free"]

            if asset == "USDT":

                self.cash_usd = src_balances[asset]["free"]

        if to_w == "SPOT":

            if asset in self.holdings:

                self.holdings[asset]["free"] = dest_balances[asset]["free"]

            else:

                self.holdings[asset] = {"free": dest_balances[asset]["free"], "locked": 0.0}

            if asset == "USDT":

                self.cash_usd = dest_balances[asset]["free"]

        transfer_id = f"XFER-{int(time.time()*1000)%100000000:08d}"

        tx_hash = f"INT-{uuid.uuid4().hex[:12].upper()}"

        record = {

            "transfer_id": transfer_id,

            "from_wallet": from_w,

            "from_wallet_name": self.wallets[from_w]["name"],

            "to_wallet": to_w,

            "to_wallet_name": self.wallets[to_w]["name"],

            "asset": asset,

            "amount": amount,

            "fee": 0.0,

            "status": "CONFIRMED",

            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),

            "tx_hash": tx_hash

        }

        self.internal_transfers.insert(0, record)

        return {

            "success": True,

            "message": f"Successfully transferred {amount} {asset} from {self.wallets[from_w]['name']} to {self.wallets[to_w]['name']}.",

            "transfer": record,

            "from_wallet_balance": src_balances[asset]["free"],

            "to_wallet_balance": dest_balances[asset]["free"]

        }


    def reset_wallet(self, initial_cash: float = 250.0) -> Dict[str, Any]:
        """Resets cash and demo holdings back to initial healthy state."""
        self.cash_usd = initial_cash
        self.holdings = {
            "USDT": {"free": initial_cash, "locked": 0.0},
            "BTC": {"free": 0.0016, "locked": 0.0},
            "ETH": {"free": 0.028, "locked": 0.0},
            "SOL": {"free": 0.20, "locked": 0.0},
            "USDC": {"free": 12.50, "locked": 0.0},
        }
        self.pending_orders = []
        self.ongoing_trades = []
        if "SPOT" in self.wallets:
            self.wallets["SPOT"]["balances"]["USDT"] = {"free": initial_cash, "locked": 0.0}
        return {
            "success": True,
            "message": f"Sub-wallet successfully reset. Available Cash: ${self.cash_usd:.2f} USDT.",
            "cash_usd": self.cash_usd
        }

    def deposit_cash(self, amount_usd: float = 250.0) -> Dict[str, Any]:
        """Deposits or tops up cash in the sub-wallet."""
        self.cash_usd += amount_usd
        if "USDT" not in self.holdings:
            self.holdings["USDT"] = {"free": 0.0, "locked": 0.0}
        self.holdings["USDT"]["free"] += amount_usd
        if "SPOT" in self.wallets:
            if "USDT" not in self.wallets["SPOT"]["balances"]:
                self.wallets["SPOT"]["balances"]["USDT"] = {"free": 0.0, "locked": 0.0}
            self.wallets["SPOT"]["balances"]["USDT"]["free"] += amount_usd
        return {
            "success": True,
            "message": f"Successfully deposited ${amount_usd:.2f} USDT. New Available Cash: ${self.cash_usd:.2f} USDT.",
            "cash_usd": self.cash_usd
        }
