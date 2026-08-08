import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { api } from "../lib/api";

export default function KnowledgeBase() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    load();
  }, []);

  async function load() {
    setLoading(true);
    try {
      const data = await api.listKnowledge();
      setEntries(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.addKnowledge({ question, answer });
      setQuestion("");
      setAnswer("");
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Are you sure you want to delete this knowledge entry?")) return;
    try {
      await api.deleteKnowledge(id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-xl font-semibold">Knowledge base</h1>
          <p className="text-ink-muted text-sm mt-1">
            The agent answers customers using only what's here.
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-2 rounded-lg bg-accent text-white text-sm font-medium px-4 py-2.5 hover:opacity-90 transition"
        >
          <Plus size={16} />
          Add entry
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="mb-6 rounded-xl border border-line bg-surface p-5 space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1.5">Question</label>
            <input
              required
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition"
              placeholder="What are your clinic hours?"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Answer</label>
            <textarea
              required
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition resize-none"
              placeholder="We're open Monday to Saturday, 10am to 8pm."
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-accent text-white text-sm font-medium px-4 py-2 hover:opacity-90 transition disabled:opacity-60"
            >
              {saving ? "Saving…" : "Save"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg text-sm font-medium px-4 py-2 text-ink-muted hover:bg-bg transition"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {loading ? (
        <p className="text-ink-muted text-sm">Loading…</p>
      ) : entries.length === 0 ? (
        <div className="text-center py-16 text-ink-muted">
          <p>No entries yet. Add the questions your customers ask most.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {entries.map((entry) => (
            <div key={entry.id} className="rounded-xl border border-line bg-surface p-4 flex items-start justify-between gap-4">
              <div className="flex-1">
                <p className="font-medium text-sm">{entry.question}</p>
                <p className="text-ink-muted text-sm mt-1 whitespace-pre-wrap">{entry.answer}</p>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(entry.id)}
                className="text-xs text-red-600 font-medium hover:underline border border-line px-2.5 py-1 rounded-lg hover:bg-red-50 transition flex items-center gap-1 shrink-0"
              >
                <Trash2 size={14} />
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
