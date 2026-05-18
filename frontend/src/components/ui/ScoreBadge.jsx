export function ScoreBadge({ score, label }) {
  const pct = Math.round(score * 100);

  const fillRgb = pct > 85 ? "16,185,129"   // emerald
                : pct > 70 ? "245,158,11"    // amber
                :            "98,125,154";   // slate

  const fillColor   = `rgba(${fillRgb},0.28)`;
  const borderColor = `rgba(${fillRgb},0.55)`;

  return (
    <div
      title={`${label}: ${pct}`}
      className="relative flex items-center justify-center rounded-full overflow-hidden border flex-shrink-0"
      style={{
        height: 20,
        minWidth: 68,
        paddingInline: 8,
        borderColor,
        background: `linear-gradient(to right, ${fillColor} ${pct}%, transparent ${pct}%)`,
      }}
    >
      <span
        className="font-mono font-semibold text-[#2e3257] dark:text-[#fffef7] whitespace-nowrap select-none"
        style={{ fontSize: 10, letterSpacing: "0.02em", textShadow: "0 0 6px rgba(255,255,255,0.6)" }}
      >
        {label} · {pct}
      </span>
    </div>
  );
}
