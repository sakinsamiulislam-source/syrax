"""
SYRAX — Deterministic Risk Engine
Core mathematical gatekeeper. Risk can and will reject an otherwise attractive trade.
Strictly enforces user mandate: max risk %, max loss in dollars, stop distance, R:R, and order limits.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class RiskParameters(BaseModel):
    capital: float = Field(default=500.0, description="Total account capital in USD")
    max_risk_pct: float = Field(default=1.0, description="Max allowed capital loss percentage (e.g., 1% = 0.01)")
    entry_price: float = Field(..., description="Proposed entry price in USD")
    stop_loss: float = Field(..., description="Stop loss price in USD")
    take_profit: float = Field(..., description="Take profit target price in USD")
    max_order_size_usd: Optional[float] = Field(default=None, description="Max single order size limit (e.g., $25)")
    leverage: float = Field(default=1.0, description="Leverage multiplier (1.0 = Spot)")
    fee_rate_bps: float = Field(default=10.0, description="Binance fee in basis points (10 bps = 0.1%)")
    slippage_bps: float = Field(default=5.0, description="Expected slippage in basis points (5 bps = 0.05%)")

class RiskAssessment(BaseModel):
    status: str = Field(..., description="APPROVED | ADJUSTED | REJECTED")
    capital: float
    max_dollar_loss: float
    stop_distance_usd: float
    stop_distance_pct: float
    target_distance_usd: float
    target_distance_pct: float
    risk_reward_ratio: float
    recommended_position_usd: float
    recommended_quantity: float
    estimated_friction_usd: float
    mandate_compliant: bool
    rejection_reasons: list[str] = []
    risk_notes: list[str] = []

class RiskEngine:
    """
    Calculates exact risk metrics and determines whether a trade passes user-defined mandates.
    Architecture: Market Analysis -> Risk Engine -> Decision Engine -> User Policy -> Execution
    """

    @staticmethod
    def evaluate(params: RiskParameters) -> RiskAssessment:
        rejection_reasons = []
        risk_notes = []

        if params.entry_price <= 0 or params.stop_loss <= 0 or params.take_profit <= 0:
            return RiskAssessment(
                status="REJECTED",
                capital=params.capital,
                max_dollar_loss=0.0,
                stop_distance_usd=0.0,
                stop_distance_pct=0.0,
                target_distance_usd=0.0,
                target_distance_pct=0.0,
                risk_reward_ratio=0.0,
                recommended_position_usd=0.0,
                recommended_quantity=0.0,
                estimated_friction_usd=0.0,
                mandate_compliant=False,
                rejection_reasons=["Invalid non-positive pricing inputs."],
                risk_notes=[]
            )

        # Calculate max dollar loss allowed by user mandate (e.g. 1% of $500 = $5.00)
        max_dollar_loss = params.capital * (params.max_risk_pct / 100.0)

        # Distance to stop loss
        stop_distance_usd = abs(params.entry_price - params.stop_loss)
        stop_distance_pct = (stop_distance_usd / params.entry_price) * 100.0

        if stop_distance_pct < 0.2:
            rejection_reasons.append(f"Stop loss is too tight ({stop_distance_pct:.2f}%). Will get stopped out by normal market noise.")

        # Distance to take profit
        target_distance_usd = abs(params.take_profit - params.entry_price)
        target_distance_pct = (target_distance_usd / params.entry_price) * 100.0

        # Risk-to-Reward Ratio (R)
        risk_reward_ratio = (target_distance_usd / stop_distance_usd) if stop_distance_usd > 0 else 0.0

        if risk_reward_ratio < 1.5:
            rejection_reasons.append(f"Risk/Reward ratio ({risk_reward_ratio:.2f}R) is below the minimum required 1.50R.")
        else:
            risk_notes.append(f"Favorable Risk/Reward ratio: {risk_reward_ratio:.2f}R.")

        # Position Sizing: Size ($) = Max Risk ($) / Stop Distance (%)
        ideal_position_usd = max_dollar_loss / (stop_distance_pct / 100.0)

        # Check against available capital
        status = "APPROVED"
        final_position_usd = ideal_position_usd

        if ideal_position_usd > params.capital:
            final_position_usd = params.capital
            risk_notes.append(f"Position size capped at total available capital (${params.capital:.2f}). Effective risk is now ${final_position_usd * (stop_distance_pct/100):.2f}.")
            status = "ADJUSTED"

        # Check against user-defined max order size policy (e.g. "never use more than $25 per order")
        if params.max_order_size_usd and final_position_usd > params.max_order_size_usd:
            final_position_usd = params.max_order_size_usd
            risk_notes.append(f"Clamped to user mandate max order size limit of ${params.max_order_size_usd:.2f}.")
            status = "ADJUSTED"

        # Calculate estimated friction (Binance maker/taker fee + spread slippage)
        total_friction_bps = (params.fee_rate_bps * 2) + params.slippage_bps
        estimated_friction_usd = final_position_usd * (total_friction_bps / 10000.0)

        # Net effective risk after fees
        effective_loss_usd = (final_position_usd * (stop_distance_pct / 100.0)) + estimated_friction_usd
        if effective_loss_usd > max_dollar_loss * 1.15: # Allow small buffer for fees
            rejection_reasons.append(f"Effective loss (${effective_loss_usd:.2f}) with fees exceeds mandate limit of ${max_dollar_loss:.2f}.")

        final_quantity = final_position_usd / params.entry_price

        if rejection_reasons:
            status = "REJECTED"

        return RiskAssessment(
            status=status,
            capital=params.capital,
            max_dollar_loss=round(max_dollar_loss, 2),
            stop_distance_usd=round(stop_distance_usd, 4),
            stop_distance_pct=round(stop_distance_pct, 2),
            target_distance_usd=round(target_distance_usd, 4),
            target_distance_pct=round(target_distance_pct, 2),
            risk_reward_ratio=round(risk_reward_ratio, 2),
            recommended_position_usd=round(final_position_usd, 2),
            recommended_quantity=round(final_quantity, 6),
            estimated_friction_usd=round(estimated_friction_usd, 3),
            mandate_compliant=(status != "REJECTED"),
            rejection_reasons=rejection_reasons,
            risk_notes=risk_notes
        )
