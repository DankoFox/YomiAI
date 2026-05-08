# Capstone Thesis — Phased Fix Plan

## Phase 1 — Critical Factual Errors (execute first)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `sections/abstract.tex` line 20 | "applied to an air quality monitoring use case" — Chapter 6 is the book app, not air quality | Remove that sentence |
| 2 | `sections/1.Introduction/1.3.Scope.tex` line 14 | Inclusion mentions "air quality monitoring dataset" | Change to "book recommendation application" |
| 3 | `sections/1.Introduction/1.3.Scope.tex` line 23 | Exclusion says "Online learning … not implemented" — FALSE; `POST /interact` fires DIF-SASRec gradient steps | Rewrite: system implements per-session online fine-tuning; exclusion is production-scale RL/bandit training |
| 4 | `sections/1.Introduction/1.4.Thesis-structure.tex` line 21 | Chapter 6 described as "air quality monitoring use case" | Replace with correct description of deployed book app |
| 5 | `sections/1.Introduction/1.5.Conclusion.tex` line 7 | Mentions "air quality case study" as a goal | Replace with "deployed interactive application" |
| 6 | `sections/5.ExperimentsEvaluation/5.3.EndToEndEvaluation.tex` | Multiseed seed=42 shows HR@10=0.7262 but main results show 0.7745 — unexplained | Add a sentence below the table explaining the checkpoint difference |
| 7 | `sections/2.Theory/2.3.Existing-solutions.tex` line 32 | GRU-SeqDQN HR@10=0.0823 but main results Table 1 shows 0.1031 | Fix to 0.1031 (canonical result) |
| 8 | `sections/3.SystemAnalysis/3.4.ChapterConclusion.tex` line 9 | Same 0.0823 vs 0.1031 mismatch | Fix to 0.1031 |
| 9 | `sections/7.Conclusion/summary.tex` line 8 | Same 0.0823 vs 0.1031 mismatch | Fix to 0.1031 |

---

## Phase 2 — Empty / Stub Sections

| # | File | Issue | Fix |
|---|------|-------|-----|
| 10 | `sections/related_work.tex` | Only `\section{Related Works}` — empty | Write ~1 page: commercial systems (Amazon, Goodreads) + academic multimodal rec |
| 11 | `sections/list-of-abbreviations.tex` | Empty longtable | Add ~22 entries (BGE-M3, RRF, HNSW, FAISS, NLLB, DIF-SASRec, GRU, DQN, HR, NDCG, MRR, ANN, BM25, CLIP, API, LRU, CTR, NBA, SPA, JSON, SASRec, BERT) |
| 12 | `sections/appendixes/appendix.tex` | Only `\appendix\chapter{Appendix}` | Add API endpoint reference table + hyperparameter table |

---

## Phase 3 — Thin Content Check

| # | File | Check |
|---|------|-------|
| 13 | `sections/2.Theory/2.4.ChapterConclusion.tex` | Already good — no action needed |
| 14 | `sections/3.SystemAnalysis/3.4.ChapterConclusion.tex` | Good — no action needed |
| 15 | `sections/4.ProposedSolutions/4.5.ChapterConclusion.tex` | Good — no action needed |
| 16 | `sections/4.ProposedSolutions/4.2.ImprovementsInDataIngestionModule.tex` | Check for thin paragraphs |
| 17 | `sections/4.ProposedSolutions/4.3.ImprovementsInDataVisualizationModule.tex` | Check for thin paragraphs |

---

## Phase 4 — Minor Wording

| # | File | Fix |
|---|------|-----|
| 18 | `main.tex` line 102 | `list-of-abbreviations` is commented out — uncomment after Phase 2 fills it |
| 19 | `sections/5.ExperimentsEvaluation/5.3.EndToEndEvaluation.tex` | Add brief note that GRU-SeqDQN was evaluated on the same 100k users, $N=99$ protocol |

---

## Status

- [x] Phase 1 — done (9 fixes: abstract, 1.2, 1.3, 1.4, 1.5, 5.3 seed discrepancy, GRU-SeqDQN number x3)
- [x] Phase 2 — done (related_work.tex ~1.5p written + included in main.tex; list-of-abbreviations 23 entries + uncommented; appendix 2 chapters: API table + hyperparameter table; 4 new bib entries added)
- [x] Phase 3 — done (4.2, 4.3, ch conclusions all substantive — no action needed)
- [x] Phase 4 — done (list-of-abbreviations uncommented in main.tex; 1.2.Goals goal-5 wording; summary.tex objectives table row updated)
