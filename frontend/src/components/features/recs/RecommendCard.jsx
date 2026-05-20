import { useState, useEffect, useRef } from "react";
import { BookCover } from "../../ui/BookCover";
import { ScoreBadge } from "../../ui/ScoreBadge";

function parseAuthor(raw) {
  if (!raw) return "Unknown Author";
  if (typeof raw === "string" && raw.startsWith("{")) {
    try { const m = raw.match(/'name':\s*'([^']+)'/); if (m) return m[1]; } catch (_) {}
  }
  return raw;
}

const PIPELINE_STYLE = {
  "Cleora + BGE-M3": { bg: "#2e3257", glow: "rgba(98,125,154,0.5),rgba(46,50,87,0.5)"   },
  "Cleora + CLIP":   { bg: "#1e3a5f", glow: "rgba(30,58,95,0.6),rgba(14,42,71,0.5)"     },
  "DIF-SASRec":      { bg: "#065f46", glow: "rgba(16,185,129,0.5),rgba(6,95,70,0.55)"   },
  "RL-DQN":          { bg: "#78350f", glow: "rgba(245,158,11,0.45),rgba(120,53,15,0.5)" },
  "Cleora + BLaIR":  { bg: "#2e3257", glow: "rgba(98,125,154,0.5),rgba(46,50,87,0.5)"   },
};

