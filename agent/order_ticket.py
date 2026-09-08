"""
SYRAX — Phase 6: Order Ticket Core & Human Confirmation Boundary
Implements immutable order tickets, cryptographic canonical hashing,
TTL-based expiration, atomic consumption, and ticket registry.
"""

import time
import json
import hashlib
import secrets
import asyncio
import logging
import os
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("syrax.order_ticket")


# =============================================================================
# 1. TICKET STATUS ENUM
# =============================================================================

class TicketStatus(str, Enum):
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"
    REJECTED_BY_GATEWAY = "REJECTED_BY_GATEWAY"
    CANCELLED = "CANCELLED"


# =============================================================================
# 2. CANONICAL HASH COMPUTATION
# =============================================================================

def compute_ticket_hash(
    parent_order_id: str,
    symbol: str,
    side: str,
    order_type: str,
    notional_usd: float,
    decision_price: float,
    limit_price: Optional[float],
    stop_loss: float,
    take_profit: Optional[float],
    leverage: int,
    market_type: str,
    venue: str,
    environment: str,
    account_scope: str
) -> str:
    """
    Computes a deterministic SHA-256 hash over immutable order ticket parameters.
    Mutable fields (status, timestamps, execution IDs) are strictly excluded.
    """
    canonical_dict = {
        "parent_order_id": str(parent_order_id).strip().upper(),
        "symbol": str(symbol).strip().upper(),
        "side": str(side).strip().upper(),
        "order_type": str(order_type).strip().upper(),
        "notional_usd": round(float(notional_usd), 4),
        "decision_price": round(float(decision_price), 6),
        "limit_price": round(float(limit_price), 6) if limit_price is not None else None,
        "stop_loss": round(float(stop_loss), 6),
        "take_profit": round(float(take_profit), 6) if take_profit is not None else None,
        "leverage": int(leverage),
        "market_type": str(market_type).strip().upper(),
        "venue": str(venue).strip().lower(),
        "environment": str(environment).strip().upper(),
        "account_scope": str(account_scope).strip().lower()
    }
    canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# =============================================================================
# 3. ORDER TICKET MODEL
# =============================================================================

class OrderTicket(BaseModel):
    """
    Immutable Order Ticket compiled before execution.
    Requires exact human confirmation token 'CONFIRM PO-XXXXXX' to unlock gateway routing.
    """
    parent_order_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    order_type: str = "MARKET"  # "MARKET" or "LIMIT"
    quantity: Optional[float] = None
    notional_usd: float
    decision_price: float
    limit_price: Optional[float] = None
    stop_loss: float
    take_profit: Optional[float] = None
    leverage: int = 1
    market_type: str = "SPOT"  # "SPOT", "FUTURES"
    venue: str = "binance"
    risk_amount_usd: float = 0.0
    risk_pct: float = 1.0
    confidence: float = 0.95
    environment: str = "SIMULATED"  # "SIMULATED", "TESTNET", "LIVE"
    account_scope: str = "default"
    created_at: float = Field(default_factory=time.time)
    ttl_seconds: float = 120.0
    expires_at: float = 0.0
    status: TicketStatus = TicketStatus.PENDING_CONFIRMATION
    ticket_hash: str = ""
    consumed_at: Optional[float] = None
    gateway_order_id: Optional[str] = None
    execution_receipt_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    invalidation_reason: Optional[str] = None
    ai_thesis: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_hash_valid(self) -> bool:
        """Verifies cryptographic integrity of the ticket against tampering."""
        expected = compute_ticket_hash(
            parent_order_id=self.parent_order_id,
            symbol=self.symbol,
            side=self.side,
            order_type=self.order_type,
            notional_usd=self.notional_usd,
            decision_price=self.decision_price,
            limit_price=self.limit_price,
            stop_loss=self.stop_loss,
            take_profit=self.take_profit,
            leverage=self.leverage,
            market_type=self.market_type,
            venue=self.venue,
            environment=self.environment,
            account_scope=self.account_scope
        )
        return self.ticket_hash == expected

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """Checks if the ticket has surpassed its TTL."""
        now = current_time or time.time()
        return now > self.expires_at

    def remaining_ttl_seconds(self, current_time: Optional[float] = None) -> float:
        """Returns remaining seconds before ticket expiration."""
        now = current_time or time.time()
        rem = self.expires_at - now
        return max(0.0, round(rem, 1))


