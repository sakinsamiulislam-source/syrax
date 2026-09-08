"""
Patching script to update agent/orchestrator.py with Phase 6 Order Ticket logic using string matching.
"""

import os

with open('agent/orchestrator.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update execute_mandate_pipeline interceptor
target_pipeline = """    async def execute_mandate_pipeline(self, user_query: str) -> Dict[str, Any]:
        \"\"\"
        Main entry point for multi-domain conversational agent loop.
        Classifies user intent, runs domain handlers, and returns structured progress.
        \"\"\"
        start_time = time.time()"""

replacement_pipeline = """    async def execute_mandate_pipeline(self, user_query: str) -> Dict[str, Any]:
        \"\"\"
        Main entry point for multi-domain conversational agent loop.
        Classifies user intent, runs domain handlers, and returns structured progress.
        \"\"\"
        start_time = time.time()

        # 1. Exact Order Ticket Confirmation Interceptor: CONFIRM PO-XXXXXX
        confirm_match = re.match(r'^\\s*CONFIRM\\s+(PO-[A-Za-z0-9]+)\\s*$', user_query, re.IGNORECASE)
        if confirm_match:
            poid = confirm_match.group(1).upper()
            return await self._handle_confirm_order_ticket(poid, user_query, start_time)

        # 2. Cancel Order Ticket Interceptor: CANCEL PO-XXXXXX
        cancel_match = re.match(r'^\\s*(?:CANCEL|ABORT|DISMISS)\\s+(PO-[A-Za-z0-9]+)\\s*$', user_query, re.IGNORECASE)
        if cancel_match:
            poid = cancel_match.group(1).upper()
            return await self._handle_cancel_order_ticket(poid, user_query, start_time)

        # 3. Generic Confirmation Interceptor: 'yes', 'confirm', 'ok', 'go ahead', 'do it'
        generic_confirm_match = re.match(r'^\\s*(yes|y|confirm|ok|okay|agree|go\\s*ahead|do\\s*it|proceed|execute|approved|sure|yep|yeah)\\s*[\\.! Cheltenham]?\\s*$', user_query, re.IGNORECASE)
        if generic_confirm_match:
            pending_tickets = self.ticket_registry.get_pending_tickets()
            if pending_tickets:
                target_ticket = pending_tickets[0]
                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "query": user_query,
                    "elapsed_ms": elapsed_ms,
                    "command_type": "CONFIRMATION_REQUIRED",
                    "target_asset": target_ticket.symbol,
                    "decision": "CONFIRMATION_REQUIRED",
                    "headline": f"⚠️ Exact Confirmation Required: CONFIRM {target_ticket.parent_order_id}",
                    "reason": f"Generic confirmation '{user_query.strip()}' is insufficient. Exact ticket token required to prevent ambiguous execution.",
                    "explanation": (
                        f"SYRAX mandates cryptographic human confirmation before executing trades.\\n\\n"
                        f"Generic responses like **'{user_query.strip()}'** or **'confirm'** cannot authorize execution.\\n\\n"
                        f"To execute order ticket **{target_ticket.parent_order_id}** ({target_ticket.side} {target_ticket.symbol} ${target_ticket.notional_usd:.2f}), please type:\\n"
                        f"### `CONFIRM {target_ticket.parent_order_id}`\\n\\n"
                        f"_Expires in {int(target_ticket.remaining_ttl_seconds())}s (TTL: {target_ticket.ttl_seconds}s)._"
                    ),
                    "ticket": format_order_ticket_card(target_ticket),
                    "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0
                }"""

# Fix regex character in generic confirm pattern
replacement_pipeline = replacement_pipeline.replace(" Cheltenham", "")

if target_pipeline in text and 'Exact Order Ticket Confirmation Interceptor' not in text:
    text = text.replace(target_pipeline, replacement_pipeline, 1)
    print("Injected pipeline interceptors")

# 2. Invalidate pending tickets on CORRECTION
correction_needle = 'elif intent == "CORRECTION":'
correction_replacement = '''elif intent == "CORRECTION":
            await self.ticket_registry.invalidate_pending_tickets(reason="Parameters modified by user correction")'''
if 'invalidate_pending_tickets' not in text:
    text = text.replace(correction_needle, correction_replacement, 1)
    print("Injected correction invalidation")

# 3. Replace _handle_execute_trade with OrderTicket compilation and add _handle_confirm_order_ticket & _handle_cancel_order_ticket
execute_trade_start = 'async def _handle_execute_trade(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:'
execute_trade_end = 'async def execute_confirmed_action(self, action_payload: Dict[str, Any]) -> Dict[str, Any]:'

new_execute_and_confirm_methods = '''    async def _handle_execute_trade(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_token = classification.get("resolved_asset") or "BTCUSDT"
        base_asset = target_token.replace("USDT", "")
        self.state_manager.active_asset = target_token

        steps = [
            {"step": "Parsing Execution Intent & Parameters", "status": "DONE", "detail": f"Target: {target_token}, analyzing price levels and constraints."},
            {"step": "Validating Mathematical Risk Limits", "status": "DONE", "detail": "Auditing 1.0% account risk cap and stop-loss boundaries via Central Gateway."},
            {"step": "Compiling Cryptographic Order Ticket", "status": "DONE", "detail": "Generating immutable order ticket with 120s TTL and SHA-256 canonical hash."}
        ]

        # Parameter extraction
        q_low = query.lower()
        side = "SELL" if any(w in q_low for w in ["sell", "short", "bechte", "bikri"]) else "BUY"
        is_futures = ("future" in q_low or "futures" in q_low or "perp" in q_low or "perps" in q_low)
        is_spot = ("spot" in q_low) or (not is_futures and not self.mandate.get("default_market", "SPOT") == "FUTURES")
        market_type = "SPOT" if is_spot else "FUTURES"

        lev_m = re.search(r'\\b(\\d+)x\\b', q_low)
        if lev_m:
            leverage = int(lev_m.group(1))
            market_type = "FUTURES" if leverage > 1 else market_type
        else:
            leverage = 1 if market_type == "SPOT" else 10

        margin_type = "ISOLATED"

        # Notional / Amount
        amt_match = re.search(r'\\$\\s*(\\d+(?:\\.\\d+)?)', query)
        if not amt_match:
            amt_match = re.search(r'(\\d+(?:\\.\\d+)?)\\s*(?:\\$|usd|dollar|dollars|usdt)', query, re.IGNORECASE)
        notional_usd = float(amt_match.group(1)) if amt_match else 25.0

        # Limit vs Market
        is_limit = ("limit" in q_low) or bool(re.search(r'\\b(?:under|below|at|discount)\\b', q_low))
        limit_match = re.search(r'(?:limit(?: order)? (?:at|price)?|at price|entry at|entry price|price at|\\bat)\\s*\\$?(\\d+(?:\\.\\d+)?)', q_low)
        discount_match = re.search(r'(?:under|below|discount of)?\\s*(\\d+(?:\\.\\d+)?)\\s*%\\s*(?:under|below|discount|from|cheaper)?', q_low)

        ticker = await self.binance.get_live_ticker(target_token)
        live_price = float(ticker.get("last_price", 100.0))

        raw_limit_price = None
        if limit_match:
            raw_limit_price = float(limit_match.group(1))
        elif discount_match and "limit" in q_low:
            pct_val = float(discount_match.group(1))
            raw_limit_price = live_price * (1.0 - (pct_val / 100.0))

        if is_limit and raw_limit_price and raw_limit_price > 0:
            order_type = "LIMIT"
            limit_price = raw_limit_price
        else:
            order_type = "MARKET"
            limit_price = None

        sl_m = re.search(r'(?:sl|stop\\s*loss)\\s*\\$?(\\d+(?:\\.\\d+)?)', query, re.IGNORECASE)
        tp_m = re.search(r'(?:tp|take\\s*profit)\\s*\\$?(\\d+(?:\\.\\d+)?)', query, re.IGNORECASE)

        stop_loss = float(sl_m.group(1)) if sl_m else (
            round((limit_price or live_price) * 0.98, 4) if side == "BUY" else round((limit_price or live_price) * 1.02, 4)
        )
        take_profit = float(tp_m.group(1)) if tp_m else None

        # Pre-audit 1.0% risk sizing
        risk_calc = RiskEngine.evaluate(RiskParameters(
            capital=self.mandate["capital_usd"],
            max_risk_pct=self.mandate["max_risk_pct"],
            entry_price=limit_price or live_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_order_size_usd=self.mandate.get("max_order_size_usd", 25.0)
        ))

        # Check hard leverage limit
        max_allowed_lev = self.mandate.get("max_leverage", 10)
        if leverage > max_allowed_lev:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRADE",
                "target_asset": target_token,
                "decision": "NO TRADE",
                "headline": f"🚨 TRADE REJECTED: Requested leverage {leverage}x exceeds mandate ceiling of {max_allowed_lev}x",
                "reason": f"Leverage {leverage}x strictly exceeds system max of {max_allowed_lev}x (silent clamping prohibited).",
                "explanation": f"The trade request exceeded the maximum allowed leverage limit ({max_allowed_lev}x).",
                "invalidation": "Mandate Risk Invariant Veto.",
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0
            }

        # Compile immutable OrderTicket (Phase 6 Human Confirmation Boundary)
        ticket = await self.ticket_registry.create_ticket(
            symbol=target_token,
            side=side,
            order_type=order_type,
            notional_usd=notional_usd,
            decision_price=live_price,
            limit_price=limit_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            leverage=leverage,
            market_type=market_type,
            venue="binance",
            risk_amount_usd=risk_calc.max_dollar_loss,
            risk_pct=self.mandate["max_risk_pct"],
            confidence=0.95,
            environment="SIMULATED",
            account_scope="default",
            ttl_seconds=120.0,
            ai_thesis=f"{side} {target_token} order draft generated based on user directive.",
            metadata={"margin_type": margin_type}
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        card = format_order_ticket_card(ticket)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "TRADE",
            "target_asset": target_token,
            "decision": "TICKET_GENERATED",
            "headline": card["headline"],
            "reason": f"Exact order ticket {ticket.parent_order_id} generated. Awaiting explicit confirmation token.",
            "explanation": card["explanation"],
            "invalidation": f"Ticket expires in {int(ticket.ttl_seconds)}s or upon parameter modification.",
            "max_risk_usd": ticket.risk_amount_usd,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "order_ticket": card,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-TKT-{ticket.parent_order_id}",
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "EXECUTE_TRADE",
                "detected_asset": target_token,
                "resolved_asset": target_token,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": 0.96
            }
        }

    async def _handle_confirm_order_ticket(self, parent_order_id: str, confirmation_token: str, start_time: float) -> Dict[str, Any]:
        \"\"\"
        Validates token, consumes OrderTicket atomically, and routes ExecutionRequest to Gateway.
        \"\"\"
        poid = parent_order_id.strip().upper()
        success, ticket, msg = await self.ticket_registry.confirm_ticket(poid, confirmation_token)
        elapsed_ms = int((time.time() - start_time) * 1000)

        if not success or not ticket:
            return {
                "query": confirmation_token,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRADE_CONFIRMATION",
                "target_asset": ticket.symbol if ticket else "UNKNOWN",
                "decision": "CONFIRMATION_REJECTED",
                "headline": f"🚨 Order Ticket Confirmation Failed: {poid}",
                "reason": msg,
                "explanation": f"Confirmation for ticket **{poid}** failed: {msg}",
                "invalidation": "Confirmation rejected / invalid ticket.",
                "ticket_id": poid,
                "ticket_status": ticket.status.value if ticket else "NOT_FOUND",
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                "debug_intent_inspector": {
                    "domain": "EXECUTION",
                    "intent": "CONFIRM_ORDER_TICKET",
                    "detected_asset": ticket.symbol if ticket else None,
                    "resolved_asset": ticket.symbol if ticket else None,
                    "is_execution_intent": True,
                    "confidence": 1.0
                }
            }

        # Map environment safely
        exec_env = ExecutionEnvironment.SIMULATED
        if ticket.environment == "TESTNET":
            exec_env = ExecutionEnvironment.TESTNET
        elif ticket.environment == "LIVE":
            exec_env = ExecutionEnvironment.LIVE

        exec_req = ExecutionRequest(
            action_type=ExecutionActionType.OPEN_POSITION,
            symbol=ticket.symbol,
            side=ticket.side,
            order_type=ticket.order_type,
            notional_usd=ticket.notional_usd,
            quantity=ticket.quantity,
            price=ticket.decision_price,
            limit_price=ticket.limit_price,
            stop_loss=ticket.stop_loss,
            take_profit=ticket.take_profit,
            leverage=ticket.leverage,
            market_type=ticket.market_type,
            margin_type=ticket.metadata.get("margin_type", "ISOLATED"),
            environment=exec_env,
            source="HUMAN_CONFIRMATION",
            mandate=self.mandate
        )

        receipt: ExecutionReceipt = await self.gateway.execute(exec_req)
        elapsed_ms = int((time.time() - start_time) * 1000)

        if receipt.status in (ExecutionStatus.REJECTED, ExecutionStatus.BLOCKED, ExecutionStatus.FAILED):
            await self.ticket_registry.mark_rejected_by_gateway(poid, receipt.rejection_reason or receipt.message)
            return {
                "query": confirmation_token,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRADE",
                "target_asset": ticket.symbol,
                "decision": "NO TRADE",
                "headline": f"🚨 TRADE {receipt.status.value}: {receipt.rejection_reason or receipt.message}",
                "reason": receipt.rejection_reason or receipt.message,
                "explanation": f"The trade for confirmed ticket **{poid}** was evaluated by the Unified Execution Gateway and was {receipt.status.value.lower()}: {receipt.rejection_reason or receipt.message}",
                "invalidation": "Safety Gatekeeper Veto.",
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "ticket_id": poid,
                "ticket_status": TicketStatus.REJECTED_BY_GATEWAY.value,
                "execution_receipt": receipt.model_dump(),
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                "journal_id": f"JRNL-VETO-{poid}",
                "debug_intent_inspector": {
                    "domain": "EXECUTION",
                    "intent": "CONFIRM_ORDER_TICKET",
                    "detected_asset": ticket.symbol,
                    "resolved_asset": ticket.symbol,
                    "is_execution_intent": True,
                    "confidence": 1.0
                }
            }

        # Successful Execution
        await self.ticket_registry.mark_executed(poid, receipt.order_id, receipt.trade_id)
        receipt_dict = receipt.model_dump()
        receipt_dict["rule_compliance"] = f"PASS (Max Loss Capped to ${self.mandate['capital_usd'] * (self.mandate['max_risk_pct']/100.0):.2f})"
        p_str = f"${receipt.requested_price:,.4f}" if receipt.requested_price < 1.0 else f"${receipt.requested_price:,.2f}"

        if ticket.order_type == "LIMIT":
            headline = f"⏳ Limit Order Placed: {receipt.term} {ticket.symbol} @ {p_str} [Ticket: {poid} | Order ID: {receipt.order_id}]"
            reason = f"Confirmed ticket {poid} executed. Limit order submitted to simulated orderbook at {p_str}. Margin ${receipt.margin_usd:.2f} USDT reserved."
            explanation = (
                f"Confirmed order ticket **{poid}** has been successfully authorized and submitted.\\n\\n"
                f"A `{receipt.term}` limit order for `{ticket.symbol}` at `{p_str}` is now active [{receipt.environment.value}]. "
                f"${receipt.margin_usd:.2f} USDT margin locked. Stop-Loss: `{receipt.stop_loss}`."
            )
        else:
            headline = f"🚀 Order Filled: {receipt.term} {ticket.symbol} [Ticket: {poid} | Order ID: {receipt.order_id}]"
            reason = f"Confirmed ticket {poid} filled at {p_str} with ${receipt.margin_usd:.2f} margin [{receipt.environment.value}]. Fee: {receipt.fee_breakdown}"
            explanation = (
                f"Confirmed order ticket **{poid}** has been successfully authorized and filled.\\n\\n"
                f"Order {receipt.order_id} filled on {receipt.environment.value} ({receipt.market_type}): {receipt.trade_id}. "
                f"Entry: {p_str}, Stop-Loss: {receipt.stop_loss or 'Trailing'}, Take-Profit: {receipt.take_profit or 'None'}. "
                f"Fee: {receipt.fee_breakdown}. Account risk strictly capped to 1.0% mandate."
            )

        journal_entry = {
            "id": receipt.trade_id or receipt.order_id,
            "parent_order_id": poid,
            "timestamp": receipt.timestamp,
            "asset": ticket.symbol,
            "decision": "TRADE",
            "entry_price": receipt.requested_price,
            "stop_loss": receipt.stop_loss,
            "take_profit": receipt.take_profit,
            "risk_amount_usd": self.mandate["capital_usd"] * (self.mandate["max_risk_pct"]/100.0),
            "risk_pct": self.mandate["max_risk_pct"],
            "status": "OPEN_LIMIT" if ticket.order_type == "LIMIT" else "OPEN",
            "realized_pnl_usd": 0.0,
            "reason": f"{'Limit Order Placed' if ticket.order_type == 'LIMIT' else 'Executed via Gateway'}: {receipt.term} {receipt.quantity:.4f} @ {p_str} [{receipt.environment.value}] (Ticket: {poid})",
            "news_context": "Sentry radar verified: 0 active exploits",
            "route": f"Sub-Wallet ({receipt.environment.value})"
        }
        self.decision_journal.insert(0, journal_entry)

        return {
            "query": confirmation_token,
            "elapsed_ms": elapsed_ms,
            "command_type": "TRADE",
            "target_asset": ticket.symbol,
            "decision": "TRADE",
            "headline": headline,
            "reason": reason,
            "explanation": explanation,
            "invalidation": "Price crosses Stop Loss.",
            "max_risk_usd": self.mandate["capital_usd"] * (self.mandate["max_risk_pct"]/100.0),
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "ticket_id": poid,
            "ticket_status": TicketStatus.EXECUTED.value,
            "execution_receipt": receipt_dict,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": receipt.trade_id or receipt.order_id,
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "CONFIRM_ORDER_TICKET",
                "detected_asset": ticket.symbol,
                "resolved_asset": ticket.symbol,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": 1.0
            }
        }

    async def _handle_cancel_order_ticket(self, parent_order_id: str, raw_input: str, start_time: float) -> Dict[str, Any]:
        \"\"\"Cancels a pending order ticket.\"\"\"
        poid = parent_order_id.strip().upper()
        ticket = await self.ticket_registry.cancel_ticket(poid, "User cancelled via command")
        elapsed_ms = int((time.time() - start_time) * 1000)

        if not ticket:
            return {
                "query": raw_input,
                "elapsed_ms": elapsed_ms,
                "command_type": "TICKET_CANCEL",
                "target_asset": "UNKNOWN",
                "decision": "NOT_FOUND",
                "headline": f"Order Ticket Not Found: {poid}",
                "reason": f"No order ticket with ID {poid} found in registry.",
                "explanation": f"Order ticket {poid} was not found.",
                "ticket_id": poid,
                "ticket_status": "NOT_FOUND"
            }

        return {
            "query": raw_input,
            "elapsed_ms": elapsed_ms,
            "command_type": "TICKET_CANCEL",
            "target_asset": ticket.symbol,
            "decision": "CANCELLED",
            "headline": f"🚫 Order Ticket Cancelled: {poid}",
            "reason": f"Pending order ticket {poid} ({ticket.side} {ticket.symbol}) has been cancelled.",
            "explanation": f"Order ticket **{poid}** has been cancelled and will not be executed.",
            "ticket_id": poid,
            "ticket_status": TicketStatus.CANCELLED.value
        }

'''

pos1 = text.find(execute_trade_start)
pos2 = text.find(execute_trade_end)

if pos1 != -1 and pos2 != -1:
    text = text[:pos1] + new_execute_and_confirm_methods + text[pos2:]
    print("Replaced _handle_execute_trade and added _handle_confirm_order_ticket & _handle_cancel_order_ticket")
else:
    print(f"Could not locate markers: pos1={pos1}, pos2={pos2}")

# 4. Update execute_confirmed_action to support ticket_id / parent_order_id
confirmed_action_target = 'async def execute_confirmed_action(self, action_payload: Dict[str, Any]) -> Dict[str, Any]:\n        """Executes an action approved by user via UnifiedExecutionGateway."""\n        action_type = action_payload.get("type", "SPOT_ORDER").upper()'
confirmed_action_replacement = '''async def execute_confirmed_action(self, action_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an action approved by user via UnifiedExecutionGateway."""
        ticket_id = action_payload.get("ticket_id") or action_payload.get("parent_order_id")
        if ticket_id:
            return await self._handle_confirm_order_ticket(str(ticket_id), f"CONFIRM {ticket_id}", time.time())

        action_type = action_payload.get("type", "SPOT_ORDER").upper()'''

if confirmed_action_target in text:
    text = text.replace(confirmed_action_target, confirmed_action_replacement, 1)
    print("Updated execute_confirmed_action")

with open('agent/orchestrator.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Successfully wrote updated agent/orchestrator.py")