function PipelineBadge({ label }) {
  if (!label) return null;
  const { bg, glow } = PIPELINE_STYLE[label] ?? { bg: "#374151", glow: "rgba(107,114,128,0.4),rgba(55,65,81,0.4)" };
  const [ring, shadow] = glow.split(",");
  return (
    <span
      className="inline-flex items-center px-2.5 py-1 rounded-full flex-shrink-0
                 text-[#fffef7] font-semibold whitespace-nowrap"
      style={{
        fontSize: 11,
        background: bg,
        boxShadow: `0 0 0 1px ${ring}, 0 2px 8px ${shadow}`,
      }}
    >
      {label}
    </span>
  );
}

export function RecommendCard({ book, onInteract, onAskAIStream, rank, isNew = false }) {
  const [showAI, setShowAI]     = useState(false);
  const [aiText, setAiText]     = useState("");
  const [aiLoading, setLoading] = useState(false);

  const [badgeVisible, setBadgeVisible] = useState(isNew);
  const [badgeExiting, setBadgeExiting] = useState(false);
  const prevIsNew = useRef(isNew);

  useEffect(() => {
    if (isNew && !prevIsNew.current) {
      setBadgeVisible(true);
      setBadgeExiting(false);
    } else if (!isNew && prevIsNew.current && badgeVisible) {
      setBadgeExiting(true);
    }
    prevIsNew.current = isNew;
  }, [isNew]);

  const handleAI = async (e) => {
    e.stopPropagation();
    if (showAI) { setShowAI(false); return; }
    setShowAI(true);
    if (!aiText) {
      setLoading(true);
      setAiText("");
      try {
        const stream = onAskAIStream(book);
        for await (const chunk of stream) {
          setLoading(false);
          setAiText(prev => prev + chunk);
        }
      } catch (_) {
        setAiText("Failed to query AI helper.");
        setLoading(false);
      }
    }
  };

  const cover  = book.cover_color || "#1e1b4b";
  const author = parseAuthor(book.author);

  return (
    <div className="flex gap-3 p-4 rounded-xl border border-[#babbbd] dark:border-[#627d9a]/60
                    bg-white/40 dark:bg-[#fffef7]/5
                    hover:border-[#dfc5a4] dark:hover:border-[#dfc5a4]/50
                    hover:bg-[#dfc5a4]/6 dark:hover:bg-[#dfc5a4]/4
                    transition-all duration-200 cursor-pointer shadow-sm">

      {/* Far-left — cover with rank + new badges overlaid */}
      <div className="relative flex-shrink-0">
        <span className="absolute -top-1 -left-1 z-10 font-mono font-bold leading-none
                         bg-[#2e3257] dark:bg-[#fffef7] text-[#fffef7] dark:text-[#2e3257]
                         rounded px-1 py-0.5"
              style={{ fontSize: 10 }}>
          #{rank + 1}
        </span>
        {badgeVisible && (
          <span
            className={`absolute -top-1 -right-1 z-10 px-1.5 py-0.5 rounded-full font-mono font-bold leading-none
                        bg-[#dfc5a4] text-[#2e3257]
                        ${badgeExiting ? "badge-exit" : "fade-in"}`}
            style={{ fontSize: 7 }}
            onAnimationEnd={() => { if (badgeExiting) setBadgeVisible(false); }}
          >
            New
          </span>
        )}
        <BookCover color={cover} title={book.title} size="md" imageUrl={book.image_url} />
      </div>

      {/* Four-corners info panel */}
      <div className="flex flex-col flex-1 min-w-0 justify-between gap-2">

        {/* TOP ROW — title+author (left) · pipeline badge (right) */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="font-serif font-semibold leading-tight text-[#2e3257] dark:text-[#fffef7] line-clamp-2"
               style={{ fontSize: 15 }}>
              {book.title}
            </p>
            <p className="text-[#627d9a] dark:text-[#babbbd] truncate mt-0.5" style={{ fontSize: 12 }}>
              {author}
            </p>
          </div>
          <PipelineBadge label={book.layer} />
        </div>

        {/* BOTTOM ROW — genres+score pills (left) · action buttons (right) */}
        <div className="flex items-end justify-between gap-2">

          {/* Bottom-left — genre tags then score pills stacked */}
          <div className="flex flex-col gap-1 min-w-0">
            {(book.genre || book.sub_genre) && (
              <div className="flex flex-wrap gap-1">
                {book.genre && (
                  <span className="px-1.5 py-px rounded-full text-[11px]
                                   bg-[#dfc5a4]/25 text-[#627d9a] dark:text-[#babbbd]">
                    {book.genre}
                  </span>
                )}
                {book.sub_genre && book.sub_genre !== book.genre && (
                  <span className="px-1.5 py-px rounded-full text-[11px]
                                   bg-[#babbbd]/15 dark:bg-[#627d9a]/15
                                   text-[#babbbd] dark:text-[#627d9a]">
                    {book.sub_genre}
                  </span>
                )}
              </div>
            )}
            <div className="flex flex-wrap gap-1">
              {book.text_sim > 0 && <ScoreBadge score={book.text_sim} label="BGE-M3" />}
              {book.img_sim  > 0 && <ScoreBadge score={book.img_sim}  label="CLIP"   />}
              {(!book.text_sim && !book.img_sim) && (
                <ScoreBadge score={book.score || 0} label="SASRec" />
              )}
            </div>
          </div>

          {/* Bottom-right — action buttons */}
          <div className="flex gap-1 flex-shrink-0 relative">
            <button
              onClick={() => onInteract(book, "click")}
              title="Mark as interested"
              className="px-3 py-1 rounded-full text-[11px] font-medium transition-all duration-150
                         bg-[#2e3257]/10 dark:bg-[#fffef7]/10
                         border border-[#2e3257]/22 dark:border-[#fffef7]/18
                         text-[#2e3257] dark:text-[#fffef7]
                         hover:bg-[#dfc5a4]/30 hover:border-[#dfc5a4]"
            >
              ✓
            </button>
            <button
              onClick={handleAI}
              title="Ask AI about this book"
              className="px-3 py-1 rounded-full text-[11px] transition-all duration-150
                         bg-[#627d9a]/10 border border-[#627d9a]/25 dark:border-[#627d9a]/40
                         text-[#627d9a] dark:text-[#babbbd]
                         hover:bg-[#627d9a]/20"
            >
              {showAI ? "✕" : "✦"}
            </button>
            <button
              onClick={e => { e.stopPropagation(); onInteract(book, "not_interested"); }}
              title="Not interested — hide from recommendations"
              className="px-3 py-1 rounded-full text-[11px] font-medium transition-all duration-150
                         bg-rose-50 dark:bg-rose-900/20
                         border border-rose-200 dark:border-rose-800/60
                         text-rose-500 dark:text-rose-400
                         hover:bg-rose-100 dark:hover:bg-rose-900/40"
            >
              ✕
            </button>

            {showAI && (
              <div className="absolute z-30 p-2.5 rounded-xl shadow-md fade-in text-left
                              bg-[#fffef7] dark:bg-[#2e3257]
                              border border-[#babbbd] dark:border-[#627d9a]"
                style={{ bottom: "calc(100% + 6px)", right: 0, minWidth: 220 }}
              >
                <p className="font-serif font-bold text-[#2e3257] dark:text-[#fffef7] mb-0.5" style={{ fontSize: 11 }}>
                  {book.title}
                </p>
                <p className="text-[#627d9a] dark:text-[#babbbd] mb-1.5" style={{ fontSize: 9 }}>by {author}</p>
                <div className="text-[#2e3257] dark:text-[#fffef7] overflow-y-auto"
                     style={{ fontSize: 10, lineHeight: 1.55, whiteSpace: "pre-wrap", maxHeight: 120 }}>
                  {aiLoading ? (
                    <span className="shimmer text-[#627d9a]">Thinking…</span>
                  ) : (
                    aiText.split("\n").map((line, i) => (
                      <p key={i} className={line.startsWith("**") ? "mt-1" : ""}>
                        {line.split(/(\*\*.*?\*\*)/).map((part, j) =>
                          part.startsWith("**") && part.endsWith("**")
                            ? <strong key={j}>{part.slice(2, -2)}</strong>
                            : part
                        )}
                      </p>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
