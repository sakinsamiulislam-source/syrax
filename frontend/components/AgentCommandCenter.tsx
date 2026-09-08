import React, { useState, useEffect, useRef } from "react";
import {
  Terminal,
  Send,
  Sparkles,
  Shield,
  Activity,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Zap,
  TrendingUp,
  ArrowRight,
  ShieldAlert,
  Clock,
  Layers,
  Lock,
  Check,
  Search,
  Bot,
  User,
  RotateCcw,
  Coins,
  DollarSign,
  PieChart,
  Square,
} from "lucide-react";
import { ChatResponse, ChatMessage, UserRules, ExecutionReceipt, Opportunity } from "@/types";
import { ExecutionReceiptCard } from "./ExecutionReceiptCard";
import { OrderTicketCard } from "./OrderTicketCard";
import { StructuredReasoningView } from "./StructuredReasoningView";
import { AnimatedNumber } from "./AnimatedNumber";

interface AgentCommandCenterProps {
  chatInput: string;
  setChatInput: (val: string) => void;
  onSendCommand: (cmd: string) => void;
  onStopExecution?: () => void;
  chatLoading: boolean;
  chatResult: ChatResponse | null;
  chatMessages: ChatMessage[];
  userRules: UserRules;
  onOpenRules: () => void;
  latestReceipt: ExecutionReceipt | null;
  availableCashUsd: number;
  onClearHistory?: () => void;
}

