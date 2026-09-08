export type DecisionType = "TRADE" | "WAIT" | "NO TRADE" | "PROTECT";
export type TradeabilityLabel = "TRADEABLE" | "WATCH" | "TRAP" | "AVOID";
export type ExecutionMode = "ANALYSIS" | "ASSISTED" | "GUARD";

export interface Holding {
  asset: string;
  free: number;
  locked: number;
  total: number;
  price_usd: number;
  value_usd: number;
  allocation_pct: number;
}

export interface Portfolio {
  total_value_usd: number;
  available_cash_usd: number;
  holdings: Holding[];
  account_type: string;
  execution_mode: string;
  updated_at: string;
}

export interface TradeSetup {
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  stop_dist_pct: number;
  target_dist_pct: number;
  risk_reward_ratio: number;
}

export interface Opportunity {
  symbol: string;
  last_price: number;
  change_24h: number;
  high_24h?: number;
  low_24h?: number;
  volume_24h: number;
  quote_volume_24h: number;
  sparkline?: number[];
  trend: string;
  momentum: string;
  spread_bps: number;
  liquidity_quality: "HIGH" | "MEDIUM" | "LOW";
  market_type?: "SPOT" | "FUTURES";
  is_alpha?: boolean;
  ai_score: number;
  label: TradeabilityLabel;
  decision: DecisionType;
  reasoning: string;
  setup: TradeSetup;
}

export interface RiskAssessment {
  status: "APPROVED" | "ADJUSTED" | "REJECTED";
  capital: number;
  max_dollar_loss: number;
  stop_distance_usd: number;
  stop_distance_pct: number;
  target_distance_usd: number;
  target_distance_pct: number;
  risk_reward_ratio: number;
  recommended_position_usd: number;
  recommended_quantity: number;
  estimated_friction_usd: number;
  mandate_compliant: boolean;
  rejection_reasons: string[];
  risk_notes: string[];
}

export interface SentryEvent {
  id: string;
  title: string;
  summary: string;
  token: string;
  timestamp: number;
  source: string;
  source_credibility: string;
  market_confirmed: boolean;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: string;
  action_recommended: string;
  reasoning: string;
}

export interface JournalEntry {
  id: string;
  timestamp: string;
  asset: string;
  decision: DecisionType;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  risk_amount_usd: number;
  risk_pct: number;
  status: string;
  realized_pnl_usd: number;
  reason: string;
  news_context: string;
  route?: string;
}

export interface AgenticStep {
  step: string;
  status: "DONE" | "RUNNING" | "PENDING";
  detail: string;
}

export interface ProposedAction {
  type: string;
  symbol?: string;
  side?: string;
  order_type?: string;
  quantity?: number;
  notional_usd?: number;
  entry_price?: number;
  stop_loss?: number;
  take_profit?: number;
  max_risk_usd?: number;
  risk_pct?: number;
  reward_risk_ratio?: number;
  affected_token?: string;
  recommendation?: string;
  confirmation_required?: boolean;
  route?: string;
}

export interface ExecutionReceipt {
  status: string;
  order_id?: string;
  trade_id?: string;
  symbol?: string;
  side?: string;
  term?: string;
  market_type?: string;
  leverage?: number;
  margin_type?: string;
  notional_usd?: number;
  margin_usd?: number;
  quantity?: number;
  entry_price?: number;
  exit_price?: number;
  realized_pnl_usd?: number;
  fee_usd?: number;
  fee_rate_pct?: number;
  fee_breakdown?: string;
  return_capital?: number;
  new_cash_usd?: number;
  stop_loss?: number;
  take_profit?: number;
  liquidation_price?: number;
  security_verdict?: string;
  rule_compliance?: string;
  action?: string;
  from_asset?: string;
  to_asset?: string;
  from_amount?: number;
  to_amount?: number;
  fee?: string;
  quote_id?: string;
  target_weights?: Record<string, number>;
  total_capital_protected_usd?: number;
  order_type?: string;
  limit_price?: number;
  live_price?: number;
  offset_pct?: number;
  message?: string;
}

