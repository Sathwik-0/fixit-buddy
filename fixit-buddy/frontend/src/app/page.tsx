"use client";
import { useState, useRef, useEffect } from "react";
import { searchDevices, getScore, getParts, uploadManual, askRag } from "@/lib/api";
import { Wrench, Search, Upload, MessageCircle, ChevronRight, CheckCircle, AlertTriangle } from "lucide-react";

type Tab = "score" | "chat" | "parts";
type Message = { role: "user" | "bot"; text: string };

const GRADE_COLORS: Record<string, string> = {
  A: "bg-emerald-100 text-emerald-800",
  B: "bg-green-100 text-green-800",
  C: "bg-yellow-100 text-yellow-800",
  D: "bg-orange-100 text-orange-800",
  E: "bg-red-100 text-red-800",
};

export default function Home() {
  const [tab, setTab] = useState<Tab>("score");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [device, setDevice] = useState<any>(null);
  const [parts, setParts] = useState<any[]>([]);
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", text: "👋 Hi! I'm FixIt Buddy. Search for your device above, then ask me anything about repairing it — even if you've never opened a phone before!" }
  ]);
  const [input, setInput] = useState("");
  const [sessionId] = useState(() => Math.random().toString(36).slice(2));
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [hasManual, setHasManual] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    const res = await searchDevices(query);
    setResults(res);
  };

  const selectDevice = async (d: any) => {
    setResults([]);
    setQuery(d.model);
    const [score, partList] = await Promise.all([getScore(d.id), getParts(d.id)]);
    setDevice({ ...d, ...score });
    setParts(partList);
    setMessages(prev => [...prev, {
      role: "bot",
      text: `Great choice! I found the **${score.model}** — it has a repairability grade of **${score.grade}** (${score.score}/10). ${score.note} What would you like to fix?`
    }]);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMessages(prev => [...prev, { role: "user", text: `📎 Uploaded: ${file.name}` }]);
    try {
      await uploadManual(sessionId, file);
      setHasManual(true);
      setMessages(prev => [...prev, {
        role: "bot",
        text: `✅ Manual uploaded! I've read through **${file.name}** and I'm ready to guide you step by step. What do you need help with?`
      }]);
    } catch {
      setMessages(prev => [...prev, { role: "bot", text: "⚠️ Couldn't read that PDF. Try a different file." }]);
    }
    setUploading(false);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await askRag(sessionId, q, device?.model || "unknown device");
      setMessages(prev => [...prev, { role: "bot", text: res.answer }]);
    } catch {
      setMessages(prev => [...prev, { role: "bot", text: "⚠️ Something went wrong. Is the backend running?" }]);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <div className="w-9 h-9 bg-emerald-100 rounded-lg flex items-center justify-center">
          <Wrench className="w-5 h-5 text-emerald-700" />
        </div>
        <div>
          <div className="font-semibold text-gray-900">FixIt Buddy</div>
          <div className="text-xs text-gray-500">EU Right-to-Repair Navigator</div>
        </div>
        {device && (
          <span className={`ml-auto text-xs font-semibold px-3 py-1 rounded-full ${GRADE_COLORS[device.grade]}`}>
            {device.model} · Grade {device.grade}
          </span>
        )}
      </header>

      <div className="max-w-2xl mx-auto p-4 flex flex-col gap-4">

        {/* Device Search */}
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex gap-2">
            <input
              className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
              placeholder="Search device e.g. iPhone 15, Fairphone..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSearch()}
            />
            <button onClick={handleSearch}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm flex items-center gap-1 transition-colors">
              <Search className="w-4 h-4" /> Search
            </button>
          </div>
          {results.length > 0 && (
            <div className="mt-2 border border-gray-100 rounded-lg overflow-hidden">
              {results.map(r => (
                <button key={r.id} onClick={() => selectDevice(r)}
                  className="w-full flex items-center justify-between px-3 py-2 hover:bg-gray-50 text-sm border-b border-gray-100 last:border-0 transition-colors">
                  <span>{r.brand} {r.model}</span>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${GRADE_COLORS[r.grade]}`}>
                      Grade {r.grade}
                    </span>
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-xl">
          {(["chat","score","parts"] as Tab[]).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-all ${
                tab === t ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"}`}>
              {t === "chat" ? "💬 AI Chat" : t === "score" ? "⭐ Score" : "🔩 Parts"}
            </button>
          ))}
        </div>

        {/* Chat Tab */}
        {tab === "chat" && (
          <div className="bg-white rounded-xl border border-gray-200 flex flex-col" style={{height:"420px"}}>
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-xs lg:max-w-sm px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-emerald-600 text-white rounded-br-sm"
                      : "bg-gray-100 text-gray-800 rounded-bl-sm"}`}>
                    {m.text.replace(/\*\*(.*?)\*\*/g, "$1")}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm">
                    <div className="flex gap-1">
                      {[0,1,2].map(i => <div key={i} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay:`${i*0.15}s`}}/>)}
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef}/>
            </div>
            {/* Upload bar */}
            <div className="border-t border-gray-100 px-3 py-2 flex items-center gap-2">
              <button onClick={() => fileRef.current?.click()}
                className={`p-2 rounded-lg transition-colors ${hasManual ? "text-emerald-600 bg-emerald-50" : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"}`}
                title="Upload repair manual PDF">
                <Upload className="w-4 h-4" />
              </button>
              <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload}/>
              {uploading && <span className="text-xs text-gray-400">Reading manual...</span>}
              {hasManual && <span className="text-xs text-emerald-600">✓ Manual loaded</span>}
            </div>
            {/* Input */}
            <div className="border-t border-gray-100 p-3 flex gap-2">
              <input
                className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
                placeholder="Ask anything about your repair..."
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && sendMessage()}
              />
              <button onClick={sendMessage} disabled={loading}
                className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-200 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                Send
              </button>
            </div>
          </div>
        )}

        {/* Score Tab */}
        {tab === "score" && device && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="font-semibold text-gray-900">{device.model}</div>
                <div className="text-sm text-gray-500">MSRP €{device.msrp} · Max part price €{device.price_cap_30pct}</div>
              </div>
              <span className={`text-2xl font-bold px-4 py-2 rounded-xl ${GRADE_COLORS[device.grade]}`}>
                {device.grade}
              </span>
            </div>
            <div className="mb-1 flex justify-between text-xs text-gray-400">
              <span>Hard to repair</span><span>{device.score}/10</span><span>Excellent</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden mb-4">
              <div className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                style={{width:`${(device.score/10)*100}%`}}/>
            </div>
            <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">{device.note}</p>
          </div>
        )}
        {tab === "score" && !device && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400 text-sm">
            Search for a device above to see its repairability score
          </div>
        )}

        {/* Parts Tab */}
        {tab === "parts" && parts.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
            {parts.map((p, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3">
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{p.name}</div>
                  <div className="text-xs text-gray-400">{p.part_number} · {p.savings_vs_new}</div>
                </div>
                <div className="text-sm font-medium">€{p.oem_price_eur}</div>
                {p.eu_compliant
                  ? <CheckCircle className="w-5 h-5 text-emerald-500" title="EU compliant"/>
                  : <AlertTriangle className="w-5 h-5 text-red-400" title="Exceeds 30% cap"/>}
              </div>
            ))}
            <div className="px-4 py-2 text-xs text-gray-400 bg-gray-50 rounded-b-xl">
              ✓ = within EU 30% price cap · ⚠ = exceeds cap (may be contested under R2R Directive)
            </div>
          </div>
        )}
        {tab === "parts" && parts.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400 text-sm">
            Search for a device above to see spare parts
          </div>
        )}
      </div>
    </div>
  );
}
