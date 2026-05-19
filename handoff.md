# Session Handoff

## What was completed

### Capstone report edits (`Captsone/sections/`)

**Abstract** — Removed all HR@10 numbers and multiplier comparisons. Now describes what was built and points to Chapter 5 for results. No benchmark metrics in the abstract.

**Chapter 1.3 Scope** — Removed the benchmark-metrics bullet (HR@k, NDCG@k). Replaced with a plain description of the two pipelines. Fixed wrong "Bellman error" term.

**Chapter 3.2 Modules Analysis** — Removed the entire Data Ingestion subsection (3.2.1). Slimmed the Recommendation Module subsection to 4 sentences: what GRU was, what it scored, why it failed, what replaced it.

**Chapter 3.3 Capabilities & Challenges** — Removed the Data Ingestion row from the challenges table. Fixed typo: GRU HR@10 0.01031 → 0.1031.

**Chapter 3.4 Chapter Conclusion** — Removed ingestion from the weakness list. Toned down dramatic framing.

**Chapter 4.1 System Infrastructure**
- Tikz diagram: "Phase 2A" → "Pipeline A", "Phase 2B" → "Pipeline B" (comment stubs unchanged).
- NLLB figure width: 0.88\textwidth → 0.55\textwidth (was taking a full page).
- Pipeline B description rewritten to include the missing HNSW retrieval step. Actual flow: HNSW KNN (200 candidates) → content veto (τ=0.3) → DIF-SASRec scoring. The old text made it sound like DIF-SASRec generated candidates directly.
- Removed the "The GRU-SeqDQN recommendation module is replaced by..." opening sentence.
- Updated to describe two-column layout and top 10 each.

**Chapter 4.2 Ingestion Improvements** — Fixed dangling reference to deleted sec:ingestion_analysis. Rewrote opening to be self-contained.

**Chapter 4.3 Data Visualisation**
- 4.3.2 Dual Recommendation Panels: "pair of sub-tabs" → "single two-column view, People Also Buy left (top 10), You Might Like right (top 10)".
- 4.3.3 Online Training Visualisation: Removed the Train Feed widget paragraph (user removed that tab from the UI). Kept radar chart + SASRec Loss sparkline.
- Reduced textit/texttt/textbf density throughout — was overused in prose.

**Chapter 4.5 Chapter Summary** — Removed "18.6× improvement" em-dash clause.

**Chapter 4.7 Model Training** — Removed the "Training Loss vs Benchmark Quality" math-heavy subsection (ln(K+1) derivation, normalised loss table). Replaced with 4 plain sentences.

**Chapter 5.1 Experiment Setup**
- Removed System (A∪B) from baselines list.
- Fixed Max sequence length: 200 → 50 (confirmed from app/config.py MAX_SEQ_LEN=50).
- Fixed Cleora index size: 375,280 → 375,439 (confirmed from data/cleora_embeddings.npz).

**Chapter 5.2 Component Analysis**
- Removed System (A∪B) from ablation table and narrative.
- Removed "18.6× improvement" from latency caption and text.
- Fixed two prose em-dashes → commas/parentheses.

**Chapter 5.3 End-to-End Evaluation**
- Removed System (A∪B) row from main results table.
- Rewrote narrative: Pipeline A (HR@10=0.9047) and Pipeline B (HR@10=0.7745) are the primary results.

**Chapter 5.4 Qualitative Analysis**
- Removed A∪B column from quartile performance table.
- Updated union coverage statement: "97.4% of test users" kept as a descriptive observation (not a headline metric).
- Fixed one prose em-dash.

**Chapter 5.5 Chapter Conclusion** — Replaced union headline with per-pipeline numbers. Removed all multiplier comparisons.

**Chapter 7 Conclusion**
- Updated metrics summary and objectives table to per-pipeline numbers.
- Removed "843% improvement", "124% improvement", all multiplier language.
- Fixed all "Bellman-error loss sparkline" → "training loss sparkline" (9 total occurrences across all chapters).