export interface SecurityAudit {
  token: string;
  security_score: number;
  exploit_status: string;
  radar_status: string;
  active_exploits_count: number;
  contract_anomaly: boolean;
  spread_bps: number;
  change_24h: number;
  last_price: number;
  events_found: any[];
  recommendation: string;
}

export interface UserRules {
  capital_usd: number;
  max_risk_pct: number;
  max_order_size_usd: number;
  max_leverage: number;
  require_stop_loss: boolean;
  sentry_exploit_filter: boolean;
  execution_mode: string;
  target_allocations?: Record<string, number>;
}

export interface DebugIntentInspector {
  domain: "GENERAL" | "CRYPTO" | "MARKET" | "PORTFOLIO" | "TRADING" | "EXECUTION" | "SECURITY";
  intent: string;
  detected_asset?: string | null;
  resolved_asset?: string | null;
  active_context_asset?: string | null;
  requires_clarification: boolean;
  is_execution_intent: boolean;
  confidence: number;
}

export interface OrderTicketCardData {
  ticket_id: string;
  parent_order_id: string;
  symbol: string;
  side: "BUY" | "SELL" | string;
  order_type: "MARKET" | "LIMIT" | string;
  notional_usd: number;
  quantity?: number;
  decision_price: number;
  limit_price?: number | null;
  stop_loss: number;
  take_profit?: number | null;
  estimated_fee_usd?: number;
  fee_rate_str?: string;
  fee_display_str?: string;
  leverage: number;
  market_type: string;
  venue: string;
  risk_amount_usd: number;
  risk_pct: number;
  confidence: number;
  environment: string;
  account_scope: string;
  created_at: number;
  ttl_seconds: number;
  expires_at: number;
  remaining_ttl_seconds: number;
  status: "PENDING_CONFIRMATION" | "CONFIRMED" | "EXECUTED" | "EXPIRED" | "INVALIDATED" | "REJECTED_BY_GATEWAY" | "CANCELLED" | string;
  ticket_hash: string;
  confirmation_command: string;
  headline?: string;
  explanation?: string;
  ai_thesis?: string;
}

export interface DeepReasoningData {
  market_view?: string;
  thesis?: string;
  supporting_evidence?: string[];
  contradicting_evidence?: string[];
  bull_case?: string[];
  bear_case?: string[];
  key_risks?: string[];
  invalidation?: string;
  tradeability?: string;
  decision?: string;
  confidence?: number;
  explanation?: string;
}

export interface GuardianIncidentData {
  incident_id: string;
  timestamp: string;
  asset: string;
  rule: string;
  trigger: number;
  threshold: number;
  portfolio_state_ref?: Record<string, any>;
  action: string;
  execution_environment: string;
  gateway_order_id?: string | null;
  gateway_receipt?: Record<string, any> | null;
  result: string;
  explanation: string;
}

export interface GuardianStatusData {
  execution_mode: "MONITOR_ONLY" | "ASSISTED" | "AUTONOMOUS_GUARD" | string;
  peak_equity_usd: number;
  daily_starting_equity_usd: number;
  current_day: string;
  realized_pnl_today_usd: number;
  total_incidents: number;
  recent_incidents: GuardianIncidentData[];
  active_high_water_marks?: Record<string, number>;
  rules?: {
    name: string;
    description: string;
    threshold: string;
    status: "NOMINAL" | "TRIGGERED" | "MONITORING";
  }[];
}