# =============================================================================
# 4. ORDER TICKET REGISTRY
# =============================================================================

class OrderTicketRegistry:
    """
    Thread-safe, atomic Order Ticket Registry.
    Tracks active tickets, manages TTL pruning, validates cryptographic hashes,
    and guarantees single-use atomic consumption.
    """

    def __init__(self, persistence_path: Optional[str] = "scratch/order_tickets.json"):
        self._tickets: Dict[str, OrderTicket] = {}
        self._lock = asyncio.Lock()
        self.persistence_path = persistence_path
        self._load_from_disk()

    def _generate_parent_order_id(self) -> str:
        """Generates a unique parent order ID in the format PO-XXXXXX."""
        while True:
            suffix = secrets.token_hex(3).upper()  # 6 chars
            poid = f"PO-{suffix}"
            if poid not in self._tickets:
                return poid

    def _load_from_disk(self):
        """Loads existing tickets from disk on initialization if available."""
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    t = OrderTicket(**item)
                    self._tickets[t.parent_order_id] = t
            logger.info(f"Loaded {len(self._tickets)} order tickets from {self.persistence_path}")
        except Exception as e:
            logger.warning(f"Failed to load order tickets from disk: {e}")

    def _save_to_disk(self):
        """Persists tickets to disk."""
        if not self.persistence_path:
            return
        try:
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                data = [t.model_dump() for t in self._tickets.values()]
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist order tickets: {e}")

    async def create_ticket(
        self,
        symbol: str,
        side: str,
        order_type: str,
        notional_usd: float,
        decision_price: float,
        stop_loss: float,
        limit_price: Optional[float] = None,
        take_profit: Optional[float] = None,
        leverage: int = 1,
        market_type: str = "SPOT",
        venue: str = "binance",
        risk_amount_usd: float = 0.0,
        risk_pct: float = 1.0,
        confidence: float = 0.95,
        environment: str = "SIMULATED",
        account_scope: str = "default",
        quantity: Optional[float] = None,
        ttl_seconds: float = 120.0,
        ai_thesis: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        invalidate_previous_pending: bool = True
    ) -> OrderTicket:
        """
        Compiles and registers a new OrderTicket in state PENDING_CONFIRMATION.
        Optionally invalidates previously pending tickets for the symbol.
        """
        async with self._lock:
            # Invalidate previous pending tickets if requested
            if invalidate_previous_pending:
                for existing in self._tickets.values():
                    if existing.status == TicketStatus.PENDING_CONFIRMATION:
                        existing.status = TicketStatus.INVALIDATED
                        existing.invalidation_reason = f"Superseded by new order draft ({side} {symbol})"

            parent_order_id = self._generate_parent_order_id()
            now = time.time()
            expires_at = now + ttl_seconds

            # Quantity computation if not passed
            if not quantity and decision_price > 0:
                raw_qty = notional_usd / decision_price
                if raw_qty >= 100:
                    quantity = round(raw_qty, 2)
                elif raw_qty >= 1:
                    quantity = round(raw_qty, 4)
                elif raw_qty >= 0.001:
                    quantity = round(raw_qty, 6)
                else:
                    quantity = round(raw_qty, 8)


            # Cryptographic hash
            tkt_hash = compute_ticket_hash(
                parent_order_id=parent_order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                notional_usd=notional_usd,
                decision_price=decision_price,
                limit_price=limit_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                leverage=leverage,
                market_type=market_type,
                venue=venue,
                environment=environment,
                account_scope=account_scope
            )

            ticket = OrderTicket(
                parent_order_id=parent_order_id,
                symbol=symbol,
                side=side.upper(),
                order_type=order_type.upper(),
                quantity=quantity,
                notional_usd=notional_usd,
                decision_price=decision_price,
                limit_price=limit_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                leverage=leverage,
                market_type=market_type.upper(),
                venue=venue.lower(),
                risk_amount_usd=risk_amount_usd,
                risk_pct=risk_pct,
                confidence=confidence,
                environment=environment.upper(),
                account_scope=account_scope.lower(),
                created_at=now,
                ttl_seconds=ttl_seconds,
                expires_at=expires_at,
                status=TicketStatus.PENDING_CONFIRMATION,
                ticket_hash=tkt_hash,
                ai_thesis=ai_thesis,
                metadata=metadata or {}
            )

            self._tickets[parent_order_id] = ticket
            self._save_to_disk()
            logger.info(f"Created OrderTicket {parent_order_id} ({side} {symbol} ${notional_usd}) with hash {tkt_hash[:12]}... (TTL: {ttl_seconds}s)")
            return ticket

    async def get_ticket(self, parent_order_id: str) -> Optional[OrderTicket]:
        """
        Retrieves an order ticket by ID, checking and updating TTL expiration.
        """
        async with self._lock:
            ticket = self._tickets.get(parent_order_id.strip().upper())
            if not ticket:
                return None
            if ticket.status == TicketStatus.PENDING_CONFIRMATION and ticket.is_expired():
                ticket.status = TicketStatus.EXPIRED
                ticket.invalidation_reason = "TTL expired before human confirmation"
                self._save_to_disk()
            return ticket

    async def confirm_ticket(
        self,
        parent_order_id: str,
        user_input_token: str
    ) -> Tuple[bool, Optional[OrderTicket], str]:
        """
        Atomically validates and transitions an OrderTicket from PENDING_CONFIRMATION to CONFIRMED.
        Guarantees single-use atomic consumption.
        """
        poid = parent_order_id.strip().upper()
        token = user_input_token.strip().upper()
        expected_token = f"CONFIRM {poid}"

        if token != expected_token:
            return False, None, f"Invalid confirmation token. Expected '{expected_token}', received '{token}'."

        async with self._lock:
            ticket = self._tickets.get(poid)
            if not ticket:
                return False, None, f"Order ticket '{poid}' not found in registry."

            # Check expiration
            if ticket.is_expired():
                ticket.status = TicketStatus.EXPIRED
                ticket.invalidation_reason = f"Ticket expired {int(time.time() - ticket.expires_at)}s ago (TTL: {ticket.ttl_seconds}s)"
                self._save_to_disk()
                return False, ticket, f"Order ticket {poid} has expired. TTL was {ticket.ttl_seconds} seconds."

            # Check status
            if ticket.status == TicketStatus.CONFIRMED or ticket.status == TicketStatus.EXECUTED:
                return False, ticket, f"Order ticket {poid} has already been consumed / executed."

            if ticket.status != TicketStatus.PENDING_CONFIRMATION:
                return False, ticket, f"Order ticket {poid} cannot be confirmed (current status: {ticket.status.value})."

            # Check cryptographic integrity
            if not ticket.is_hash_valid():
                ticket.status = TicketStatus.INVALIDATED
                ticket.invalidation_reason = "Cryptographic integrity violation: parameter hash mismatch."
                self._save_to_disk()
                return False, ticket, f"Security Violation: Ticket {poid} failed hash verification."

            # Atomically lock and consume ticket
            ticket.status = TicketStatus.CONFIRMED
            ticket.consumed_at = time.time()
            self._save_to_disk()
            logger.info(f"OrderTicket {poid} successfully confirmed and locked for execution.")
            return True, ticket, f"Order ticket {poid} confirmed successfully."

    async def mark_executed(
        self,
        parent_order_id: str,
        gateway_order_id: str,
        execution_receipt_id: Optional[str] = None
    ) -> Optional[OrderTicket]:
        """Marks a ticket as executed following successful UnifiedExecutionGateway processing."""
        async with self._lock:
            ticket = self._tickets.get(parent_order_id.strip().upper())
            if not ticket:
                return None
            ticket.status = TicketStatus.EXECUTED
            ticket.gateway_order_id = gateway_order_id
            ticket.execution_receipt_id = execution_receipt_id or gateway_order_id
            self._save_to_disk()
            logger.info(f"OrderTicket {parent_order_id} marked EXECUTED (Gateway ID: {gateway_order_id})")
            return ticket

    async def mark_rejected_by_gateway(
        self,
        parent_order_id: str,
        reason: str
    ) -> Optional[OrderTicket]:
        """Marks a ticket as rejected if the UnifiedExecutionGateway vetoes execution."""
        async with self._lock:
            ticket = self._tickets.get(parent_order_id.strip().upper())
            if not ticket:
                return None
            ticket.status = TicketStatus.REJECTED_BY_GATEWAY
            ticket.rejection_reason = reason
            self._save_to_disk()
            logger.warning(f"OrderTicket {parent_order_id} marked REJECTED_BY_GATEWAY: {reason}")
            return ticket

    async def invalidate_ticket(
        self,
        parent_order_id: str,
        reason: str = "Parameters modified"
    ) -> Optional[OrderTicket]:
        """Explicitly invalidates a pending ticket."""
        async with self._lock:
            ticket = self._tickets.get(parent_order_id.strip().upper())
            if not ticket:
                return None
            if ticket.status == TicketStatus.PENDING_CONFIRMATION:
                ticket.status = TicketStatus.INVALIDATED
                ticket.invalidation_reason = reason
                self._save_to_disk()
                logger.info(f"OrderTicket {parent_order_id} invalidated: {reason}")
            return ticket

    async def cancel_ticket(
        self,
        parent_order_id: str,
        reason: str = "User cancelled"
    ) -> Optional[OrderTicket]:
        """Cancels a pending ticket upon user request."""
        async with self._lock:
            ticket = self._tickets.get(parent_order_id.strip().upper())
            if not ticket:
                return None
            if ticket.status == TicketStatus.PENDING_CONFIRMATION:
                ticket.status = TicketStatus.CANCELLED
                ticket.invalidation_reason = reason
                self._save_to_disk()
                logger.info(f"OrderTicket {parent_order_id} cancelled: {reason}")
            return ticket

    async def invalidate_pending_tickets(
        self,
        symbol: Optional[str] = None,
        reason: str = "Parameters modified or superseded"
    ) -> int:
        """Invalidates all pending tickets, optionally filtering by symbol."""
        count = 0
        async with self._lock:
            for ticket in self._tickets.values():
                if ticket.status == TicketStatus.PENDING_CONFIRMATION:
                    if symbol is None or ticket.symbol == symbol:
                        ticket.status = TicketStatus.INVALIDATED
                        ticket.invalidation_reason = reason
                        count += 1
            if count > 0:
                self._save_to_disk()
                logger.info(f"Invalidated {count} pending tickets (reason: {reason})")
        return count

    async def prune_expired(self) -> List[str]:
        """Prunes and marks expired tickets past TTL."""
        expired_ids = []
        now = time.time()
        async with self._lock:
            for poid, ticket in self._tickets.items():
                if ticket.status == TicketStatus.PENDING_CONFIRMATION and now > ticket.expires_at:
                    ticket.status = TicketStatus.EXPIRED
                    ticket.invalidation_reason = "TTL expired"
                    expired_ids.append(poid)
            if expired_ids:
                self._save_to_disk()
                logger.info(f"Pruned {len(expired_ids)} expired tickets: {expired_ids}")
        return expired_ids

    def get_pending_tickets(self, symbol: Optional[str] = None) -> List[OrderTicket]:
        """Returns all currently pending unexpired tickets."""
        now = time.time()
        res = []
        for t in self._tickets.values():
            if t.status == TicketStatus.PENDING_CONFIRMATION and now <= t.expires_at:
                if symbol is None or t.symbol == symbol:
                    res.append(t)
        return sorted(res, key=lambda x: x.created_at, reverse=True)