**Chapter 2.1.2 DIF-SASRec Architecture**
- Removed BGE-M3-specific reference from the theoretical background (inappropriate in a theory chapter).
- Removed the three detailed attention equations (A_content, A_cat, Q/K notation) and both training loss equations.
- Kept: the fusion equation (A_fused = α·A_cat + (1-α)·A_content), plain-English explanations, and the training summary.

**Appendix** — Fixed 6 fact errors (all confirmed from app/config.py and data files):
- Max sequence length: 200 → 50
- Feed-forward dimension: 2,048 → 1,024 (hidden_dim * 2 = 512 * 2)
- Dropout rate: 0.1 → 0.2
- Learning rate: 10^{-4} → 10^{-3}
- Online training: removed "reward 1.0/5.0" DQN language, replaced with correct sampled softmax description
- HNSW vectors: 1,742,826 → 1,732,910 (confirmed from faiss index)
- Cleora items: 375,280 → 375,439 (confirmed from npz file)

---

## UI task for next session

### Goal
Change the Recommendations tab from a merged `combined` grid to a **two-column split view**: People Also Buy (Pipeline A, left) and You Might Like (Pipeline B, right), top 10 each, displayed side by side.

### Current behaviour
File: `frontend/src/App.jsx`, lines ~742–752

The recs tab currently renders `recommendations.combined` as a flat `grid-cols-2` grid — all results mixed together with no pipeline separation:

```jsx
<div className="grid grid-cols-2 gap-2">
  {recommendations.combined?.map((book, i) => (
    <RecommendCard
      key={i} book={book} rank={i}
      onInteract={handleInteract} onAskAIStream={handleAskAIStream}
      isNew={newRecAsins.has(book.id)}
    />
  ))}
</div>
```

Also on lines ~635–652, there is a badge cluster that includes `"Union (A∪B)"` — remove that badge.

### Target behaviour

Replace the grid above with a two-column split. Each column has its own header and scrolls its own list of 10 cards. The pipeline label on each card already identifies the source (`book.layer`).

```jsx
{/* Two-column split: Pipeline A left, Pipeline B right */}
<div className="grid grid-cols-2 gap-4 h-full">

  {/* Left — People Also Buy (Pipeline A) */}
  <div className="flex flex-col gap-2 overflow-y-auto pr-1">
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
  <div className="flex flex-col gap-2 overflow-y-auto pl-1">
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
```

### Badge cluster cleanup (lines ~634–652)

Remove the `"Union (A∪B)"` badge. Keep the other two:

```jsx
{/* Remove this badge */}
<span className="... bg-[#dfc5a4]/15 ...">Union (A∪B)</span>
```

### isNew tracking

Currently `newRecAsins` is diffed against `recs.combined`. After the change, diff against the union of both pipelines. In `loadRecs` around line ~159:

```js
// Change from:
const nextIds = (recs.combined || []).map(b => b.id);

// Change to:
const nextIds = [
  ...(recs.people_also_buy || []),
  ...(recs.you_might_like  || []),
].map(b => b.id);
```

### Mock data

The existing `MOCK_RECS` in App.jsx (lines ~19–34) already has `people_also_buy` and `you_might_like` arrays. No change needed there — it will work with the new layout.

### Skeleton state

The skeleton loading block (lines ~726–729) currently does:
```jsx
<div className="grid grid-cols-2 gap-2">
  {[0,1,2,3].map(i => <SkeletonCard key={i} size="sm" />)}
</div>
```

Update it to mirror the two-column layout:
```jsx
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
```

### Files to touch
- `frontend/src/App.jsx` — main change (recs grid, badge cluster, isNew diff)
- No changes needed to `RecommendCard.jsx`, `api.js`, or the backend

### Verify after change
- People Also Buy column shows Cleora + BGE-M3 layer tags
- You Might Like column shows DIF-SASRec layer tags
- Cold-start (< 5 interactions): both columns show empty state messages
- Personalized mode: both columns populate after loadRecs()
- Rank badge (#1, #2...) is per-column, not global
