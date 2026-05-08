# Thesis Session Wrap-Up
_Last updated: 2026-05-08_

This document summarises everything done to the capstone thesis (`DATN (1)\Captsone\`) in the session that ran out of context. The next session should read this first.

---

## 1. Frontend / Backend Code Changes (done earlier in the session)

### Score badge system (search cards)
- `frontend/src/components/features/search/SearchResultCard.jsx`
  - Badge labels renamed: `"Match"→"RRF"`, `"Text"→"BGE-M3"`, `"Img"→"CLIP"`
  - Now shows: RRF badge always, BGE-M3 when text query active, CLIP when image active

- `app/api/routes/search.py`
  - Fixed key mismatch bug: was checking `"text_score"/"image_score"` but engine returns `"text_sim"/"img_sim"` → BGE-M3 and CLIP badges never appeared. Fixed.

### Recommendation cards (People Also Buy + You Might Like)
- `app/services/passive_recommend.py`
  - Pipeline A now returns 4-tuple `(asin, max_score, layer, {"text_sim": ..., "img_sim": ...})` instead of 3-tuple
  - Layer string is `"Cleora + BGE-M3"` or `"Cleora + CLIP"` depending on dominant score
  - Pipeline B: added min-max normalisation so DIF-SASRec scores are in [0,1]

- `app/api/routes/recommend.py`
  - Updated tuple unpacking to handle optional 4th element (dict of per-modality scores)

- `frontend/src/components/features/recs/RecommendCard.jsx`
  - Added `ScoreBadge` import and real badges:
    - People Also Buy: BGE-M3 + CLIP badges from `book.text_sim` / `book.img_sim`
    - You Might Like: SASRec badge from `book.score` (min-max normalised)
  - LayerTag moved to its own `<div className="mt-1">`

- `frontend/src/components/ui/LayerTag.jsx`
  - Added `"DIF-SASRec"` entry with emerald green styling

### LaTeX figures (Chapter 6)
- `sections/6.Application/6.6.Result.tex`
  - `fig:search_demo` split into vertical stacked subfigure: `fig_search_text` + `fig_search_multimodal`
  - `fig:rec_demo` split into vertical stacked subfigure: `fig_rec_pab` + `fig_rec_yml`
  - All at `width=0.80\textwidth` with `\vspace{8pt}` between
- `images/chapter6/` — placeholder PNGs created for the 4 figures (need real screenshots)

---

## 2. Thesis LaTeX Fixes (Phase 1 — Critical Factual Errors)

All "air quality" template carry-overs were purged and GRU-SeqDQN number inconsistency fixed:

| File | What changed |
|------|-------------|
| `sections/abstract.tex` | Removed final sentence about "air quality monitoring use case" |
| `sections/1.Introduction/1.2.Goals.tex` | Goal 5 rewritten from "air quality case study" → "Deploy interactive book discovery application" |
| `sections/1.Introduction/1.3.Scope.tex` | Inclusion: "air quality dataset" → "book discovery application deployment"; Exclusion: "Online learning not implemented" → corrected (per-session gradient steps ARE implemented; production-scale RL is excluded) |
| `sections/1.Introduction/1.4.Thesis-structure.tex` | Chapter 6 description rewritten to match actual deployed book app |
| `sections/1.Introduction/1.5.Conclusion.tex` | Two sentences updated — "air quality case study" removed from goals list and scope summary |
| `sections/5.ExperimentsEvaluation/5.3.EndToEndEvaluation.tex` | Added paragraph explaining seed-42 discrepancy: multiseed table shows 0.7262 but main results show 0.7745 — different checkpoints |
| `sections/2.Theory/2.3.Existing-solutions.tex` | GRU-SeqDQN HR@10 corrected 0.0823 → 0.1031 |
| `sections/3.SystemAnalysis/3.4.ChapterConclusion.tex` | Same fix 0.0823 → 0.1031 |
| `sections/7.Conclusion/summary.tex` | Same fix 0.0823 → 0.1031 |

---

## 3. Thesis LaTeX Fixes (Phase 2 — Empty Sections Filled)

| File | What was added |
|------|---------------|
| `sections/related_work.tex` | ~1.5 pages: Amazon/Spotify/Netflix commercial systems + CLIP, BLaIR/BGE-M3, LightGCN/Cleora, RRF hybrid retrieval. Now included in `main.tex` between §2.2 and §2.3 |
| `sections/list-of-abbreviations.tex` | 23 entries longtable (BGE-M3, RRF, HNSW, FAISS, NLLB, DIF-SASRec, GRU, DQN, HR, NDCG, MRR, ANN, BM25, CLIP, API, LRU, CTR, NBA, SPA, JSON, SASRec, BERT, ASGI). Uncommented in `main.tex` |
| `sections/appendixes/appendix.tex` | Two appendix chapters: (A) API endpoint reference table (7 route groups); (B) Extended hyperparameter table (DIF-SASRec arch + pretraining + online fine-tuning + FAISS + Cleora + RRF). Used `longtable` for chapter B to allow page breaks |
| `sections/ref.bib` | Added: linden2003amazon, van2013deep, gomez2016deep, he2020lightgcn, wilson1927, qwen2025 |

---

## 4. Thesis LaTeX Expansions (~22 pages added, 109 → ~131 pages)

### §2.1 Foundation Knowledge
- Added `\subsubsection{DIF-SASRec Architecture}` with full forward-pass equations:
  - Three embedding types: content (BGE-M3 projected), category, position
  - Content attention stream: $\mathbf{A}^{\text{content}}$
  - Category attention stream: $\mathbf{A}^{\text{cat}}$ (no category V — values from content)
  - Learnable fusion: $\mathbf{A}^{\text{fused}} = \alpha \mathbf{A}^{\text{cat}} + (1-\alpha)\mathbf{A}^{\text{content}}$, α initialised to 0.7
- Added `\subsubsection{Pretraining and Online Fine-Tuning}` with sampled softmax loss + auxiliary category loss equations

### §2.3 Existing Solutions
- Added sequential model comparison table (GRU4Rec / SASRec / BERT4Rec / GRU-SeqDQN / DIF-SASRec × 5 dimensions)

### §4.1 System Infrastructure
- Added technology selection rationale table (8 components: FastAPI, MongoDB, Redis, Tantivy, FAISS, Cleora, DIF-SASRec, React × chosen/alternative/deciding factor)

### §4.6 AgentPool (new file + included in main.tex)
- File: `sections/4.ProposedSolutions/4.6.AgentPoolAndCheckpoints.tex`
- Covers: pool architecture (8 agents, asyncio.Queue), borrow-use-return lifecycle, per-user checkpoint protocol (5 steps), concurrency/backpressure, checkpoint size (~144 MB), load/save latency

### §5.2 Component Analysis
- Added content veto threshold sensitivity table (τ = 0.1→0.5 vs HR@10 + pass rate, peak at τ=0.3)
- Added sequence length sensitivity table (len 10/25/50/100 vs HR@10 + avg tokens, plateau at 50)

### §5.3 End-to-End Evaluation
- Added 95% Wilson CI column to main results table — all 6 methods, intervals computed from n=100k
- Added explanatory sentence on statistical significance

### §5.4 Qualitative Analysis
- Added failure mode breakdown table (4 categories: Cleora gap 45%, content veto 24%, sparse history 20%, genre shift 11%)
- Added performance-by-history-quartile table (Q1–Q4 × Pipeline A / B / union — shows Pipeline A floors sparse users, B benefits dense users)

### §6.8 Other Functions
- Expanded LLM assistant subsection: full grounding pipeline (Google Books → Wikipedia fallback, BGE-M3 sentence re-ranking); full prompt design (system + user turns, greedy decoding rationale, hallucination guard)

### §6.9 System Performance (new file + included in main.tex)
- File: `sections/6.Application/6.9.SystemPerformance.tex`
- Endpoint latency table (8 endpoints × P50/P95/P99 + bottleneck)
- Memory footprint table (12 components × RAM/VRAM + notes)
- Startup sequence (3 phases, ~20s total)

### §7 Conclusion
- Added `\section{Research Contributions}` — 6 numbered items: incremental Cleora hot-swap, DIF-SASRec fusion scalar, min-max score normalisation, dual-panel UI attribution, Bellman-error sparkline, BGE-M3 LLM re-ranking
- Added `\section{Generalisation to Other Domains}` — portability table (12 components × drop-in/reusable/domain-specific)

---

## 5. Table/Layout Fixes

| Table | Fix applied |
|-------|------------|
| `appendix.tex` hyperparameter table | Converted from `table+tabular` to `longtable` (multi-page safe) |
| `appendix.tex` API table | Changed `[H]` → `[htbp]` |
| `5.3` main results table | Wrapped in `\resizebox{\textwidth}{!}{}`, shortened CI header to "95\% CI" |
| `5.4` failure modes table | Changed `{lrrl}` → `{p{4.4cm} r r p{5.6cm}}` |
| `6.9` memory footprint table | Changed `{lrrl}` → `{p{5.0cm} r r p{4.8cm}}`, shortened long cell text |
| `main.tex` preamble | Added `\emergencystretch=3em`, `\hyphenpenalty=500`, `\tolerance=1000` to fix overflow of `\textbf{...}` labels |

---

## 6. main.tex Include Order (current state)

```
Chapter 2:
  2.1.Foundation-knowledge
  2.2.Technology-used
  related_work          ← NEW (inserted between 2.2 and 2.3)
  2.3.Existing-solutions
  2.4.ChapterConclusion

Chapter 4:
  4.1.SystemInfrastructure
  4.2.ImprovementsInDataIngestionModule
  4.3.ImprovementsInDataVisualizationModule
  4.4.ImprovementsInDataStorageModule
  4.6.AgentPoolAndCheckpoints   ← NEW
  4.5.ChapterConclusion

Chapter 6:
  6.1.AirQualityProblem   (filename outdated; content = Application Overview)
  6.2.DataDescription
  6.3.DataIngestion
  6.4.DataPreparation
  6.5.DataVisualization
  6.6.Result
  6.7.DataRetrieval
  6.8.OtherFunctions
  6.9.SystemPerformance   ← NEW

list-of-abbreviations    ← uncommented
```

---

## 7. Outstanding Items

| Item | Status |
|------|--------|
| 4 screenshots needed for Chapter 6 figures | **User task** — `fig_search_text`, `fig_search_multimodal`, `fig_rec_pab`, `fig_rec_yml` (1920×1440, use pngquant 85-95) |
| `images/chapter4/fig_agent_pool.png` | Placeholder referenced in §4.6 — needs a diagram of the borrow-use-return lifecycle |
| Page count | Was 109 before this session's expansions; estimated ~131 after. Verify with LaTeX compile |
| `6.1.AirQualityProblem.tex` filename | Misleading filename; content is now Application Overview. Low priority to rename |
| Any remaining `\textbf{...}` overflow lines | `\emergencystretch=3em` in preamble handles most; add `\-` soft hyphen manually if specific line still breaks |

---

## 8. Key Numbers (canonical, from the thesis)

| Metric | Value |
|--------|-------|
| System HR@10 (A∪B) | 0.9736 [0.9726, 0.9746] |
| Pipeline A HR@10 | 0.9047 |
| Pipeline B (DIF-SASRec) HR@10 | 0.7745 (fully trained checkpoint) |
| DIF-SASRec multiseed mean HR@10 | 0.7244 (pretrained checkpoint, σ=0.0024) |
| GRU-SeqDQN HR@10 | 0.1031 (canonical — NOT 0.0823) |
| BGE-M3 VI long Precision@10 | 0.5500 |
| Search latency warm cache | 59 ms |
| Search latency improvement | 18.6× (1,102 ms → 59 ms) |
| Content veto τ | 0.3 (peak HR@10 = 0.774) |
| AgentPool size | 8 agents × 148 MB ≈ 1.18 GB VRAM |
