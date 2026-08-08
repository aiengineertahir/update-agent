import { useEffect, useState } from "react";
import { api } from "../lib/api";

const TABS = [
  { key: "whatsapp", label: "Whatsapp" },
  { key: "instagram", label: "Instagram" },
  { key: "facebook", label: "Facebook" },
];

export default function Inbox() {
  const [tab, setTab] = useState("whatsapp");
  const [conversations, setConversations] = useState([]);
  const [selected, setSelected] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setSelected(null);
    setMessages([]);
    api
      .listConversations(tab)
      .then((data) => {
        setConversations(data);
        setSelected(data.length > 0 ? data[0].id : null);
      })
      .finally(() => setLoading(false));
  }, [tab]);

  useEffect(() => {
    if (!selected) return;
    api.listMessages(selected).then(setMessages);
  }, [selected]);

  const activeConvo = conversations.find((c) => c.id === selected);

  return (
    <div className="flex flex-col h-screen">
      <div className="flex border-b border-line px-2 flex-shrink-0">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-3 text-sm border-b-2 transition ${
              tab === t.key
                ? "border-ink text-ink font-medium"
                : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="w-64 flex-shrink-0 border-r border-line overflow-y-auto">
          {loading ? (
            <p className="p-4 text-sm text-ink-muted">Loading…</p>
          ) : conversations.length === 0 ? (
            <p className="p-4 text-sm text-ink-muted">
              No conversations yet. Once this channel is connected and a customer
              messages you, it'll show up here.
            </p>
          ) : (
            conversations.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelected(c.id)}
                className={`w-full text-left px-4 py-3 border-b border-line transition ${
                  selected === c.id ? "bg-accent-soft" : "hover:bg-bg"
                }`}
              >
                <p className="text-sm font-medium truncate">
                  {c.contact_name || c.contact_external_id}
                </p>
                <p className="text-xs text-ink-muted truncate">{c.contact_external_id}</p>
              </button>
            ))
          )}
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          {activeConvo ? (
            <>
              <div className="px-5 py-3 border-b border-line flex-shrink-0">
                <p className="text-sm font-medium">
                  {activeConvo.contact_name || activeConvo.contact_external_id}
                </p>
              </div>
              <div className="flex-1 overflow-y-auto p-5 space-y-3">
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={`max-w-md px-3.5 py-2 rounded-xl text-sm ${
                      m.direction === "outbound" ? "ml-auto bg-accent text-white" : "bg-bg"
                    }`}
                  >
                    {m.body}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-ink-muted text-sm">
              Select a conversation
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
