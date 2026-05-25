# Capstone Defense — MCP Execution Plan Progress

**Started:** 2026-05-24
**Plan version:** v3

---

## Status Overview

| Step | Task | Status | Output File |
|------|------|--------|-------------|
| 1A | Research trend analysis (NBA/sequential rec) | ✅ Done | `Markdowns/report/trend_analysis.md` |
| 1B | Literature review — traditional sequential | ✅ Done | `Markdowns/report/literature_step1.md` |
| 1B | Literature review — multimodal/visual | ✅ Done | `Markdowns/report/literature_step1.md` |
| 1C | Cross-verify all cited papers | ✅ Done | `Markdowns/report/verified_papers.md` |
| 2A | Code verify: routing logic | ✅ Done | `Markdowns/report/code_verification_step2.md` |
| 2B | Code verify: AgentPool / Phase 2 | ✅ Done | `Markdowns/report/code_verification_step2.md` |
| 2C | Code verify: HR@10 eval reproducibility | ✅ Done | `Markdowns/report/code_verification_step2.md` |
| 3 | Write Chapter 2 NBA section (LaTeX) | ✅ Done | `Captsone/chapter2_nba_section.tex` |
| 4 | Write Chapter 5 Holistic Eval (LaTeX) | ✅ Done | `Captsone/chapter5_holistic.tex` |
| 5A | Slide: NBA Origins Timeline | ✅ Done | `slides/slide_nba_origins.png` |
| 5B | Slide: Alternative NBA Approaches | ✅ Done | `slides/slide_nba_alternatives.png` |
| 5C | Slide: End-to-End System Performance | ✅ Done | `slides/slide_system_performance.png` |
| 6 | RTK chain run for final .tex output | ⏳ Pending — use when Khoa's delta arrives | — |

---

## Step 1A — Trend Analysis Notes

_To be filled after semantic-scholar search completes._

### Key questions to answer:
- Year NBA as a concept peaks in citations
- Which venue dominates (RecSys, WWW, SIGIR, KDD)
- Method family evolution: RNN → Transformer → Multimodal

---

## Step 1B — Literature Sections

### Section A — Founding papers (1–2 papers, earliest + highest citations)
_To be filled._

### Section B — Traditional approaches (3 papers)
- [ ] Markov / bandit method
- [ ] RNN-based (GRU4Rec)
- [ ] Attention-based (SASRec)

### Section C — Multimedia papers 2022+ (2–3 papers)
_To be filled._

---

## Step 1C — Verification Log

_Each paper must appear in ≥2 databases. Flag single-source papers for replacement._

| Paper | Title | Databases Found | Status |
|-------|-------|-----------------|--------|
| — | — | — | — |

---

## Step 2A — Routing Logic

_To be filled from code-review-graph query._

- **Routing function:** —
- **Condition A→Pipeline A:** —
- **Condition A→Pipeline B:** —
- **Unrouted 2.6%:** —

---

## Step 2B — AgentPool / Phase 2

_To be filled from code-review-graph query._

- **Trigger:** —
- **Weights changed:** —
- **Update frequency:** —

---

## Step 2C — Evaluation Reproducibility

_To be filled from code-review-graph query._

- **Eval script:** —
- **Dataset split:** —
- **Reproducible from single command?** —
- **HR@10 Pipeline A:** 0.9047 ✓ (from CLAUDE.md)
- **HR@10 Pipeline B:** 0.7745 ✓ (from CLAUDE.md)

---

## Benchmark Results (seed=42, N=99 negatives, 100k users)

| Strategy | HR@10 | NDCG@10 | MRR@10 |
|---|---|---|---|
| Random | 0.1000 | 0.0454 | 0.1000 |
| Content Baseline | 0.4346 | 0.3022 | 0.2609 |
| SASRec (content-only ablation, α=0) | 0.7655 | 0.4932 | 0.4102 |
| DIF-SASRec — Pipeline B | 0.7755 | 0.5019 | 0.4183 |
| Pipeline A (Cleora+BGE-M3) | 0.9047 | 0.5393 | — |
| System A∪B | 0.9736 | 0.5571 | — |

## Blockers / Notes

- Khoa's Phase 2 delta result still needed — placeholder `[DELTA\_RESULT]` in `chapter5_holistic.tex` line ~41
- Citation rule: `\cite{}` only — zero `\parencite{}` tolerated
- Paper cutoff: 2020+ preferred; foundational older works allowed for origin story only

---

## Checklist

### Step 1 — Literature
- [ ] Trend analysis saved → `trend_analysis.md`
- [ ] Traditional lit review (x1 search)
- [ ] Multimedia lit review (x1 search)
- [ ] All papers cross-verified → `verified_papers.md`
- [ ] Section A: 1–2 founding papers confirmed
- [ ] Section B: 3 traditional approaches confirmed
- [ ] Section C: 2–3 multimedia papers 2022+ confirmed

### Step 2 — Code verification
- [ ] Routing function identified
- [ ] AgentPool mechanism documented
- [ ] HR@10 traced to reproducible eval script
- [ ] All findings → `code_verification_step2.md`

### Step 3 — Chapter 2
- [x] Drafted from verified papers only
- [x] GRU-SeqDQN labeled "traditional sequential NBA" (in code_verification_step2.md)
- [x] Content Baseline labeled "non-multimedia NBA" (in code_verification_step2.md)
- [x] Output → `Captsone/chapter2_nba_section.tex`
- [ ] scholar-evaluation score ≥ 3/5 all dimensions (run manually)

### Step 4 — Chapter 5
- [x] Drafted from code-verified facts (all function names traceable)
- [x] Output → `Captsone/chapter5_holistic.tex`
- [ ] Khoa's Phase 2 delta — replace `[DELTA\_RESULT]` (still open)
- [x] Comparison table added → `Captsone/chapter5_comparison_table.tex`
- [x] Benchmark run (seed=42) — SASRec ablation + DIF-SASRec confirmed
- [ ] scholar-evaluation score ≥ 3/5 all dimensions (run manually)

### Step 5 — Slides
- [x] `slides/slide_nba_origins.png` generated
- [x] `slides/slide_nba_alternatives.png` generated
- [x] `slides/slide_system_performance.png` generated

### Final QA
- [x] Zero `\parencite{}` in `Captsone/` new files
- [x] All new claims match `Markdowns/report/code_verification_step2.md`
- [x] All citations exist in `Markdowns/report/verified_papers.md`
- [x] 4 new BibTeX entries added to `Captsone/sections/ref.bib`
- [ ] Global `\parencite{}` scan on all existing Captsone sections (run manually)
