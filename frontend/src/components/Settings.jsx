import { useState, useEffect } from "react";
import { Key, CheckCircle, AlertTriangle, Eye, EyeOff, Save, ShieldCheck, Sparkles } from "lucide-react";
import { api } from "../lib/api";

export default function Settings() {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [status, setStatus] = useState({ configured: false, masked_key: "", provider: "none" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    try {
      setLoading(true);
      const res = await api.getApiKey();
      setStatus(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(e) {
    e.preventDefault();
    if (!apiKey.trim()) return;

    try {
      setSaving(true);
      setMessage(null);
      setError(null);
      const res = await api.saveApiKey(apiKey.trim());
      setMessage(res.message || "API Key saved successfully to .env file!");
      setStatus({ configured: true, masked_key: res.masked_key, provider: res.provider || "Gemini" });
      setApiKey("");
    } catch (err) {
      setError(err.message || "Failed to save API key.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          AI & Agent Settings
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Configure Google Gemini (100% Free) or OpenAI API Key to enable real-time AI responses across all connected channels.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        {/* Status Header */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50 border border-slate-200">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-lg ${status.configured ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
              {status.configured ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
            </div>
            <div>
              <div className="font-semibold text-slate-900 text-sm">
                AI Key Status:{" "}
                {loading ? (
                  <span className="text-slate-400 font-normal">Checking...</span>
                ) : status.configured ? (
                  <span className="text-emerald-600 font-semibold">Active ({status.provider || "Real AI Replies"})</span>
                ) : (
                  <span className="text-amber-600 font-semibold">Mock Mode (Not Configured)</span>
                )}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                {status.configured
                  ? `Active key: ${status.masked_key} (${status.provider})`
                  : "Currently running in mock mode. Add your free Gemini key below for real-time replies."}
              </div>
            </div>
          </div>
          <div className="text-xs font-mono px-3 py-1 bg-white border border-slate-200 rounded-full text-slate-600">
            .env file target
          </div>
        </div>

        {/* Message Banner */}
        {message && (
          <div className="flex items-center gap-2 p-3.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-sm">
            <ShieldCheck size={18} className="text-emerald-600 flex-shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3.5 rounded-lg bg-red-50 text-red-700 border border-red-200 text-sm">
            <AlertTriangle size={18} className="text-red-500 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              API Key (Google Gemini or OpenAI)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Key size={18} />
              </div>
              <input
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Paste Google Gemini Key (Free) or OpenAI Key..."
                className="w-full pl-10 pr-10 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand font-mono"
                required
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
              >
                {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-2 flex flex-col gap-1">
              <span className="flex items-center gap-1">
                <Sparkles size={14} className="text-amber-500 flex-shrink-0" />
                <span>
                  Get a 100% free API key from{" "}
                  <a
                    href="https://console.groq.com/keys"
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand font-medium underline hover:text-brand/80"
                  >
                    Groq Console (Llama-3.3 70B)
                  </a>{" "}
                  or{" "}
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand font-medium underline hover:text-brand/80"
                  >
                    Google AI Studio (Gemini 2.0)
                  </a>.
                </span>
              </span>
            </p>
          </div>

          <button
            type="submit"
            disabled={saving || !apiKey.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand/90 transition disabled:opacity-50"
          >
            <Save size={16} />
            {saving ? "Saving to .env..." : "Save API Key to .env"}
          </button>
        </form>
      </div>
    </div>
  );
}