def format_crypto_price(price: Optional[float]) -> str:
    """
    Dynamically formats cryptocurrency prices across all magnitudes:
    - Sub-cent / micro-cap meme tokens (< $0.01): 8 decimal places (e.g. $0.00003120)
    - Sub-dollar tokens (< $1.0): 4 decimal places (e.g. $0.4500)
    - Standard assets (>= $1.0): 2 decimal places with thousands separators (e.g. $103.14)
    """
    if price is None:
        return "N/A"
    try:
        p = float(price)
    except (ValueError, TypeError):
        return "N/A"
    if p <= 0:
        return "$0.00"
    if p < 0.01:
        return f"${p:.8f}"
    if p < 1.0:
        return f"${p:.4f}"
    return f"${p:,.2f}"



def format_order_ticket_card(ticket: OrderTicket) -> Dict[str, Any]:
    """
    Formats an OrderTicket into a clean structured card for UI rendering and AI chat.
    Highlights key parameters, risk invariants, fee estimates, TTL, and explicit confirmation command.
    """
    remaining_ttl = int(ticket.remaining_ttl_seconds())
    price_fmt = format_crypto_price(ticket.decision_price)
    limit_fmt = format_crypto_price(ticket.limit_price) if ticket.limit_price else "N/A (Market Order)"
    sl_fmt = format_crypto_price(ticket.stop_loss)
    tp_fmt = format_crypto_price(ticket.take_profit) if ticket.take_profit else "N/A"
    
    # Calculate estimated transaction fee
    is_futures = ticket.market_type.upper() in ("FUTURES", "FUTURES_USDM", "FUTURES_COINM")
    est_fee_rate = 0.0005 if is_futures else 0.0010
    fee_rate_str = "0.05% Futures Taker" if is_futures else "0.10% Spot Taker"
    est_fee_usd = round(ticket.notional_usd * est_fee_rate, 4)
    fee_display_str = f"~${est_fee_usd:.4f} USDT ({fee_rate_str})"
    
    headline = f"📋 Order Ticket Generated: {ticket.parent_order_id} ({ticket.side} {ticket.symbol})"
    
    explanation = (
        f"An exact immutable order ticket **{ticket.parent_order_id}** has been prepared.\n\n"
        f"• **Asset**: `{ticket.symbol}` ({ticket.market_type} on `{ticket.venue}`)\n"
        f"• **Action**: `{ticket.side}` ({ticket.order_type})\n"
        f"• **Notional**: `${ticket.notional_usd:,.2f} USD` (Qty: `{ticket.quantity or 0.0}`)\n"
        f"• **Decision Price**: `{price_fmt}`\n"
        f"• **Limit Price**: `{limit_fmt}`\n"
        f"• **Mandatory Stop Loss**: `{sl_fmt}`\n"
        f"• **Take Profit**: `{tp_fmt}`\n"
        f"• **Estimated Fee**: `{fee_display_str}`\n"
        f"• **Leverage**: `{ticket.leverage}x`\n"
        f"• **Risk Amount**: `${ticket.risk_amount_usd:,.2f}` ({ticket.risk_pct}% of capital)\n"
        f"• **Environment**: `{ticket.environment}` | **Account Scope**: `{ticket.account_scope}`\n"
        f"• **TTL Expiration**: `{remaining_ttl}s remaining`\n\n"
        f"🔒 **To authorize and execute this trade, send exact confirmation:**\n"
        f"### `CONFIRM {ticket.parent_order_id}`\n\n"
        f"_Note: Generic responses ('yes', 'ok', 'confirm') will NOT execute the order._"
    )

    return {
        "ticket_id": ticket.parent_order_id,
        "parent_order_id": ticket.parent_order_id,
        "symbol": ticket.symbol,
        "side": ticket.side,
        "order_type": ticket.order_type,
        "notional_usd": ticket.notional_usd,
        "quantity": ticket.quantity,
        "decision_price": ticket.decision_price,
        "limit_price": ticket.limit_price,
        "stop_loss": ticket.stop_loss,
        "take_profit": ticket.take_profit,
        "estimated_fee_usd": est_fee_usd,
        "fee_rate_str": fee_rate_str,
        "fee_display_str": fee_display_str,
        "leverage": ticket.leverage,
        "market_type": ticket.market_type,
        "venue": ticket.venue,
        "risk_amount_usd": ticket.risk_amount_usd,
        "risk_pct": ticket.risk_pct,
        "confidence": ticket.confidence,
        "environment": ticket.environment,
        "account_scope": ticket.account_scope,
        "created_at": ticket.created_at,
        "ttl_seconds": ticket.ttl_seconds,
        "expires_at": ticket.expires_at,
        "remaining_ttl_seconds": remaining_ttl,
        "status": ticket.status.value,
        "ticket_hash": ticket.ticket_hash,
        "confirmation_command": f"CONFIRM {ticket.parent_order_id}",
        "headline": headline,
        "explanation": explanation
    }