export interface ChatResponse {
  query: string;
  elapsed_ms: number;
  command_type?: "TRADE" | "CLOSE" | "PROTECT" | "CONVERT" | "RULES_UPDATE" | "REBALANCE" | "RISK_AUDIT" | "DISCOVERY" | "CONVERSATION" | "EXPLANATION" | "PORTFOLIO" | "CLARIFICATION" | "MARKET_ANALYSIS" | "TRADE_PLAN" | "TRADE_CONFIRMATION" | "CONFIRMATION_REQUIRED";
  mandate: {
    capital_usd: number;
    max_risk_pct: number;
    max_order_size_usd: number;
    target_allocations: Record<string, number>;
    execution_mode: string;
    max_leverage?: number;
    require_stop_loss?: boolean;
    sentry_exploit_filter?: boolean;
  };
  active_rules?: UserRules;
  agentic_steps: AgenticStep[];
  target_asset?: string | null;
  decision?: DecisionType | "TICKET_GENERATED" | "CONFIRMATION_REQUIRED" | "CONFIRMATION_REJECTED" | null;
  tradeability?: string | null;
  headline: string;
  reason: string;
  explanation: string;
  invalidation?: string | null;
  max_risk_usd: number;
  market_analysis?: Opportunity;
  deep_reasoning?: DeepReasoningData;
  order_ticket?: OrderTicketCardData;
  ticket?: OrderTicketCardData;
  risk_assessment?: RiskAssessment;
  sentry_assessment?: Record<string, any>;
  proposed_action?: ProposedAction;
  execution_receipt?: ExecutionReceipt;
  security_audit?: SecurityAudit;
  journal_id: string;
  available_cash_usd: number;
  debug_intent_inspector?: DebugIntentInspector;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  response?: ChatResponse;
}

export interface SubWalletTrade {
  trade_id: string;
  symbol: string;
  side: "BUY" | "SELL";
  entry_price: number;
  quantity: number;
  current_price: number;
  notional_usd: number;
  unrealized_pnl_usd: number;
  unrealized_pnl_pct: number;
  stop_loss?: number;
  take_profit?: number;
  market_type: string;
  leverage?: number;
  margin_type?: "ISOLATED" | "CROSS";
  margin_usd?: number;
  liquidation_price?: number;
  funding_rate?: number;
  roe_pct?: number;
  status: "OPEN" | "CLOSED";
  health: "HEALTHY" | "IN_PROFIT" | "AT_RISK" | "STOP_LOSS_BREACHED" | "TAKE_PROFIT_REACHED";
  opened_at: string;
  closed_at?: string;
  exit_price?: number;
  realized_pnl_usd?: number;
  strategy?: string;
}

export interface OrderFillEvent {
  fill_id: string;
  timestamp: string;
  quantity: number;
  price: number;
  notional_usd: number;
  fee_usd: number;
  fee_breakdown: string;
}

export interface PendingOrder {
  order_id: string;
  trade_id: string;
  symbol: string;
  side: "BUY" | "SELL";
  term: string;
  order_type: "LIMIT";
  market_type: string;
  status: "PENDING" | "PARTIALLY_FILLED" | "FILLED" | "CANCELED" | "CANCELED_REMAINDER";
  requested_quantity: number;
  filled_quantity: number;
  remaining_quantity: number;
  fill_percentage: number;
  limit_price: number;
  live_price_at_placement?: number;
  current_market_price?: number;
  distance_to_market_pct?: number;
  average_fill_price?: number | null;
  fills?: OrderFillEvent[];
  notional_usd: number;
  margin_usd: number;
  reserved_usd: number;
  reserved_asset_qty: number;
  leverage: number;
  margin_type: string;
  fee_rate_pct: number;
  estimated_fee_usd: number;
  stop_loss?: number | null;
  take_profit?: number | null;
  environment: string;
  strategy: string;
  created_at: string;
  updated_at: string;
}

export interface SubWalletHolding {
  asset: string;
  free_quantity?: number;
  locked_quantity?: number;
  quantity: number;
  price_usd: number;
  value_usd: number;
  actual_allocation_pct: number;
  target_allocation_pct: number;
  drift_pct: number;
  drift_status: "BALANCED" | "OVERWEIGHT" | "UNDERWEIGHT";
  verdict: string;
}

export interface SubWalletAnalysis {
  sub_wallet_id?: string;
  allocated_budget_usd?: number;
  total_portfolio_value_usd?: number;
  available_cash_usd?: number;
  reserved_cash_usd?: number;
  cash_ratio_pct?: number;
  total_crypto_value_usd?: number;
  cash_allocation_pct?: number;
  crypto_allocation_pct?: number;
  holdings_count?: number;
  ongoing_trades_count?: number;
  pending_orders_count?: number;
  unrealized_pnl_usd?: number;
  realized_pnl_usd?: number;
  total_unrealized_pnl_usd?: number;
  status?: string;
  holdings?: SubWalletHolding[];
  pending_orders?: PendingOrder[];
  mandate_compliance?: string;
  updated_at?: string;
}

