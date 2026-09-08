"""
SYRAX — AI Portfolio Manager & Rebalancer
Parses natural language mandates, tracks allocation drift, identifies idle cash & dust,
and computes optimal minimal-friction rebalancing trade sequences respecting order size limits.
"""

import re
from typing import Dict, List, Any, Optional
from backend.binance.agent_os import BinanceAgentOS

class PortfolioAgent:
    """
    Manages asset allocation, balances, and rebalancing execution through Binance Agent OS.
    Example mandate: "Keep 50% USDT, 30% BTC and 20% ETH, and never use more than $25 per order."
    """

    def __init__(self, binance_client: BinanceAgentOS):
        self.binance = binance_client
        self.target_allocations: Dict[str, float] = {
            "USDT": 50.0,
            "BTC": 30.0,
            "ETH": 20.0
        }
        self.max_order_size_usd: Optional[float] = 25.0

    def parse_mandate(self, text: str) -> Dict[str, Any]:
        """
        Extracts asset allocation targets and order size constraints from natural language.
        Example: "Keep 50% USDT, 30% BTC and 20% ETH, never use more than $25 per order"
        """
        targets = {}
        # Match patterns like "50% USDT", "30% BTC", "20 percent ETH"
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s+([A-Za-z]+)', text, re.IGNORECASE)
        for pct_str, asset in matches:
            targets[asset.upper()] = float(pct_str)

        # Match max order size: "never use more than $25", "max order $50"
        max_order = None
        order_match = re.search(r'(?:more than|max order(?: size)? of?|never use more than)\s*\$?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if order_match:
            max_order = float(order_match.group(1))

        # Check if total sums up close to 100%
        total_pct = sum(targets.values())
        valid = (98.0 <= total_pct <= 102.0) if targets else False

        if valid:
            self.target_allocations = targets
        if max_order:
            self.max_order_size_usd = max_order

        return {
            "targets": targets or self.target_allocations,
            "total_percentage": total_pct if targets else 100.0,
            "max_order_size_usd": max_order or self.max_order_size_usd,
            "is_valid_mandate": valid or bool(targets)
        }

    async def calculate_rebalancing_plan(self, custom_targets: Optional[Dict[str, float]] = None, custom_max_order: Optional[float] = None) -> Dict[str, Any]:
        """
        Compares current portfolio state against target allocations,
        measures drift, and generates a structured, minimal-fee trade execution plan.
        """
        portfolio = await self.binance.get_account_portfolio()
        total_val = portfolio["total_value_usd"]
        holdings = {h["asset"]: h for h in portfolio["holdings"]}
        
        targets = custom_targets or self.target_allocations
        max_order = custom_max_order or self.max_order_size_usd

        # Calculate current allocation vs target drift
        drift_analysis = []
        proposed_actions = []
        
        all_assets = set(list(holdings.keys()) + list(targets.keys()))
        
        for asset in all_assets:
            cur_holding = holdings.get(asset, {"value_usd": 0.0, "allocation_pct": 0.0, "price_usd": 1.0, "total": 0.0})
            cur_pct = cur_holding["allocation_pct"]
            cur_val = cur_holding["value_usd"]
            
            target_pct = targets.get(asset, 0.0)
            target_val = total_val * (target_pct / 100.0)
            
            drift_val = target_val - cur_val
            drift_pct = round(target_pct - cur_pct, 2)
            
            drift_analysis.append({
                "asset": asset,
                "current_val_usd": round(cur_val, 2),
                "current_pct": round(cur_pct, 2),
                "target_pct": round(target_pct, 2),
                "target_val_usd": round(target_val, 2),
                "drift_pct": drift_pct,
                "drift_val_usd": round(drift_val, 2),
                "status": "BALANCED" if abs(drift_pct) <= 2.0 else ("UNDERWEIGHT" if drift_pct > 0 else "OVERWEIGHT")
            })

            # If drift is significant (> $5 or > 2%), plan rebalancing
            if abs(drift_val) >= 5.0 and abs(drift_pct) >= 1.5:
                side = "BUY" if drift_val > 0 else "SELL"
                needed_usd = abs(drift_val)
                
                # Check order slicing if max order size policy is active
                if max_order and needed_usd > max_order:
                    # Slicing into multiple safe orders
                    num_orders = int(needed_usd // max_order)
                    rem = needed_usd % max_order
                    chunks = [max_order] * num_orders
                    if rem >= 5.0:
                        chunks.append(round(rem, 2))
                    
                    for idx, chunk in enumerate(chunks):
                        proposed_actions.append({
                            "action_id": f"REBAL-{asset}-{idx+1}",
                            "asset": asset,
                            "symbol": f"{asset}USDT" if asset != "USDT" else "USDT",
                            "side": side,
                            "notional_usd": chunk,
                            "preferred_route": "BINANCE_CONVERT" if asset in ["USDC", "USDT"] else "BINANCE_SPOT",
                            "fee_estimate": "0.00 (Convert)" if asset in ["USDC", "USDT"] else f"${round(chunk * 0.001, 3)} (0.1%)",
                            "reasoning": f"Sliced trade {idx+1}/{len(chunks)} of ${chunk:.2f} respecting max order policy of ${max_order:.2f} to correct {drift_pct:+.1f}% drift."
                        })
                else:
                    proposed_actions.append({
                        "action_id": f"REBAL-{asset}-1",
                        "asset": asset,
                        "symbol": f"{asset}USDT" if asset != "USDT" else "USDT",
                        "side": side,
                        "notional_usd": round(needed_usd, 2),
                        "preferred_route": "BINANCE_CONVERT" if asset in ["USDC", "USDT"] else "BINANCE_SPOT",
                        "fee_estimate": "0.00 (Convert)" if asset in ["USDC", "USDT"] else f"${round(needed_usd * 0.001, 3)} (0.1%)",
                        "reasoning": f"Rebalance {asset} by {side}ing ${needed_usd:.2f} to align with target {target_pct:.1f}%."
                    })

        # Identify Idle Cash & Dust
        usdc_free = self.binance._portfolio_state.get("USDC", {}).get("free", 0.0)
        idle_cash = []
        if usdc_free > 1.0:
            idle_cash.append({
                "asset": "USDC",
                "amount": usdc_free,
                "amount_usd": round(usdc_free, 2),
                "type": "IDLE_STABLECOIN",
                "recommendation": "Convert to USDT at 0% fee to consolidate active margin capital."
            })

        return {
            "portfolio_value_usd": round(total_val, 2),
            "target_allocations": targets,
            "max_order_size_policy_usd": max_order,
            "drift_analysis": drift_analysis,
            "proposed_rebalance_orders": proposed_actions,
            "idle_cash_opportunities": idle_cash,
            "rebalance_required": len(proposed_actions) > 0,
            "estimated_total_friction_usd": round(len(proposed_actions) * 0.025, 2)
        }
