import { useState } from "react";
import { BookCover } from "../../ui/BookCover";
import { ScoreBadge } from "../../ui/ScoreBadge";

function parseAuthor(raw) {
  if (!raw) return "Unknown Author";
  if (typeof raw === "string" && raw.startsWith("{")) {
    try { const m = raw.match(/'name':\s*'([^']+)'/); if (m) return m[1]; } catch (_) {}
  }
  return raw;
}

export function SearchResultCard({ book, onInteract, onAskAIStream }) {
  const [showAI, setShowAI]     = useState(false);
  const [aiText, setAiText]     = useState("");
  const [aiLoading, setLoading] = useState(false);

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
          setLoading(false); // Hide loading as soon as first token arrives
          setAiText(prev => prev + chunk);
        }
      } catch (_) {
        setAiText("Failed to query AI helper.");
        setLoading(false);
      }
    }
  };

  const genre  = book.genre || "Books";
  const cover  = book.cover_color || "#1e1b4b";
  const author = parseAuthor(book.author);

  return (
    <div className="group flex gap-3 p-3 rounded-xl border border-[#babbbd] dark:border-[#627d9a]/60
                    bg-white/50 dark:bg-[#fffef7]/5
                    hover:border-[#dfc5a4] dark:hover:border-[#dfc5a4]/60
                    hover:bg-[#dfc5a4]/8 dark:hover:bg-[#dfc5a4]/5
                    transition-all duration-200 cursor-pointer shadow-sm">

      <BookCover color={cover} title={book.title} size="md" imageUrl={book.image_url} />

      <div className="flex-1 min-w-0">
        {/* Title row */}
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-serif font-semibold leading-tight text-[#2e3257] dark:text-[#fffef7]" style={{ fontSize: 16 }}>
              {book.title}
            </p>
            <p className="text-[#627d9a] dark:text-[#babbbd] mt-0.5" style={{ fontSize: 13 }}>{author}</p>
            <div className="flex flex-wrap gap-1 mt-1">
              <span className="px-2 py-0.5 rounded-full text-[11px]
                               bg-[#dfc5a4]/25 text-[#627d9a] dark:text-[#babbbd]">
                {genre}
              </span>
              {book.sub_genre && book.sub_genre !== genre && (
                <span className="px-2 py-0.5 rounded-full text-[11px]
                                 bg-[#babbbd]/15 dark:bg-[#627d9a]/15
                                 text-[#babbbd] dark:text-[#627d9a]">
                  {book.sub_genre}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-col gap-1 flex-shrink-0 items-end">
            <ScoreBadge score={book.score} label="RRF" />
            {book.text_sim > 0 && <ScoreBadge score={book.text_sim} label="BGE-M3" />}
            {book.img_sim  > 0 && <ScoreBadge score={book.img_sim}  label="CLIP"  />}
          </div>
        </div>

        {/* Actions — single compact row */}
        <div className="flex gap-1.5 mt-2 justify-end relative">
          <button
            onClick={() => onInteract(book, "click")}
            title="Mark as interested"
            className="px-3 py-1 rounded-full text-[12px] font-medium transition-all duration-150
                       bg-[#2e3257]/10 dark:bg-[#fffef7]/10
                       border border-[#2e3257]/25 dark:border-[#fffef7]/20
                       text-[#2e3257] dark:text-[#fffef7]
                       hover:bg-[#dfc5a4]/30 hover:border-[#dfc5a4]"
          >
            ✓ Interested
          </button>
          <button
            onClick={handleAI}
            title="Ask AI about this book"
            className="px-3 py-1 rounded-full text-[12px] transition-all duration-150
                       bg-[#627d9a]/10 dark:bg-[#627d9a]/15
                       border border-[#627d9a]/25 dark:border-[#627d9a]/40
                       text-[#627d9a] dark:text-[#babbbd]
                       hover:bg-[#627d9a]/20"
          >
            {showAI ? "✕ AI" : "✦ Ask AI"}
          </button>
          <button
            onClick={e => { e.stopPropagation(); onInteract(book, "not_interested"); }}
            title="Not interested — hide from recommendations"
            className="px-3 py-1 rounded-full text-[12px] font-medium transition-all duration-150
                       bg-rose-50 dark:bg-rose-900/20
                       border border-rose-200 dark:border-rose-800/60
                       text-rose-500 dark:text-rose-400
                       hover:bg-rose-100 dark:hover:bg-rose-900/40"
          >
            Not interested
          </button>

          {/* AI popover */}
          {showAI && (
            <div className="absolute z-20 p-3 rounded-xl shadow-md fade-in text-left
                            bg-[#fffef7] dark:bg-[#2e3257]
                            border border-[#babbbd] dark:border-[#627d9a]"
              style={{ top: "calc(100% + 8px)", left: 0, right: 0, minWidth: 260 }}
            >
              <p className="font-serif font-bold text-[#2e3257] dark:text-[#fffef7] mb-0.5" style={{ fontSize: 14 }}>
                {book.title}
              </p>
              <p className="text-[#627d9a] dark:text-[#babbbd] mb-2" style={{ fontSize: 11 }}>by {author}</p>
              <div className="text-[#2e3257] dark:text-[#fffef7] overflow-y-auto" style={{ fontSize: 11, lineHeight: 1.55, whiteSpace: "pre-wrap", maxHeight: 160 }}>
                {aiLoading ? (
                  <span className="shimmer text-[#627d9a]">Thinking…</span>
                ) : (
                  aiText.split("\n").map((line, i) => (
                    <p key={i} className={line.startsWith("**") ? "mt-1.5" : ""}>
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
  );
}