export interface TradeHistoryItem {
  order_id: string;
  trade_id: string;
  timestamp: string;
  symbol: string;
  market_type: string;
  side: string;
  term: string;
  price: number;
  quantity: number;
  notional_usd: number;
  margin_usd: number;
  leverage: number;
  fee_usd: number;
  fee_rate_pct: number;
  fee_breakdown: string;
  status: string;
  type: string;
  realized_pnl_usd?: number;
  notes?: string;
}

export interface SubWalletData {
  analysis: SubWalletAnalysis;
  ongoing_trades: SubWalletTrade[];
  pending_orders?: PendingOrder[];
  closed_trades: SubWalletTrade[];
  trade_history?: TradeHistoryItem[];
}

export interface MonitorEvent {
  id: string;
  timestamp: string;
  severity: "INFO" | "WARNING" | "CRITICAL" | "SUCCESS" | "TRIGGER";
  category: "TRADE_WATCH" | "PORTFOLIO_DRIFT" | "SENTRY_RADAR" | "HEARTBEAT";
  message: string;
  meta?: Record<string, any>;
}

export interface MonitorStatus {
  is_running: boolean;
  is_paused: boolean;
  interval_seconds: number;
  last_pulse: string;
  total_checks: number;
  active_monitored_trades: number;
  events: MonitorEvent[];
}

export interface MCPInfo {
  status?: string;
  mcp_url?: string;
  url?: string;
  version?: string;
  protocol?: string;
  server_name?: string;
  tools_count?: number;
  endpoints?: string[];
  tools?: { name: string; description: string }[];
  claude_config?: Record<string, any>;
  cursor_config?: Record<string, any>;
}

export interface BinanceMCPStatus {
  status?: "DISCONNECTED" | "CONNECTING" | "CONNECTED" | "UNAUTHORIZED" | "ERROR" | string;
  is_connected: boolean;
  connected?: boolean;
  account_scope?: {
    sub_account_id?: string;
    environment?: string;
  };
  endpoint?: string;
  sub_account_id?: string;
  auth_token_masked?: string;
  latency_ms?: number;
  connected_at?: string | null;
  last_synced_at?: string | null;
  error_message?: string | null;
  granted_scopes?: string[];
  available_tools_count?: number;
  available_tools?: string[];
  cached_holdings_count?: number;
  cached_positions_count?: number;
}

export interface TodayPnLBreakdown {
  total_pnl_usd: number;
  pnl_pct: number;
  realized_pnl_usd: number;
  unrealized_pnl_usd: number;
  fees_usd: number;
  funding_usd: number;
  status: "PROFIT" | "LOSS" | "NEUTRAL" | "UNAVAILABLE";
  timezone: string;
  is_live_mcp: boolean;
  sub_account_id?: string;
  note?: string;
}



export interface WalletAssetItem {
  asset: string;
  free: number;
  locked: number;
  total: number;
  price_usd: number;
  value_usd: number;
}

export interface WalletItemData {
  wallet_id: "SPOT" | "FUNDING" | "USDT_FUTURES" | "COIN_FUTURES" | "CROSS_MARGIN" | "EARN" | string;
  name: string;
  badge: string;
  description: string;
  icon: string;
  total_value_usd: number;
  assets: WalletAssetItem[];
  asset_count: number;
  allocation_pct?: number;
}

export interface InternalTransferReceipt {
  transfer_id: string;
  from_wallet: string;
  from_wallet_name: string;
  to_wallet: string;
  to_wallet_name: string;
  asset: string;
  amount: number;
  fee: number;
  status: string;
  timestamp: string;
  tx_hash: string;
}

export interface WalletsSummaryData {
  total_ecosystem_value_usd: number;
  wallet_count: number;
  wallets: WalletItemData[];
  recent_transfers: InternalTransferReceipt[];
  updated_at: string;
}
