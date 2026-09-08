"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Shield,
  Radio,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Key,
  Layers,
  Activity,
  RefreshCw,
  Power,
  Lock,
  Cpu,
  ChevronRight,
  Sparkles,
  Server,
  Globe
} from "lucide-react";
import { BinanceMCPStatus } from "@/types";
import { api } from "@/lib/api";

interface BinanceMcpModalProps {
  isOpen: boolean;
  onClose: () => void;
  mcpStatus: BinanceMCPStatus | null;
  onRefreshStatus: () => void;
}

export const BinanceMcpModal: React.FC<BinanceMcpModalProps> = ({
  isOpen,
  onClose,
  mcpStatus,
  onRefreshStatus,
}) => {
  const [activeTab, setActiveTab] = useState<"MCP" | "API_KEYS">("MCP");
  
  // MCP / Passkey states
  const [authToken, setAuthToken] = useState("");
  const [subAccountId, setSubAccountId] = useState("agentic-sub-01");
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);

  // Standard API Keys state
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [network, setNetwork] = useState<"testnet" | "mainnet">("testnet");
  const [apiStatus, setApiStatus] = useState<any>(null);

  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      api.getBinanceStatus().then((res) => {
        if (res) setApiStatus(res);
      });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isMcpConnected = mcpStatus?.is_connected ?? false;
  const isApiConnected = apiStatus?.connected ?? false;
  const isAnyConnected = isMcpConnected || isApiConnected;

  const handleBrowserOAuth = async () => {
    setOauthLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const data = await api.initiateBinanceOAuth(subAccountId);
      if (!data?.authorization_url) {
        setActionError("Could not initiate Binance OAuth authorization URL.");
        setOauthLoading(false);
        return;
      }

      // Open Binance auth popup
      window.open(data.authorization_url, "BinanceOAuth", "width=620,height=740,scrollbars=yes,status=1");

      // Listen for message
      const messageListener = (evt: MessageEvent) => {
        if (evt.data?.type === "BINANCE_MCP_AUTH_SUCCESS") {
          setActionSuccess("🎉 Binance Agent OS authorization verified successfully via Passkey/SSO!");
          onRefreshStatus();
          setOauthLoading(false);
          window.removeEventListener("message", messageListener);
        }
      };
      window.addEventListener("message", messageListener);

      // Polling fallback
      const interval = setInterval(async () => {
        const stat = await api.getBinanceMcpStatus();
        if (stat?.is_connected) {
          setActionSuccess("🎉 Connected to live Binance Agentic Sub-Account!");
          onRefreshStatus();
          clearInterval(interval);
          setOauthLoading(false);
        }
      }, 2500);

      setTimeout(() => {
        clearInterval(interval);
        setOauthLoading(false);
      }, 60000);
    } catch (err: any) {
      setActionError(err?.message || "Failed to initiate browser OAuth.");
      setOauthLoading(false);
    }
  };

  const handleConnectMcp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authToken.trim()) {
      setActionError("Please enter your Binance Agentic Sub-Account authorization token.");
      return;
    }

    setLoading(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const res = await api.connectBinanceMcp({
        auth_token: authToken.trim(),
        sub_account_id: subAccountId.trim() || "default-agentic-sub",
        endpoint_url: "https://agent.binance.com/mcp/agentic",
      });

      if (res.is_connected) {
        setActionSuccess(`Successfully connected to Binance Agent OS MCP! Sub-account: ${res.sub_account_id}`);
        setAuthToken("");
        onRefreshStatus();
      } else {
        setActionError(res.error_message || "Connection failed. Please verify your token and network permissions.");
      }
    } catch (err: any) {
      setActionError(err?.message || "Network error connecting to Binance MCP.");
    } finally {
      setLoading(false);
    }
  };

  const handleConnectApiKeys = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim() || !apiSecret.trim()) {
      setActionError("Please enter both Binance API Key and API Secret.");
      return;
    }

    setLoading(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const res = await api.connectBinanceApi({
        api_key: apiKey.trim(),
        api_secret: apiSecret.trim(),
        network,
      });

      setApiStatus(res);
      if (res.connected) {
        setActionSuccess(`🎉 Connected to Binance API (${network.toUpperCase()})! Masked Key: ${res.api_key_masked}`);
        setApiKey("");
        setApiSecret("");
        onRefreshStatus();
      } else {
        setActionError(res.message || "Binance API verification failed. Please check your API key & secret.");
      }
    } catch (err: any) {
      setActionError(err?.message || "Network error verifying Binance API keys.");
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnectMcp = async () => {
    setLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await api.disconnectBinanceMcp();
      setActionSuccess("Disconnected from Binance Agent OS MCP. Live execution switched to sandbox mode.");
      onRefreshStatus();
    } catch (err: any) {
      setActionError("Error disconnecting from MCP.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-[#0F172A] border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0B1120]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-amber-400 to-yellow-300 p-[1.5px] shadow-sm">
              <div className="w-full h-full bg-[#090D16] rounded-[10px] flex items-center justify-center">
                <Cpu className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-wide">
                  Connect Binance Account
                </h3>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                    isAnyConnected
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-slate-800 border-slate-700 text-slate-400"
                  }`}
                >
                  {isMcpConnected ? "LIVE MCP CONNECTED" : isApiConnected ? "API KEYS CONNECTED" : "OFFLINE / SANDBOX"}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Choose between Official Agent OS MCP Passkey or Direct API Keys
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-6 pt-2">
          <button
            type="button"
            onClick={() => setActiveTab("MCP")}
            className={`pb-3 px-4 font-mono text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
              activeTab === "MCP"
                ? "border-amber-400 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Agent OS MCP / Passkey (Recommended)</span>
            {isMcpConnected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("API_KEYS")}
            className={`pb-3 px-4 font-mono text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
              activeTab === "API_KEYS"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>Direct Binance API Keys</span>
            {isApiConnected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm">
          {/* Status Alert Banner */}
          {actionError && (
            <div className="flex items-start gap-3 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Connection Error</p>
                <p className="opacity-90">{actionError}</p>
              </div>
            </div>
          )}

          {actionSuccess && (
            <div className="flex items-start gap-3 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Success</p>
                <p className="opacity-90">{actionSuccess}</p>
              </div>
            </div>
          )}

          {/* TAB 1: MCP / PASSKEY CONNECTOR */}
          {activeTab === "MCP" && (
            <div className="space-y-6">
              {isMcpConnected ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="font-semibold text-white">Active Binance Agentic Connection</span>
                      </div>
                      <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        {mcpStatus?.latency_ms ? `${mcpStatus.latency_ms}ms Latency` : "Active"}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                      <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-slate-400 block text-[10px] uppercase">Sub-Account ID</span>
                        <span className="text-white font-bold">{mcpStatus?.sub_account_id}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-slate-400 block text-[10px] uppercase">Token Masked</span>
                        <span className="text-amber-300 font-bold">{mcpStatus?.auth_token_masked}</span>
                      </div>
                    </div>

                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-mono mb-1.5">
                        Authorized Agentic Scopes
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {(mcpStatus?.granted_scopes || ["MARKET_DATA", "ACCOUNT_READ", "SPOT_TRADE", "FUTURES_TRADE", "CONVERT"]).map((scope) => (
                          <span
                            key={scope}
                            className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                          >
                            ✓ {scope}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <button
                      type="button"
                      onClick={onRefreshStatus}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Sync Live State
                    </button>
                    <button
                      type="button"
                      onClick={handleDisconnectMcp}
                      disabled={loading}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 text-xs font-semibold transition-colors"
                    >
                      <Power className="w-3.5 h-3.5" />
                      Disconnect Agentic MCP
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* 1-Click Browser Passkey Option */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-amber-400" />
                        <span className="font-bold text-white text-xs uppercase tracking-wider font-mono">
                          Option 1: 1-Click Browser Passkey / SSO
                        </span>
                      </div>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                        Zero Token Copy-Paste
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      Authorizes SYRAX directly with your desktop browser login session on Binance. Opens the official Binance authorization prompt to confirm with your security key, biometric passkey, or 2FA.
                    </p>

                    <button
                      type="button"
                      onClick={handleBrowserOAuth}
                      disabled={oauthLoading}
                      className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-amber-400 via-amber-500 to-yellow-500 hover:from-amber-300 hover:to-yellow-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition-all active:scale-[0.99] disabled:opacity-50"
                    >
                      {oauthLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin text-slate-950" />
                          <span>Waiting for Binance Browser Authorization...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-slate-950" />
                          <span>Authorize with Binance Browser (Passkey / OAuth)</span>
                          <ExternalLink className="w-3.5 h-3.5 text-slate-950 ml-1" />
                        </>
                      )}
                    </button>
                  </div>

                  {/* Manual MCP Token Form */}
                  <div className="space-y-4 pt-1">
                    <div className="flex items-center gap-2">
                      <Key className="w-4 h-4 text-slate-400" />
                      <span className="font-bold text-slate-300 text-xs uppercase tracking-wider font-mono">
                        Option 2: Manual Sub-Account Token
                      </span>
                    </div>

                    <form onSubmit={handleConnectMcp} className="space-y-4">
                      <div>
                        <label className="block text-xs font-mono text-slate-300 mb-1.5 font-semibold">
                          Sub-Account Identifier
                        </label>
                        <input
                          type="text"
                          value={subAccountId}
                          onChange={(e) => setSubAccountId(e.target.value)}
                          placeholder="e.g. agentic-sub-01"
                          className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-white font-mono text-xs focus:outline-none focus:border-amber-400 transition-colors"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-mono text-slate-300 mb-1.5 font-semibold">
                          Binance MCP Authorization Bearer Token
                        </label>
                        <input
                          type="password"
                          value={authToken}
                          onChange={(e) => setAuthToken(e.target.value)}
                          placeholder="ey..."
                          className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-white font-mono text-xs focus:outline-none focus:border-amber-400 transition-colors"
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={loading || !authToken.trim()}
                        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors disabled:opacity-50"
                      >
                        {loading ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span>Verifying Connection...</span>
                          </>
                        ) : (
                          <>
                            <Key className="w-3.5 h-3.5 text-amber-400" />
                            <span>Connect via Manual Token</span>
                          </>
                        )}
                      </button>
                    </form>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: DIRECT BINANCE API KEYS */}
          {activeTab === "API_KEYS" && (
            <div className="space-y-6">
              {isApiConnected && (
                <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="font-semibold text-white">Binance API Key Verified</span>
                    </div>
                    <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 uppercase font-bold">
                      {apiStatus?.network || "TESTNET"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono">
                    <span className="text-slate-400 block text-[10px] uppercase">Masked API Key</span>
                    <span className="text-cyan-300 font-bold">{apiStatus?.api_key_masked}</span>
                  </div>
                </div>
              )}

              <form onSubmit={handleConnectApiKeys} className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5 font-semibold">
                    Network Environment
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setNetwork("testnet")}
                      className={`p-3 rounded-xl border text-left font-mono transition-all ${
                        network === "testnet"
                          ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-300"
                          : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs">Binance Testnet</span>
                        {network === "testnet" && <span className="w-2 h-2 rounded-full bg-cyan-400" />}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1">Safe Sandbox environment</p>
                    </button>

                    <button
                      type="button"
                      onClick={() => setNetwork("mainnet")}
                      className={`p-3 rounded-xl border text-left font-mono transition-all ${
                        network === "mainnet"
                          ? "bg-amber-500/10 border-amber-500/40 text-amber-300"
                          : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs">Binance Mainnet</span>
                        {network === "mainnet" && <span className="w-2 h-2 rounded-full bg-amber-400" />}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1">Live Trading account</p>
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5 font-semibold">
                    Binance API Key
                  </label>
                  <input
                    type="text"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your 64-character Binance API Key"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-white font-mono text-xs focus:outline-none focus:border-cyan-400 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5 font-semibold">
                    Binance API Secret Key
                  </label>
                  <input
                    type="password"
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                    placeholder="Enter your Binance Secret Key"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-white font-mono text-xs focus:outline-none focus:border-cyan-400 transition-colors"
                  />
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-400 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
                    <Shield className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Security &amp; Permissions Advice</span>
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    Enable <strong>Enable Reading</strong> and <strong>Enable Spot &amp; Margin Trading</strong>. Never enable <strong>Enable Withdrawals</strong>.
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={loading || !apiKey.trim() || !apiSecret.trim()}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Verifying API Credentials...</span>
                    </>
                  ) : (
                    <>
                      <Key className="w-3.5 h-3.5" />
                      <span>Connect Binance API Keys</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