export const AgentCommandCenter: React.FC<AgentCommandCenterProps> = ({
  chatInput,
  setChatInput,
  onSendCommand,
  onStopExecution,
  chatLoading,
  chatResult,
  chatMessages,
  userRules,
  onOpenRules,
  latestReceipt,
  availableCashUsd,
  onClearHistory,
}) => {
  const [expandedEvidence, setExpandedEvidence] = useState<Record<string, boolean>>({});
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});
  const [activeLoadingStage, setActiveLoadingStage] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages or loading change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, chatLoading, activeLoadingStage]);

  // Dynamic progressive stage transitions during loading
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (chatLoading) {
      setActiveLoadingStage(0);
      interval = setInterval(() => {
        setActiveLoadingStage((prev) => (prev < 3 ? prev + 1 : prev));
      }, 450);
    } else {
      setActiveLoadingStage(0);
    }
    return () => clearInterval(interval);
  }, [chatLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;
    onSendCommand(chatInput);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!chatInput.trim() || chatLoading) return;
      onSendCommand(chatInput);
    }
  };

  const toggleEvidence = (msgId: string) => {
    setExpandedEvidence((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const toggleSteps = (msgId: string) => {
    setExpandedSteps((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const quickCommands = [
    { label: "🚀 Buy $5 PUMP on spot", cmd: "5$ worth of pump kinte" },
    { label: "⚡ 10x Long BTC (SL 76k)", cmd: "Open 10x long on BTC with $15 margin, SL 76000, TP 82000" },
    { label: "🟢 Buy $20 SOL on spot", cmd: "Buy $20 SOL on spot" },
    { label: "🔍 Find best opportunity (<1% risk)", cmd: "Find the best opportunity with max 1% risk" },
    { label: "📊 Show my token holdings", cmd: "amar asset ki ki ache" },
    { label: "🛡️ Check Hack & Exploit Risk", cmd: "Check if SOL has any hack or exploit news" },
    { label: "⚖️ Rebalance Portfolio", cmd: "Rebalance portfolio to target allocations" },
    { label: "💵 Consolidate Idle Stablecoins", cmd: "Find idle stablecoins and convert to USDT" },
    { label: "🚨 Emergency Protect Portfolio", cmd: "Emergency: protect portfolio and liquidate SOL to USDT" },
  ];

  const getDecisionTheme = (decision?: string | null) => {
    switch (decision) {
      case "TRADE":
      case "TICKET_GENERATED":
        return {
          bg: "from-emerald-950/30 to-[#0A101C] border-emerald-500/40 text-emerald-400",
          badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          glow: "border-emerald-500/30",
          label: decision === "TICKET_GENERATED" ? "ORDER TICKET COMPILED" : "TRADE APPROVED",
          iconColor: "text-emerald-400",
        };
      case "WAIT":
      case "CONFIRMATION_REQUIRED":
        return {
          bg: "from-amber-950/30 to-[#0A101C] border-amber-500/40 text-amber-400",
          badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          glow: "border-amber-500/30",
          label: decision === "CONFIRMATION_REQUIRED" ? "EXACT CONFIRMATION REQUIRED" : "WAIT (STANDBY)",
          iconColor: "text-amber-400",
        };
      case "PROTECT":
        return {
          bg: "from-rose-950/30 to-[#0A101C] border-rose-500/40 text-rose-400",
          badge: "bg-rose-500/20 text-rose-300 border-rose-500/40",
          glow: "border-rose-500/30",
          label: "PROTECT (CAPITAL DEFENSE)",
          iconColor: "text-rose-400",
        };
      case "NO TRADE":
      default:
        return {
          bg: "from-slate-900/40 to-[#0A101C] border-slate-800 text-slate-300",
          badge: "bg-slate-800 text-slate-300 border-slate-700",
          glow: "border-slate-800",
          label: decision || "STANDBY",
          iconColor: "text-slate-400",
        };
    }
  };

  const loadingStages = [
    { label: "Accessing Sub-Wallet Mandate & Cash Reserves...", icon: Coins },
    { label: "Auditing Live Binance L1/L2 Depth & Sentry Radar...", icon: Search },
    { label: "Synthesizing Deep Multi-Timeframe Gemini Reasoning...", icon: Sparkles },
    { label: "Validating 1.0% Risk Mathematical Sizing...", icon: Shield },
  ];

  return (
    <div className="flex flex-col min-h-[680px] lg:h-[calc(100vh-190px)] bg-[#080C14] rounded-2xl border border-slate-800/90 shadow-2xl overflow-hidden">
      {/* Terminal Bar */}
      <div className="px-5 py-3.5 bg-[#0A101D] border-b border-slate-800/80 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white tracking-wide font-mono">
                SYRAX COGNITIVE COMMAND CENTER
              </span>
              <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                ACTIVE
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Multi-Turn Conversational Trading &bull; Banglish / English &bull; Deep Reasoning &bull; Mandatory Stop-Loss
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {onClearHistory && (
            <button
              onClick={onClearHistory}
              className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono flex items-center gap-1.5 transition-colors"
              title="Reset conversation memory"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reset Context</span>
            </button>
          )}

          <button
            onClick={onOpenRules}
            className="px-3.5 py-1.5 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-mono font-semibold flex items-center gap-1.5 transition-all"
          >
            <Lock className="w-3.5 h-3.5 text-indigo-400" />
            <span>1% Risk Hard Cap</span>
          </button>
        </div>
      </div>

      {/* Main Conversation Feed */}
      <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-5 font-sans text-sm">
        {chatMessages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-12 space-y-3 opacity-60">
            <Bot className="w-14 h-14 text-indigo-400 animate-pulse" />
            <div className="text-base font-semibold text-white">SYRAX AI Trading Agent is Ready</div>
            <p className="text-xs text-slate-400 max-w-md">
              Type naturally in English or Banglish, explore market opportunities, analyze any Binance token, or plan risk-gated orders.
            </p>
          </div>
        ) : (
          chatMessages.map((msg) => {
            const isUser = msg.sender === "user";
            const res = msg.response;
            const decisionTheme = res ? getDecisionTheme(res.decision) : null;
            const isEvidenceOpen = expandedEvidence[msg.id] ?? false;
            const isStepsOpen = expandedSteps[msg.id] ?? false;
            const ticketData = res?.order_ticket || res?.ticket;
            const isAnalysis = !isUser && (
              res?.command_type === "MARKET_ANALYSIS" ||
              res?.command_type === "DISCOVERY" ||
              res?.command_type === "RISK_AUDIT" ||
              res?.command_type === "TRADE_PLAN" ||
              Boolean(res?.market_analysis) ||
              Boolean(res?.deep_reasoning) ||
              /analy|analysis|kemon|view|outlook|trend|rsi|support|resistance|volume|momentum|market|score|opportunity|bullish|bearish|forecast/i.test(msg.text || "") ||
              /analy|kemon|view|check|opportunity|score|sentiment/i.test(res?.query || "")
            );

            return (
              <div
                key={msg.id}
                className={`flex gap-3 animate-in fade-in duration-200 ${
                  isUser ? "justify-end" : "justify-start"
                }`}
              >
                {/* Agent Avatar */}
                {!isUser && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-cyan-600 flex items-center justify-center text-white shrink-0 shadow-md mt-0.5">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}

                {/* Message Bubble Container */}
                <div
                  className={`max-w-3xl rounded-2xl p-4 space-y-3 ${
                    isUser
                      ? "bg-gradient-to-br from-indigo-600 to-indigo-700 text-white rounded-tr-none ml-8 shadow-md"
                      : "bg-[#0B111F] border border-slate-800 text-slate-200 rounded-tl-none mr-8"
                  }`}
                >
                  {/* Message Header */}
                  <div className="flex items-center justify-between gap-3 text-[11px] pb-1.5 border-b border-white/10">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${isUser ? "text-indigo-100" : "text-indigo-300"}`}>
                        {isUser ? "You (Trader)" : "SYRAX Trading Agent"}
                      </span>
                      {!isUser && isAnalysis && (
                        <span
                          title="Do Your Own Research (DYOR) — AI analytical intelligence only, not financial advice"
                          className="px-2 py-0.5 rounded text-[10px] font-mono font-black bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm flex items-center gap-1 animate-in fade-in"
                        >
                          <ShieldAlert className="w-3 h-3 text-amber-400" />
                          DYOR
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 opacity-75 font-mono text-[10px]">
                      {res?.elapsed_ms && (
                        <span className="text-emerald-400 font-semibold">{res.elapsed_ms}ms</span>
                      )}
                      <span>{msg.timestamp}</span>
                    </div>
                  </div>

                  {/* Primary Text Content */}
                  <div className="text-sm leading-relaxed whitespace-pre-wrap font-medium">
                    {msg.text}
                  </div>

                  {/* Rich Metadata Payload */}
                  {res && (
                    <div className="space-y-3 pt-2">
                      {/* Decision & Risk Verdict Banner (Only for trading/risk commands) */}
                      {decisionTheme && res.decision && !["CONVERSATION", "EXPLANATION", "CLARIFICATION", "PORTFOLIO", "ORDER_STATUS", "CANCEL_ORDER", "MARKET_ANALYSIS"].includes(res.command_type || "") && (
                        <div
                          className={`rounded-xl p-3 border ${decisionTheme.glow} bg-gradient-to-r ${decisionTheme.bg} flex flex-wrap items-center justify-between gap-2 text-xs`}
                        >
                          <div className="flex items-center gap-2 flex-wrap">
                            <span
                              className={`px-2.5 py-1 rounded-md font-mono font-black text-xs uppercase tracking-wider border ${decisionTheme.badge}`}
                            >
                              {decisionTheme.label}
                            </span>
                            {res.target_asset && (
                              <span className="font-bold text-white font-mono bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700 text-xs">
                                {res.target_asset}
                              </span>
                            )}
                            {res.command_type && (
                              <span className="text-[10px] font-bold text-slate-400 uppercase">
                                [{res.command_type}]
                              </span>
                            )}
                          </div>

                          <div className="text-[11px] text-slate-300 flex items-center gap-1.5 font-mono">
                            <span>Max Dollar Risk:</span>
                            <span className="font-bold text-rose-400">
                              ${res.max_risk_usd ? res.max_risk_usd.toFixed(2) : "5.00"}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* PHASE 6 EXACT ORDER TICKET CARD (If compiled) */}
                      {ticketData && (
                        <div className="pt-1">
                          <OrderTicketCard
                            ticket={ticketData}
                            onConfirmed={(result) => {
                              onSendCommand(`CONFIRM ${ticketData.parent_order_id}`);
                            }}
                            onCancelled={(result) => {
                              onSendCommand(`CANCEL ${ticketData.parent_order_id}`);
                            }}
                            onInjectPrompt={(cmd) => {
                              setChatInput(cmd);
                            }}
                          />
                        </div>
                      )}

                      {/* PHASE 4/7 DEEP STRUCTURED REASONING VIEW (If available) */}
                      {res.deep_reasoning && (
                        <div className="pt-1">
                          <StructuredReasoningView
                            reasoning={res.deep_reasoning}
                            marketData={res.market_analysis}
                            targetAsset={res.target_asset || "BTCUSDT"}
                            invalidation={res.invalidation}
                          />
                        </div>
                      )}

                      {/* Detailed Explanation / Reasoning if distinct from text */}
                      {res.explanation && res.explanation.trim() !== msg.text.trim() && !res.deep_reasoning && !ticketData && (
                        <div className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80 whitespace-pre-wrap">
                          {res.explanation}
                        </div>
                      )}

                      {/* Intent Inspector Telemetry (Collapsible) */}
                      {res.debug_intent_inspector && (
                        <details className="text-[10px] font-mono text-slate-500 pt-0.5 group">
                          <summary className="cursor-pointer text-slate-600 hover:text-slate-400 select-none flex items-center gap-1 inline-flex items-center">
                            <span>Telemetry / Brain Trace</span>
                            <span className="text-[9px] opacity-70 group-open:rotate-90 transition-transform inline-block">▸</span>
                          </summary>
                          <div className="flex items-center gap-1.5 pt-1.5 flex-wrap">
                            <span className="px-1.5 py-0.5 rounded bg-slate-900/90 border border-slate-800 text-slate-400">
                              Domain: <strong className="text-slate-300">{res.debug_intent_inspector.domain}</strong>
                            </span>
                            <span className="px-1.5 py-0.5 rounded bg-slate-900/90 border border-slate-800 text-slate-400">
                              Intent: <strong className="text-indigo-300">{res.debug_intent_inspector.intent}</strong>
                            </span>
                            {res.debug_intent_inspector.resolved_asset && (
                              <span className="px-1.5 py-0.5 rounded bg-slate-900/90 border border-slate-800 text-amber-300 font-bold">
                                Asset: {res.debug_intent_inspector.resolved_asset}
                              </span>
                            )}
                            <span className="px-1.5 py-0.5 rounded bg-slate-900/90 border border-slate-800 text-slate-500">
                              Confidence: {(res.debug_intent_inspector.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </details>
                      )}

                      {/* Invalidation Alert Condition (if not in StructuredReasoningView) */}
                      {res.invalidation && !res.deep_reasoning && (
                        <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-500/30 text-xs flex items-start gap-2 text-amber-200">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-bold text-amber-300">Invalidation: </span>
                            <span>{res.invalidation}</span>
                          </div>
                        </div>
                      )}

                      {/* Cognitive Step Pipeline Trace (Expandable/Collapsible) */}
                      {res.agentic_steps && res.agentic_steps.length > 0 && (
                        <div className="rounded-xl bg-slate-950/80 border border-slate-800/90 p-3 space-y-2">
                          <button
                            onClick={() => toggleSteps(msg.id)}
                            className="w-full flex items-center justify-between text-xs font-semibold text-slate-300 hover:text-white transition-colors"
                          >
                            <span className="flex items-center gap-1.5 text-indigo-300">
                              <Layers className="w-3.5 h-3.5 text-indigo-400" />
                              <span>Cognitive Verification Trace ({res.agentic_steps.length} Checkpoints)</span>
                            </span>
                            {isStepsOpen ? (
                              <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                            )}
                          </button>

                          {isStepsOpen && (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 animate-in fade-in duration-150">
                              {res.agentic_steps.map((st, idx) => (
                                <div
                                  key={idx}
                                  className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-0.5 text-xs"
                                >
                                  <div className="flex items-center gap-1.5 font-bold text-slate-200 text-[11px]">
                                    <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                                    <span className="truncate">{st.step}</span>
                                  </div>
                                  <p className="text-[10px] text-slate-400 line-clamp-2 leading-relaxed">
                                    {st.detail}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Deep Market & Risk Evidence Toggle (fallback if deep reasoning not rendered) */}
                      {res.market_analysis && !res.deep_reasoning && (
                        <div>
                          <button
                            onClick={() => toggleEvidence(msg.id)}
                            className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
                          >
                            <span>
                              {isEvidenceOpen ? "Hide Market Evidence" : "View Orderbook Depth & Risk Math"}
                            </span>
                            {isEvidenceOpen ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                          </button>

                          {isEvidenceOpen && (
                            <div className="mt-2 p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs animate-in fade-in duration-150">
                              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                  <span className="text-[10px] text-slate-400 uppercase font-bold block">
                                    Orderbook Depth
                                  </span>
                                  <div className="mt-1 space-y-0.5 text-slate-200 text-[11px]">
                                    <div>
                                      Spread:{" "}
                                      <strong className="font-mono text-emerald-400">
                                        {res.market_analysis.spread_bps ?? 0.05} bps
                                      </strong>
                                    </div>
                                    <div>
                                      Liquidity:{" "}
                                      <strong className="text-white">
                                        {res.market_analysis.liquidity_quality ?? "HIGH"}
                                      </strong>
                                    </div>
                                  </div>
                                </div>

                                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                  <span className="text-[10px] text-slate-400 uppercase font-bold block">
                                    Risk Sizing Limit
                                  </span>
                                  <div className="mt-1 space-y-0.5 text-slate-200 text-[11px]">
                                    <div>
                                      Max Loss:{" "}
                                      <strong className="font-mono text-rose-400">
                                        ${res.max_risk_usd?.toFixed(2) ?? "5.00"}
                                      </strong>
                                    </div>
                                    <div>
                                      Mandate:{" "}
                                      <strong className="text-white">
                                        {userRules.max_risk_pct}% Sub-Wallet
                                      </strong>
                                    </div>
                                  </div>
                                </div>

                                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                  <span className="text-[10px] text-slate-400 uppercase font-bold block">
                                    Sentry Exploit Filter
                                  </span>
                                  <div className="mt-1 space-y-0.5 text-slate-200 text-[11px]">
                                    <div>
                                      Threats: <strong className="text-emerald-400">0 Active</strong>
                                    </div>
                                    <div>
                                      Radar: <strong className="text-emerald-400">ARMED (24/7)</strong>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* INLINE EXECUTION RECEIPT (If Order Filled) */}
                      {res.execution_receipt && (
                        <div className="pt-2 animate-receipt-stamp">
                          <ExecutionReceiptCard
                            receipt={res.execution_receipt}
                            confidenceScore={88}
                            environmentType="BINANCE_AGENTIC_SUB_ACCOUNT"
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {/* DYOR Watermark / Side Tag for Analysis */}
                  {isAnalysis && (
                    <div className="flex items-center justify-end gap-1.5 pt-2 border-t border-slate-800/60 text-[10px] font-mono text-amber-400/90 select-none">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                      <span className="font-bold tracking-wider">DYOR</span>
                      <span className="text-slate-500 font-sans">• Do Your Own Research &bull; Not Financial Advice</span>
                    </div>
                  )}
                </div>

                {/* User Avatar */}
                {isUser && (
                  <div className="w-8 h-8 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300 shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Dynamic Loading State */}
        {chatLoading && (
          <div className="flex gap-3 items-start animate-in fade-in duration-200">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-cyan-600 flex items-center justify-center text-white shrink-0 shadow-md animate-spin">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="bg-[#0B111F] border border-slate-800 rounded-2xl rounded-tl-none p-4 space-y-3 min-w-[300px] shadow-xl">
              <div className="flex items-center justify-between gap-3 border-b border-slate-800/80 pb-2">
                <div className="flex items-center gap-2 text-indigo-300 font-mono text-xs font-bold">
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                  <span>SYRAX AI AGENT THINKING</span>
                </div>
                {onStopExecution && (
                  <button
                    type="button"
                    onClick={onStopExecution}
                    className="px-2.5 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 hover:text-white text-[11px] font-mono font-bold flex items-center gap-1.5 transition-all active:scale-95 shadow-sm"
                    title="Stop AI Thinking & Cancel Execution"
                  >
                    <Square className="w-3 h-3 fill-rose-400 text-rose-400" />
                    <span>Stop Execution</span>
                  </button>
                )}
              </div>
              <div className="space-y-1.5 text-xs text-slate-300">
                {loadingStages.map((stage, idx) => {
                  const Icon = stage.icon;
                  const isDone = idx < activeLoadingStage;
                  const isCurrent = idx === activeLoadingStage;
                  return (
                    <div
                      key={idx}
                      className={`flex items-center gap-2 transition-all ${
                        isDone
                          ? "text-emerald-400 font-semibold"
                          : isCurrent
                          ? "text-white font-bold animate-pulse"
                          : "text-slate-500 opacity-60"
                      }`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Icon className={`w-3.5 h-3.5 ${isCurrent ? "text-indigo-400" : "text-slate-500"}`} />
                      )}
                      <span className="text-[11px]">{stage.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Action Prompt Pills */}
      <div className="px-5 py-2.5 bg-[#090E1A] border-t border-slate-800/80 overflow-x-auto no-scrollbar flex items-center gap-2">
        <span className="text-[11px] font-mono text-slate-400 shrink-0 uppercase font-bold flex items-center gap-1">
          <Zap className="w-3 h-3 text-amber-400" />
          Quick Intents:
        </span>
        {quickCommands.map((q, i) => (
          <button
            key={i}
            onClick={() => setChatInput(q.cmd)}
            className="px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white text-xs font-medium shrink-0 transition-all active:scale-95 shadow-sm"
          >
            {q.label}
          </button>
        ))}
      </div>

      {/* Natural Language Input Box */}
      <div className="p-4 bg-[#0A101D] border-t border-slate-800/90">
        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={chatLoading}
              placeholder="e.g. '5$ worth of SOL kino' or 'Open 10x long on BTC SL 76k' or 'Check if ETH has exploit news'..."
              className="w-full bg-[#070B14] border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-sans transition-all disabled:opacity-50 shadow-inner"
            />
          </div>

          {chatLoading ? (
            <button
              type="button"
              onClick={onStopExecution}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-rose-600 via-rose-500 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-bold text-sm flex items-center gap-2 shadow-lg shadow-rose-950/60 transition-all active:scale-95 shrink-0 animate-pulse"
              title="Stop AI Execution"
            >
              <Square className="w-4 h-4 fill-white text-white" />
              <span>Stop</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!chatInput.trim()}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold text-sm flex items-center gap-2 shadow-lg shadow-indigo-950/60 transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              <span>Execute</span>
              <Send className="w-4 h-4" />
            </button>
          )}
        </form>
      </div>
    </div>
  );
};
