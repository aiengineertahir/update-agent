import { Link2, MessageCircle, Calendar, BookOpen, Settings as SettingsIcon, ShieldCheck, FileText, UserX, ExternalLink, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { key: "connect", label: "Connect", icon: Link2 },
  { key: "inbox", label: "Inbox", icon: MessageCircle },
  { key: "bookings", label: "Bookings", icon: Calendar },
  { key: "knowledge", label: "Knowledge base", icon: BookOpen },
  { key: "settings", label: "Settings", icon: SettingsIcon },
  { key: "privacy", label: "Privacy policy", icon: ShieldCheck, href: "/privacy" },
  { key: "terms", label: "Terms & conditions", icon: FileText, href: "/terms" },
  { key: "deletion", label: "Data deletion", icon: UserX, href: "/data-deletion" },
];

export default function Sidebar({ active, onSelect }) {
  const { user, logout } = useAuth();

  return (
    <div className="w-60 flex-shrink-0 bg-brand text-white flex flex-col h-screen sticky top-0">
      <div className="px-5 py-4 font-display text-lg font-semibold tracking-tight border-b border-white/10 flex items-center gap-3">
        <img src="/logo.png" alt="AI Assistant" className="w-8 h-8 rounded-lg object-contain bg-white p-0.5 shadow-sm" />
        <div>
          <div className="leading-none text-base">RAVISN</div>
          <div className="text-[10px] text-white/50 font-sans tracking-normal mt-0.5">AI ASSISTANT</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ key, label, icon: Icon, href }) => {
          if (href) {
            return (
              <a
                key={key}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-white/60 hover:text-white hover:bg-white/5 transition"
              >
                <div className="flex items-center gap-3">
                  <Icon size={18} strokeWidth={1.75} />
                  {label}
                </div>
                <ExternalLink size={14} className="opacity-40" />
              </a>
            );
          }
          return (
            <button
              key={key}
              onClick={() => onSelect(key)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
                active === key
                  ? "bg-white/10 text-white font-medium"
                  : "text-white/60 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon size={18} strokeWidth={1.75} />
              {label}
            </button>
          );
        })}
      </nav>

      <div className="px-3 py-4 border-t border-white/10">
        <div className="px-3 pb-2 text-xs text-white/40 truncate">{user?.tenant?.name}</div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/60 hover:text-white hover:bg-white/5 transition"
        >
          <LogOut size={18} strokeWidth={1.75} />
          Log out
        </button>
      </div>
    </div>
  );
}
