import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { api } from "./services/api";
import { BookCover } from "./components/ui/BookCover";
import { ProfileRadar } from "./components/features/profile/ProfileRadar";
import { SearchResultCard } from "./components/features/search/SearchResultCard";
import { RecommendCard } from "./components/features/recs/RecommendCard";
import { SkeletonCard } from "./components/ui/SkeletonCard";
import { LoginPage } from "./components/LoginPage";
import { InfoTooltip } from "./components/ui/InfoTooltip";

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  // ── Theme (initialised first — LoginPage needs it) ──────────────────────────
  const [isDark, setIsDark] = useState(false);
  useEffect(() => { document.documentElement.classList.toggle("dark", isDark); }, [isDark]);

  // ── Session & auth ──────────────────────────────────────────────────────────
  const [sessionId] = useState(() => {
    let id = localStorage.getItem("yomiai_session_id");
    if (!id) { id = "sess_" + Math.random().toString(36).substring(2, 15); localStorage.setItem("yomiai_session_id", id); }
    return id;
  });

  // userId: read from localStorage on mount so returning users skip the gate
  const [userId, setUserId] = useState(() => localStorage.getItem("yomiai_user_id") || null);
  const [isGuest, setIsGuest] = useState(() => (localStorage.getItem("yomiai_user_id") || "").startsWith("guest_"));

  const handleLogin = (uid) => {
    localStorage.setItem("yomiai_user_id", uid);
    // Reset all user-scoped state so previous user's data never bleeds through
    setInteractions([]);
    setRlStep(0);
    setRlMetrics({ loss_history: [], step: 0, arch: "" });
    setProfileStats({ recent_items: [] });
    setTrainPulse(null);
    setRecommendations({ people_also_buy: [], you_might_like: [], combined: [] });
    setNewRecAsins(new Set());
    setSearchResults([]);
    setBlockedIds(new Set());
    prevRecMode.current  = null;
    prevYmlAsins.current = new Set();
    setUserId(uid);
    setIsGuest(uid.startsWith("guest_"));
  };

  const handleLogout = () => {
    localStorage.removeItem("yomiai_user_id");
    setUserId(null);
  };

  // ── Search ──────────────────────────────────────────────────────────────────
  const [query, setQuery]               = useState("");
  const [imageFile, setImageFile]       = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching]   = useState(false);
  const [searchError, setSearchError]   = useState(null);

  // ── Recommendations ─────────────────────────────────────────────────────────
  const [recommendations, setRecommendations] = useState({ people_also_buy: [], you_might_like: [], combined: [] });
  const [isLoadingRecs, setLoadingRecs] = useState(false);
  const [recsError, setRecsError]       = useState(null);
  const [lastRecsRefresh, setLastRecsRefresh] = useState(null);

  // ── RL / profile ────────────────────────────────────────────────────────────
  const [interactions, setInteractions] = useState([]);
  const [rlStep, setRlStep]             = useState(0);
  const [rlMetrics, setRlMetrics]       = useState({ loss_history: [], step: 0, arch: "" });
  const [lastTrained, setLastTrained]   = useState(null);
  const [profileStats, setProfileStats] = useState({ recent_items: [] });
  const [trainPulse, setTrainPulse]     = useState(null);    // D: flashing loss value after a click

  // ── Rec mode + new-badge tracking ───────────────────────────────────────────
  const [recMode, setRecMode]           = useState(null);    // A: "cold_start" | "personalized"
  const [newRecAsins, setNewRecAsins]   = useState(new Set()); // F: ASINs new since last refresh
  const prevRecMode  = useRef(null);
  const prevYmlAsins = useRef(new Set());

  // ── UI state ────────────────────────────────────────────────────────────────
  const [toasts, setToasts]           = useState([]);
  const [activeTab, setActiveTab]     = useState("search");
  const [activeRight, setActiveRight] = useState("profile");
  const [blockedIds, setBlockedIds]    = useState(new Set());
  const [rightPanelOpen, setRightPanelOpen] = useState(true);

  const [showImagePopover, setShowImagePopover] = useState(false);

  const fileRef       = useRef();
  const dropRef       = useRef();
  const imageAreaRef  = useRef();

  useEffect(() => {
    const handler = (e) => {
      if (imageAreaRef.current && !imageAreaRef.current.contains(e.target))
        setShowImagePopover(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // ── Helpers ─────────────────────────────────────────────────────────────────
  const toast = useCallback((msg, type = "info") => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3000);
  }, []);

  const loadProfile = async () => {
    try { const d = await api.profile(userId); if (d) { setProfileStats(d); setInteractions(d.recent_items || []); } } catch (_) {}
  };

  const loadRecs = useCallback(async () => {
    setLoadingRecs(true);
    setRecsError(null);
    try {
      const d = await api.recommend(userId, sessionId);
      const recs = d || { people_also_buy: [], you_might_like: [], combined: [] };
      setRecommendations(recs);

      // A: track mode, fire toast on cold-start → personalised transition
      const mode = d?.mode || null;
      if (mode === "personalized" && prevRecMode.current === "cold_start") {
        toast("DIF-SASRec is now ranking for you", "success");
      }
      prevRecMode.current = mode;
      setRecMode(mode);

      // F: diff both pipelines — mark ASINs that weren't in the previous refresh
      const nextIds = [
        ...(recs.people_also_buy || []),
        ...(recs.you_might_like  || []),
      ].map(b => b.id);
      const prev    = prevYmlAsins.current;
      if (prev.size > 0) {
        const fresh = new Set(nextIds.filter(id => !prev.has(id)));
        if (fresh.size > 0) {
          setNewRecAsins(fresh);
          setTimeout(() => setNewRecAsins(new Set()), 4000);
        }
      }
      prevYmlAsins.current = new Set(nextIds);

      try { const m = await api.rlMetrics(userId); setRlMetrics(m); } catch (_) {}
      setLastRecsRefresh(new Date());
    } catch (_) {
      setRecsError("Could not load recommendations.");
      toast("Backend connection failed: Displaying cached data", "error");
    } finally { setLoadingRecs(false); }
  }, [userId, sessionId, toast]);

  // Single effect — fires on mount and whenever userId/useMock change
  useEffect(() => { loadRecs(); loadProfile(); }, [userId]);

  // ── Search handler ──────────────────────────────────────────────────────────
  const handleSearch = async () => {
    if (!query.trim() && !imageFile) return;
    setIsSearching(true);
    setSearchError(null);
    try {
      let imgB64 = null;
      if (imageFile) imgB64 = await new Promise(res => { const r = new FileReader(); r.onload = () => res(r.result.split(",")[1]); r.readAsDataURL(imageFile); });
      const d = await api.search(query, imgB64, sessionId);
      setSearchResults(d.results || []);
    } catch (_) {
      setSearchError("Search failed. Is the backend running?");
      toast("Backend connection failed: Displaying cached data", "error");
    } finally { setIsSearching(false); }
  };

  // ── Interact handler ────────────────────────────────────────────────────────
  const handleInteract = async (book, action) => {
    if (action === "not_interested") {
      setBlockedIds(prev => new Set([...prev, book.id]));
      setRecommendations(prev => ({
        people_also_buy: prev.people_also_buy.filter(b => b.id !== book.id),
        you_might_like:  prev.you_might_like.filter(b => b.id !== book.id),
        combined:        prev.combined.filter(b => b.id !== book.id),
      }));
      toast(`"${book.title}" hidden from recommendations`, "info");
      try { await api.interact(userId, book.id, action, sessionId); } catch (_) {}
      return;
    }

    setInteractions(p => [{ ...book, action, ts: Date.now() }, ...p]);
    setRlStep(s => s + 1);
    if (action === "click") { toast(`"${book.title}" — profile updated`, "success"); }
    else                    { toast(`Skipped "${book.title}"`, "info"); }
    try {
      const res  = await api.interact(userId, book.id, action, sessionId);
      const loss = res?.sasrec_loss;
      if (loss != null) {
        setRlMetrics(p => ({
          ...p,
          loss_history: [...p.loss_history, loss].slice(-100),
          step: p.step + 1,
        }));
        setTrainPulse(loss);
        setTimeout(() => setTrainPulse(null), 2500);
      } else {
        try { const m = await api.rlMetrics(userId); setRlMetrics(m); } catch (_) {}
      }
      setLastTrained(new Date());
      if ((rlStep + 1) % 3 === 0) setTimeout(loadRecs, 800);
    } catch (_) {}
  };

  const handleImageDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
    if (file?.type.startsWith("image/")) {
      setImageFile(file);
      setShowImagePopover(false);
      const r = new FileReader(); r.onload = () => setImagePreview(r.result); r.readAsDataURL(file);
      toast("Image loaded — CLIP encoder ready", "info");
    }
  };

  const handleAskAI = async (book) => {
    const d = await api.askLLM(book.title, book.author, "Why should I read this? Give a short 2-sentence pitch.");
    return d.response;
  };

  const handleAskAIStream = (book) => {
    return api.askLLMStream(book.title, book.author, "Why should I read this? Give a short 2-sentence pitch.");
  };

  const ctr = interactions.length
    ? (interactions.filter(i => i.action === "click").length / interactions.length * 100).toFixed(1)
    : "—";

  // Pre-compute sparkline points + phase split index once per loss_history change
  const { sparklinePoints, onlineStartIdx } = useMemo(() => {
    const h = rlMetrics.loss_history;
    if (h.length < 2) return { sparklinePoints: null, onlineStartIdx: null };
    const min = Math.min(...h), max = Math.max(...h), range = max - min || 1;
    const pts = h.map((v, i) => `${i},${1 - (v - min) / range}`).join(" ");
    // C: how many points are pretraining vs online
    // rlMetrics.step = number of online gradient steps appended after the checkpoint
    const split = rlMetrics.step > 0 ? h.length - rlMetrics.step : null;
    return { sparklinePoints: pts, onlineStartIdx: split };
  }, [rlMetrics.loss_history, rlMetrics.step]);

  // ── Shared class shorthands ──────────────────────────────────────────────────
  const CARD    = "rounded-xl border border-[#babbbd] dark:border-[#627d9a]/70 bg-white/50 dark:bg-[#fffef7]/5 shadow-sm";
  const DIVIDER = "border-[#babbbd] dark:border-[#627d9a]/60";

  // ─── RENDER ─────────────────────────────────────────────────────────────────

  // Gate: show login screen until a userId is established
  if (!userId) {
    return <LoginPage onLogin={handleLogin} isDark={isDark} onToggleDark={() => setIsDark(d => !d)} />;
  }

  return (
    <div className="h-screen flex flex-col font-sans bg-[#fffef7] dark:bg-[#2e3257] text-[#2e3257] dark:text-[#fffef7] overflow-hidden transition-colors duration-300">

      {/* Toast rack */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2" style={{ maxWidth: 320 }}>
        {toasts.map(t => (
          <div key={t.id} className={`fade-in flex items-start gap-2 px-3 py-2 rounded-xl text-[11px] border shadow-sm
            ${t.type === "success" ? "bg-emerald-50 dark:bg-emerald-900/30 border-emerald-300 dark:border-emerald-700/60 text-emerald-700 dark:text-emerald-300"
            : t.type === "error"   ? "bg-red-50 dark:bg-red-900/30 border-red-300 dark:border-red-700/60 text-red-600 dark:text-red-300"
            : "bg-[#dfc5a4]/20 dark:bg-[#dfc5a4]/10 border-[#dfc5a4] text-[#627d9a] dark:text-[#babbbd]"}`}>
            <span className="flex-1 leading-snug">{t.msg}</span>
            <button
              onClick={() => setToasts(ts => ts.filter(x => x.id !== t.id))}
              className="flex-shrink-0 opacity-40 hover:opacity-100 transition-opacity bg-transparent border-none cursor-pointer p-0 leading-none"
              style={{ fontSize: 11 }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* ── HEADER ──────────────────────────────────────────────────────────── */}
      <header className={`relative z-10 flex-shrink-0 flex flex-col border-b ${DIVIDER} bg-[#fffef7]/90 dark:bg-[#2e3257]/90 backdrop-blur-md`}>
        <div className="flex items-center justify-between px-6 py-3">

          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 bg-[#2e3257] dark:bg-[#dfc5a4] shadow-sm select-none">
              <span className="font-serif font-bold text-[#fffef7] dark:text-[#2e3257]" style={{ fontSize: 20, lineHeight: 1 }}>愛</span>
            </div>
            <div>
              <h1 className="font-serif font-bold tracking-tight leading-none text-[#2e3257] dark:text-[#fffef7]" style={{ fontSize: 18 }}>
                Yomi<span className="text-[#627d9a] dark:text-[#dfc5a4]">愛</span>
              </h1>
              <p className="font-mono text-[#babbbd] dark:text-[#627d9a] mt-0.5 tracking-widest uppercase" style={{ fontSize: 8 }}>
                読み愛 · Multimodal Rec Engine
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-4">

            {/* Logged-in user badge + logout */}
            <div className="flex items-center gap-1">
              <span className={`px-3 py-1.5 rounded-lg text-[12px] font-semibold flex items-center gap-1.5 border
                ${isGuest
                  ? "bg-[#627d9a]/10 border-[#627d9a]/30 text-[#627d9a] dark:text-[#babbbd]"
                  : "bg-[#2e3257]/8 dark:bg-[#fffef7]/8 border-[#2e3257]/20 dark:border-[#fffef7]/20 text-[#2e3257] dark:text-[#fffef7]"}`}
              >
                {userId}
              </span>
              <button
                onClick={handleLogout}
                className="p-1.5 rounded-lg bg-transparent border-none
                           text-[#babbbd] dark:text-[#627d9a]
                           hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-all duration-200"
                title="Log out"
              >
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"
                     strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                  <path d="M6 2H3a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" />
                  <polyline points="10 11 13 8 10 5" />
                  <line x1="13" y1="8" x2="5" y2="8" />
                </svg>
              </button>
            </div>

            {/* Theme */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsDark(d => !d)}
                className={`px-3 py-1.5 rounded-lg text-[12px] border transition-all duration-200
                  hover:bg-[#dfc5a4]/30 hover:border-[#dfc5a4] hover:text-[#2e3257]
                  bg-transparent border-[#babbbd] dark:border-[#627d9a]/70
                  text-[#627d9a] dark:text-[#babbbd]`}
              >
                {isDark ? "Light" : "Dark"}
              </button>
            </div>

            {/* Right panel toggle */}
            <button
              onClick={() => setRightPanelOpen(p => !p)}
              title={rightPanelOpen ? "Collapse profile panel" : "Expand profile panel"}
              className={`p-1.5 rounded-lg border transition-all duration-200
                ${rightPanelOpen
                  ? `border-[#2e3257]/25 dark:border-[#fffef7]/20 bg-[#2e3257]/6 dark:bg-[#fffef7]/6
                     text-[#2e3257] dark:text-[#fffef7]`
                  : `border-[#babbbd] dark:border-[#627d9a]/70
                     text-[#627d9a] dark:text-[#babbbd]
                     hover:border-[#dfc5a4] hover:text-[#2e3257] dark:hover:text-[#fffef7]`}`}
            >
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"
                   strokeLinecap="round" className="w-4 h-4">
                <rect x="1.5" y="1.5" width="13" height="13" rx="2" />
                <line x1="10.5" y1="1.5" x2="10.5" y2="14.5" />
              </svg>
            </button>
          </div>
        </div>

      </header>

      {/* ── MAIN ────────────────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0">

        {/* ── LEFT PANEL — grows to fill remaining space ── */}
        <div className={`flex flex-col flex-1 min-w-0 min-h-0 border-r ${DIVIDER}`}>

          {/* Tab bar */}
          <div className={`flex items-center px-4 py-2 border-b ${DIVIDER}`}>
            <div className="flex rounded-lg p-0.5 gap-0.5
                            bg-[#2e3257]/6 dark:bg-[#fffef7]/6
                            border border-[#2e3257]/10 dark:border-[#fffef7]/10">
              {[["search", "Active Search", "M1"], ["recs", "Recommendations", "M2"]].map(([tab, label, mode]) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-1.5 rounded-md text-[13px] font-medium transition-all duration-200 cursor-pointer border-none
                    ${activeTab === tab
                      ? "bg-[#2e3257] dark:bg-[#fffef7] text-[#fffef7] dark:text-[#2e3257] shadow-sm"
                      : "bg-transparent text-[#627d9a] dark:text-[#babbbd] hover:text-[#2e3257] dark:hover:text-[#fffef7]"}`}
                >
                  {label}
                  <span className="ml-1.5 opacity-50 font-mono" style={{ fontSize: 10 }}>{mode}</span>
                </button>
              ))}
            </div>
          </div>

          {/* ── Search tab ── */}
          {activeTab === "search" ? (
            <div className="flex flex-col flex-1 min-h-0 px-4 pt-4 gap-3">

              {/* Input row */}
              <div className="flex gap-2 flex-shrink-0">
                {/* Text input with inset image button */}
                <div ref={imageAreaRef} className="relative flex-1">
                  <input
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleSearch()}
                    placeholder='"Dark Fantasy with complex magic systems"'
                    className={`w-full pl-4 pr-12 py-3 rounded-xl text-[15px] transition-all duration-200
                                bg-white dark:bg-[#fffef7]/5
                                border ${DIVIDER}
                                text-[#2e3257] dark:text-[#fffef7]
                                placeholder:text-[#babbbd] dark:placeholder:text-[#627d9a]
                                focus:border-[#2e3257] dark:focus:border-[#dfc5a4] focus:outline-none`}
                  />

                  {/* Camera icon button */}
                  <button
                    onClick={() => setShowImagePopover(p => !p)}
                    title={imagePreview ? "Image loaded — click to change" : "Search by image"}
                    className={`absolute right-2.5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg flex items-center justify-center
                                transition-all duration-200 border
                                ${imagePreview
                                  ? "border-[#dfc5a4] bg-[#dfc5a4]/20 hover:bg-[#dfc5a4]/35"
                                  : `border-[#babbbd]/60 dark:border-[#627d9a]/50 bg-transparent
                                     hover:border-[#dfc5a4] hover:bg-[#dfc5a4]/15
                                     ${showImagePopover ? "border-[#2e3257] dark:border-[#dfc5a4] bg-[#2e3257]/8 dark:bg-[#dfc5a4]/10" : ""}`}`}
                  >
                    {imagePreview ? (
                      <img src={imagePreview} className="w-6 h-6 rounded object-cover" alt="" />
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"
                        className="w-4 h-4 text-[#627d9a] dark:text-[#babbbd]">
                        <path fillRule="evenodd" d="M1 8a2 2 0 0 1 2-2h.93a2 2 0 0 0 1.664-.89l.812-1.22A2 2 0 0 1 8.07 3h3.86a2 2 0 0 1 1.664.89l.812 1.22A2 2 0 0 0 16.07 6H17a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8Zm13.5 3a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0ZM10 14a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>

                  {/* Image popover */}
                  {showImagePopover && (
                    <div className="absolute z-30 left-0 right-0 mt-1 p-3 rounded-xl shadow-lg fade-in
                                    bg-[#fffef7] dark:bg-[#2e3257]
                                    border border-[#babbbd] dark:border-[#627d9a]/70"
                      style={{ top: "calc(100% + 4px)" }}
                    >
                      <div
                        ref={dropRef}
                        onClick={() => fileRef.current?.click()}
                        onDrop={handleImageDrop}
                        onDragOver={e => e.preventDefault()}
                        className={`flex items-center gap-3 rounded-xl cursor-pointer transition-all duration-200 border
                                    ${imagePreview
                                      ? "border-[#dfc5a4] bg-[#dfc5a4]/10"
                                      : "border-dashed border-[#babbbd] dark:border-[#627d9a]/60 hover:border-[#dfc5a4] hover:bg-[#dfc5a4]/5"}`}
                        style={{ padding: "10px 14px" }}
                      >
                        {imagePreview ? (
                          <>
                            <img src={imagePreview} className="w-11 h-11 rounded-lg object-cover flex-shrink-0 shadow-sm" alt="query" />
                            <div className="flex-1 min-w-0">
                              <p className="text-[12px] font-medium text-[#2e3257] dark:text-[#fffef7]">Image query loaded</p>
                              <p className="text-[10px] text-[#627d9a] dark:text-[#babbbd]">CLIP will encode this for visual similarity</p>
                            </div>
                            <button
                              onClick={e => { e.stopPropagation(); setImageFile(null); setImagePreview(null); }}
                              className="text-[#babbbd] hover:text-rose-400 transition-colors flex-shrink-0 bg-transparent border-none cursor-pointer p-1"
                              style={{ fontSize: 14 }}
                            >
                              ✕
                            </button>
                          </>
                        ) : (
                          <>
                            <div>
                              <p className="text-[12px] text-[#627d9a] dark:text-[#babbbd]">Drop a cover image here, or click to browse</p>
                              <p className="text-[10px] text-[#babbbd] dark:text-[#627d9a]/70 mt-0.5">CLIP image encoder · visual similarity search</p>
                            </div>
                          </>
                        )}
                      </div>
                      <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleImageDrop} />
                    </div>
                  )}
                </div>

                <button
                  onClick={handleSearch}
                  disabled={isSearching}
                  className={`px-5 py-3 rounded-xl text-[15px] font-semibold flex-shrink-0 transition-all duration-200
                              border border-transparent
                              ${isSearching
                                ? "bg-[#babbbd]/30 text-[#627d9a] cursor-not-allowed"
                                : "bg-[#2e3257] dark:bg-[#fffef7] text-[#fffef7] dark:text-[#2e3257] hover:bg-[#dfc5a4] hover:text-[#2e3257] shadow-sm"}`}
                >
                  {isSearching ? <span className="shimmer">…</span> : "Search"}
                </button>
              </div>

              {/* Encoder legend */}
              <div className="flex items-center gap-4 flex-shrink-0">
                {[["BGE-M3", "#2e3257", "text semantics"], ["CLIP", "#627d9a", "visual features"], ["RRF", "#dfc5a4", "fusion score"]].map(([name, color, desc]) => (
                  <div key={name} className="flex items-center gap-1.5">
                    <div className="rounded-full flex-shrink-0" style={{ width: 7, height: 7, background: color }} />
                    <span className="text-[#627d9a] dark:text-[#babbbd]" style={{ fontSize: 12 }}>
                      <span className="font-medium text-[#2e3257] dark:text-[#fffef7]">{name}</span> · {desc}
                    </span>
                  </div>
                ))}
              </div>

              {/* Results */}
              <div className="flex-1 min-h-0 overflow-y-auto space-y-2 pr-1 pb-6">
                {isSearching ? (
                  [0,1,2,4].map(i => <SkeletonCard key={i} size="md" />)
                ) : searchError ? (
                  <div className={`p-4 rounded-xl border ${DIVIDER} text-center space-y-2`}>
                    <p className="text-[12px] font-medium text-red-500 dark:text-red-400">{searchError}</p>
                    <button
                      onClick={handleSearch}
                      className="text-[11px] px-3 py-1.5 rounded-lg border border-[#babbbd] dark:border-[#627d9a]/70
                                 text-[#627d9a] dark:text-[#babbbd] hover:bg-[#dfc5a4]/20 hover:border-[#dfc5a4] transition-all"
                    >
                      ↺ Retry
                    </button>
                  </div>
                ) : searchResults.length > 0 ? (
                  searchResults.map((book, i) => (
                    <SearchResultCard key={i} book={book} onInteract={handleInteract} onAskAIStream={handleAskAIStream} />
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center h-48 gap-3 text-center">
                    <div>
                      <p className="text-[16px] font-medium text-[#627d9a] dark:text-[#babbbd]">Search for a book to begin</p>
                      <p className="text-[13px] text-[#babbbd] dark:text-[#627d9a]/70 mt-1">BGE-M3 + CLIP · 3M book catalog</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

          ) : (
            /* ── Recs tab ── */
            <div className="flex flex-col flex-1 min-h-0 px-4 pt-4 gap-3">
              <div className="flex items-center justify-between gap-3 flex-shrink-0">
                <div className="flex items-center gap-2.5 flex-wrap min-w-0">
                  <p className="text-[15px] font-medium text-[#2e3257] dark:text-[#fffef7] flex-shrink-0">Personalized For You</p>

                  {/* Consolidated pipeline badge cluster */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="px-2 py-0.5 rounded-full border text-[10px] font-medium
                                     bg-[#627d9a]/10 border-[#627d9a]/35 dark:border-[#627d9a]/50
                                     text-[#627d9a] dark:text-[#babbbd]">
                      Multi-mode
                    </span>
                    <span className="px-2 py-0.5 rounded-full border text-[10px] font-medium
                                     bg-[#2e3257]/8 dark:bg-[#fffef7]/6
                                     border-[#2e3257]/25 dark:border-[#fffef7]/20
                                     text-[#2e3257] dark:text-[#fffef7]">
                      Cleora + DIF-SASRec
                    </span>
                  </div>
                </div>

                <button
                  onClick={loadRecs}
                  disabled={isLoadingRecs}
                  className={`flex-shrink-0 text-[11px] px-3 py-1.5 rounded-lg border transition-all duration-200
                    ${isLoadingRecs
                      ? "border-[#babbbd] dark:border-[#627d9a]/50 text-[#babbbd] cursor-not-allowed"
                      : `border-[#babbbd] dark:border-[#627d9a]/70 text-[#627d9a] dark:text-[#babbbd]
                         hover:bg-[#dfc5a4]/20 hover:border-[#dfc5a4] hover:text-[#2e3257] dark:hover:text-[#fffef7]`}`}
                >
                  {isLoadingRecs ? (
                    <span className="shimmer">Fetching…</span>
                  ) : (
                    <span>
                      ↺ Refresh
                      {lastRecsRefresh && (
                        <span className="ml-1.5 text-[#babbbd] dark:text-[#627d9a] font-normal" style={{ fontSize: 9 }}>
                          {lastRecsRefresh.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      )}
                    </span>
                  )}
                </button>
              </div>

              {/* B: DIF-SASRec input sequence strip */}
              {recMode === "personalized" && (() => {
                const seq = interactions
                  .filter(i => i.action === "click")
                  .slice(0, 8)
                  .reverse();
                if (seq.length < 2) return null;
                return (
                  <div className="shrink-0">
                    <p className="text-[9px] font-mono text-[#627d9a] dark:text-[#babbbd] mb-1 px-0.5 tracking-wide">
                      DIF-SASRec reads →
                    </p>
                    <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide">
                      {seq.map((item, idx) => {
                        const bg = item.cover_color || "#1e1b4b";
                        return (
                          <div key={idx} className="relative shrink-0 flex flex-col items-center gap-0.5" style={{ width: 40 }}>
                            <div
                              className="w-10 h-14 rounded-md flex items-end justify-center overflow-hidden border border-[#babbbd]/40 dark:border-[#627d9a]/30"
                              style={{ background: bg }}
                            >
                              {item.image_url ? (
                                <img src={item.image_url} alt="" className="w-full h-full object-cover" />
                              ) : (
                                <span className="text-white/50 font-serif text-[8px] pb-0.5 px-0.5 text-center leading-tight">
                                  {(item.title || "").slice(0, 12)}
                                </span>
                              )}
                            </div>
                            <span className="text-[7px] font-mono px-1 py-0.5 rounded-full border leading-none
                                             bg-[#dfc5a4]/20 border-[#dfc5a4]/50 text-[#627d9a] dark:text-[#babbbd]">
                              ✓
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}

              <div className="flex-1 overflow-y-auto pr-1 pb-6 min-h-0">
                {isLoadingRecs ? (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-2">
                      <div className="h-3 w-24 rounded bg-[#babbbd]/30 mb-1" />
                      {[0,1,2].map(i => <SkeletonCard key={i} size="sm" />)}
                    </div>
                    <div className="flex flex-col gap-2">
                      <div className="h-3 w-24 rounded bg-[#babbbd]/30 mb-1" />
                      {[0,1,2].map(i => <SkeletonCard key={i} size="sm" />)}
                    </div>
                  </div>
                ) : recsError ? (
                  <div className={`p-4 rounded-xl border ${DIVIDER} text-center space-y-2`}>
                    <p className="text-[12px] font-medium text-red-500 dark:text-red-400">{recsError}</p>
                    <button
                      onClick={loadRecs}
                      className="text-[11px] px-3 py-1.5 rounded-lg border border-[#babbbd] dark:border-[#627d9a]/70
                                 text-[#627d9a] dark:text-[#babbbd] hover:bg-[#dfc5a4]/20 hover:border-[#dfc5a4] transition-all"
                    >
                      ↺ Retry
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 grid-rows-1 gap-4 h-full">
                    {/* Left — People Also Buy (Pipeline A) */}
                    <div className="flex flex-col gap-2 overflow-y-auto min-h-0 pr-1 pb-4">
                      <p className="text-[10px] font-mono tracking-widest uppercase text-[#627d9a] dark:text-[#babbbd] flex-shrink-0">
                        People Also Buy · Cleora + BGE-M3
                      </p>
                      {recommendations.people_also_buy?.slice(0, 10).map((book, i) => (
                        <RecommendCard
                          key={book.id ?? i} book={book} rank={i}
                          onInteract={handleInteract} onAskAIStream={handleAskAIStream}
                          isNew={newRecAsins.has(book.id)}
                        />
                      ))}
                      {(!recommendations.people_also_buy?.length) && (
                        <p className="text-[11px] text-[#babbbd] dark:text-[#627d9a] text-center mt-4">
                          No candidates yet
                        </p>
                      )}
                    </div>

                    {/* Right — You Might Like (Pipeline B) */}
                    <div className="flex flex-col gap-2 overflow-y-auto min-h-0 pl-1 pb-4">
                      <p className="text-[10px] font-mono tracking-widest uppercase text-[#627d9a] dark:text-[#babbbd] flex-shrink-0">
                        You Might Like · DIF-SASRec
                      </p>
                      {recommendations.you_might_like?.slice(0, 10).map((book, i) => (
                        <RecommendCard
                          key={book.id ?? i} book={book} rank={i}
                          onInteract={handleInteract} onAskAIStream={handleAskAIStream}
                          isNew={newRecAsins.has(book.id)}
                        />
                      ))}
                      {(!recommendations.you_might_like?.length) && (
                        <p className="text-[11px] text-[#babbbd] dark:text-[#627d9a] text-center mt-4">
                          Interact with books to activate DIF-SASRec
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT PANEL — fixed width, collapsible ── */}
        <div className={`flex-shrink-0 overflow-hidden transition-[width] duration-300 ease-in-out`}
             style={{ width: rightPanelOpen ? 384 : 0 }}>
        <div className="flex flex-col h-full" style={{ width: 384 }}>

          {/* Tabs */}
          <div className={`flex items-center px-3 py-2 border-b ${DIVIDER}`}>
            <div className="flex w-full rounded-lg p-0.5 gap-0.5
                            bg-[#2e3257]/6 dark:bg-[#fffef7]/6
                            border border-[#2e3257]/10 dark:border-[#fffef7]/10">
              {[["profile", "User Profile"], ["history", "Activity History"]].map(([tab, label]) => (
                <button
                  key={tab}
                  onClick={() => setActiveRight(tab)}
                  className={`flex-1 py-1.5 text-center text-[11px] font-medium transition-all duration-200 rounded-md cursor-pointer border-none
                    ${activeRight === tab
                      ? "bg-[#2e3257] dark:bg-[#fffef7] text-[#fffef7] dark:text-[#2e3257] shadow-sm"
                      : "bg-transparent text-[#627d9a] dark:text-[#babbbd] hover:text-[#2e3257] dark:hover:text-[#fffef7]"}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* ── Profile tab — bento grid ── */}
          {activeRight === "profile" ? (
            <div className="flex-1 overflow-y-auto p-4">
              {/* User identity row */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-[13px] font-extrabold tracking-tight text-[#2e3257] dark:text-[#fffef7]">User Profile State</h2>
                  <p className="text-[10px] text-[#627d9a] dark:text-[#babbbd] mt-0.5">
                    Aggregated embedding · temporal decay λ=0.1
                  </p>
                </div>
                <div className="text-right">
                  <div className="font-mono text-[10px] text-[#627d9a] dark:text-[#babbbd]">{userId}</div>
                  {lastTrained && <div className="font-mono text-[9px] text-[#babbbd] dark:text-[#627d9a] mt-0.5">updated {lastTrained.toLocaleTimeString()}</div>}
                </div>
              </div>

              {/* ── Bento grid ── */}
              <div className="grid grid-cols-2 gap-3">

                {/* Radar — full width */}
                <div className={`col-span-2 p-4 ${CARD}`}>
                  <p className="text-[10px] font-semibold tracking-widest uppercase text-[#627d9a] dark:text-[#babbbd] mb-4">Engagement Signals</p>
                  <ProfileRadar interactions={interactions} />
                </div>

                {/* SASRec Loss */}
                <div className={`col-span-2 p-3 ${CARD}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      {/* C: InfoTooltip explaining the pretraining→online drop */}
                      <div className="flex items-center">
                        <p className="text-[10px] font-semibold tracking-widest uppercase text-[#627d9a] dark:text-[#babbbd]">SASRec Loss</p>
                        <InfoTooltip
                          tip="The sharp drop from ~5.3 to ~0.5 is expected, not instability. Pretraining uses 512 hard negatives; online training uses random negatives from 3M+ books (much easier). The pretrained model already ranks similar items well."
                          formula="Pretrain loss ≠ Online loss scale"
                        />
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* D: training pulse badge */}
                      {trainPulse != null && (
                        <span className="fade-in font-mono text-[9px] text-emerald-500 dark:text-emerald-400">
                          ↓ {trainPulse.toFixed(3)} trained
                        </span>
                      )}
                      <span className="font-mono font-semibold text-[#2e3257] dark:text-[#dfc5a4]" style={{ fontSize: 13 }}>
                        {rlMetrics.loss_history.length > 0 ? rlMetrics.loss_history.at(-1).toFixed(4) : "0.0000"}
                      </span>
                    </div>
                  </div>
                  {sparklinePoints ? (() => {
                    const h     = rlMetrics.loss_history;
                    const total = h.length;
                    const vbW   = Math.max(1, total - 1);
                    const minV  = Math.min(...h), maxV = Math.max(...h);
                    const splitX = onlineStartIdx != null && onlineStartIdx > 0 && onlineStartIdx < total
                      ? onlineStartIdx - 0.5
                      : null;
                    return (
                      <div className="w-full relative mt-1" style={{ height: 88 }}>
                        <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none"
                          viewBox={`0 0 ${vbW} 1`}>
                          <defs>
                            <linearGradient id="lossAreaGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%"   stopColor="#627d9a" stopOpacity="0.28" />
                              <stop offset="100%" stopColor="#627d9a" stopOpacity="0.02" />
                            </linearGradient>
                          </defs>

                          {/* subtle horizontal grid at 25 / 50 / 75 % */}
                          {[0.25, 0.5, 0.75].map(y => (
                            <line key={y} x1={0} y1={y} x2={vbW} y2={y}
                              stroke="#627d9a" strokeOpacity="0.15" strokeWidth="0.5"
                              vectorEffect="non-scaling-stroke" />
                          ))}

                          {/* area fill */}
                          <polygon
                            fill="url(#lossAreaGrad)"
                            points={`0,1 ${sparklinePoints} ${vbW},1`}
                          />

                          {/* main line */}
                          <polyline
                            fill="none" stroke="#627d9a" strokeWidth="1.5"
                            strokeLinejoin="round" strokeLinecap="round"
                            vectorEffect="non-scaling-stroke"
                            points={sparklinePoints}
                          />

                          {/* phase divider */}
                          {splitX != null && (
                            <line
                              x1={splitX} y1={0} x2={splitX} y2={1}
                              stroke="#dfc5a4" strokeWidth="1.5"
                              strokeDasharray="4 3"
                              vectorEffect="non-scaling-stroke"
                            />
                          )}
                        </svg>

                        {/* Y-axis labels */}
                        <span className="absolute right-0 font-mono text-[8px] text-[#babbbd] dark:text-[#627d9a]"
                              style={{ top: 0, lineHeight: 1 }}>
                          {maxV.toFixed(2)}
                        </span>
                        <span className="absolute right-0 font-mono text-[8px] text-[#babbbd] dark:text-[#627d9a]"
                              style={{ bottom: 2, lineHeight: 1 }}>
                          {minV.toFixed(2)}
                        </span>

                        {/* phase labels */}
                        {splitX != null && (
                          <>
                            <span className="absolute font-mono text-[8px] text-[#babbbd] dark:text-[#627d9a]"
                                  style={{ top: 2, left: `${Math.max(0, (splitX / vbW) * 100 - 18)}%` }}>
                              Pretrain
                            </span>
                            <span className="absolute font-mono text-[8px] text-[#dfc5a4]"
                                  style={{ top: 2, left: `${Math.min(88, (splitX / vbW) * 100 + 2)}%` }}>
                              Online
                            </span>
                          </>
                        )}

                        {/* bottom axis line */}
                        <div className="absolute bottom-0 left-0 right-0 border-b border-[#babbbd]/35 dark:border-[#627d9a]/30" />
                      </div>
                    );
                  })() : (
                    <div className={`h-14 flex items-center justify-center rounded-lg border ${DIVIDER}`}>
                      <span className="text-[9px] text-[#babbbd] dark:text-[#627d9a]">Interact to see loss converge</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

          ) : (
            /* ── History tab ── */
            <div className="flex-1 overflow-y-auto px-5 py-4">
              <h3 className="text-[11px] font-extrabold tracking-widest uppercase text-[#627d9a] dark:text-[#babbbd] mb-3">
                Interaction History
              </h3>
              {interactions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 gap-3 text-center">
                  <p className="text-[11px] text-[#babbbd] dark:text-[#627d9a]">
                    Interact with search results or<br />recommendations to train DIF-SASRec
                  </p>
                  <p className="text-[9px] text-[#babbbd]/70 dark:text-[#627d9a]/60 mt-1">Profile fingerprint updates in real-time</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {interactions.map((item, i) => (
                    <div key={i} className={`flex items-center gap-3 py-2 fade-in border-b ${DIVIDER}`}>
                      <BookCover color={item.cover_color} title={item.title} size="sm" imageUrl={item.image_url} />
                      <div className="flex-1 min-w-0">
                        <p className="truncate font-serif text-[11px] font-medium text-[#2e3257] dark:text-[#fffef7]">{item.title}</p>
                        <p className="text-[9px] text-[#627d9a] dark:text-[#babbbd] mt-0.5">{item.author}</p>
                      </div>
                      <div className="flex flex-col items-end gap-1 flex-shrink-0">
                        <span className={`text-[9px] px-2 py-0.5 rounded-full font-medium border
                          ${item.action === "click"
                            ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-300 dark:border-emerald-700/60 text-emerald-700 dark:text-emerald-400"
                            : "bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700/60 text-red-600 dark:text-red-400"}`}>
                          {item.action}
                        </span>
                        <span className="font-mono text-[8px] text-[#babbbd] dark:text-[#627d9a]">
                          {new Date(item.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>{/* end inner fixed-width wrapper */}
        </div>{/* end collapsible outer */}
      </div>
    </div>
  );
}
