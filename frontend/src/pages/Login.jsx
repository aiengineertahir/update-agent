import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      <div className="hidden md:flex md:w-1/2 bg-brand text-white flex-col justify-between p-12">
        <div className="flex items-center gap-3 font-display text-2xl font-semibold tracking-tight">
          <img src="/logo.png" alt="AI Assistant" className="w-10 h-10 rounded-xl object-contain bg-white p-1 shadow-lg" />
          <span>RAVISN</span>
        </div>
        <div>
          <p className="font-display text-3xl leading-snug max-w-sm">
            One inbox for every customer conversation.
          </p>
          <p className="text-white/60 mt-4 max-w-sm">
            WhatsApp, Instagram and Facebook, answered automatically from your own knowledge base.
          </p>
        </div>
        <div className="text-white/40 text-sm">RAVISN</div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <h1 className="font-display text-2xl font-semibold mb-1">Log in</h1>
          <p className="text-ink-muted mb-8">Welcome back.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition"
                placeholder="you@business.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition"
                placeholder="••••••••"
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-accent text-white font-medium py-2.5 hover:opacity-90 transition disabled:opacity-60"
            >
              {loading ? "Logging in…" : "Log in"}
            </button>
          </form>

          <p className="text-xs text-ink-muted mt-4 flex gap-3 flex-wrap">
            <Link to="/privacy" target="_blank" rel="noopener noreferrer" className="hover:underline">
              Privacy Policy
            </Link>
            <span>•</span>
            <Link to="/terms" target="_blank" rel="noopener noreferrer" className="hover:underline">
              Terms & Conditions
            </Link>
            <span>•</span>
            <Link to="/data-deletion" target="_blank" rel="noopener noreferrer" className="hover:underline">
              Data Deletion
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
