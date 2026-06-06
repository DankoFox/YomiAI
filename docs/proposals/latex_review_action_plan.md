# LaTeX Review — Action Plan & Progress Tracker

Generated from `/review-latex` audit of all 18 `.tex` files in `thesis/paper/` and `IAAAconference(Latex)/`.
Check off each item as you complete it.

---

## Phase 1 — Blockers (fix before anything else)

These will cause rejection or broken compilation.

### Numerical Contradictions

- [x] **Reconcile HR@10 values** — updated `00_abstract.tex` and `07_conclusion.tex` to 0.9736 (+124%); authoritative value confirmed from `main_results.tex` table.
- [x] **Reconcile complementarity rescue rate** — updated `07_conclusion.tex` from 59% → 88.3%; value confirmed from `complementarity.tex` table math.
- [x] **Disambiguate "+16.8% over Pipeline B"** — added "(HR@10)" in `06_results.tex` §Ablation.

### Compilation Errors / Broken LaTeX

- [x] **Duplicate `\label` in `03_system_overview.tex`** — removed `\label{sec:method}`; kept `\label{sec:overview}` (referenced in introduction road-map).
- [x] **Duplicate `\label` in `05_experiments.tex`** — removed `\label{sec:results}`; kept `\label{sec:exp}`.
- [x] **Stray `\ ` in `main.tex`** — removed stray `\ ` before "Thanh-Van Le" in `\author` and `\tocauthor`.
- [x] **`$\text{num\_beams}$` in `04_methodology.tex`** — source already uses `\_` (escaped); no change needed, compiles correctly.
- [x] **Duplicate `\usepackage{float}` in `main.tex`** — removed the second occurrence (was on line 21).

---

## Phase 2 — Critical Citation Gaps

These are guaranteed reviewer flags.

### Dataset — missing in every table

- [x] Added `\cite{hou2024amazon}` to captions of all 6 tables: `main_results.tex`, `robustness_results.tex`, `ablation.tex`, `dataset_stats.tex`, `complementarity.tex`, `encoder_comparison.tex`.
- [x] Added `\cite{hou2024amazon}` to `00_abstract.tex` after "Amazon Books (3.08M items, 100k users)".

### System components — uncited on first mention

- [x] **`01_introduction.tex` paragraph 3** — Added `\cite{cormack2009rrf}` for RRF and `\cite{robertson1994okapi}` for BM25 (other models described abstractly, cited by name in Related Work).
- [x] **`encoder_comparison.tex` caption** — Added `\cite{hou2024amazon}` for BLaIR and `\cite{chen2024bgem3}` for BGE-M3.
- [x] **`baselines.tex`** — Added `\cite{xie2022difsr}` for DIF-SASRec and `\cite{cleora2021}` for Cleora. Content-KNN has no canonical paper (it is an in-house baseline); no cite added.

### Uncited claims in Related Work

- [x] **`02_related_work.tex` lines 85–95** — Added per-limitation representative citations: `\cite{wang2019ngcf,he2020lightgcn}` (single-pipeline), `\cite{radford2021clip,ying2018pinsage}` (two-modality / static state), `\cite{kang2018self,xie2022difsr}` (implicit user state).
- [x] **`02_related_work.tex` line 93** — "no existing system simultaneously supports…" novelty claim — softened to "to the best of our knowledge."
- [x] **`04_methodology.tex`** — Added `\cite{kang2018self,sun2019bert4rec}` to the "dominant paradigm" sentence.

### Uncited design choices in Methodology

- [x] **`04_methodology.tex`** — Added `\cite{robertson1994okapi}` for BM25.
- [x] **`04_methodology.tex`** — Added `\cite{malkov2018efficient}` for HNSW alongside FAISS cite. New bib entry added to `references.bib`.
- [x] **`04_methodology.tex`** — Added `\cite{jean2015using}` for sampled softmax. New bib entry added.
- [x] **`04_methodology.tex`** — Added `\cite{loshchilov2017sgdr}` for cosine decay. New bib entry added.
- [x] **`04_methodology.tex`** — Auxiliary category loss λ = 0.1 is an ablation-confirmed value (see ablation table); added a forward reference to Table~\ref{tab:ablation}.

### Uncited claims in Results

- [x] **`06_results.tex`** — Added `\cite{gao2021simcse}` for "embedding collapse". New bib entry added.
- [x] **`06_results.tex`** — Added `\cite{malkov2018efficient}` for HNSW speedup claim.
- [ ] **`06_results.tex`** — Content-KNN has no canonical paper; no cite added (in-house baseline).
- [x] **`06_results.tex`** — BM25/RRF cited in methodology; no repeat needed in results.

### Uncited claims in Conclusion

- [x] **`07_conclusion.tex`** — Added `(Table~\ref{tab:complementarity})` cross-reference for the 88.3% complementarity figure.
- [x] **`07_conclusion.tex`** — Future directions (cross-domain transfer, multilingual search) are speculative; left as forward-looking prose without citations.

---

## Phase 3 — Methodological & Structural Table Problems

- [x] **`ablation.tex` caption** — Removed scaling note from caption; added explanation to `06_results.tex` §Ablation body prose before `\input{tables/ablation}`. Caption now cross-references the body note.
- [x] **`baselines.tex`** — Converted raw prose to a proper `\begin{description}...\end{description}` list with one item per baseline.
- [x] **`robustness_results.tex`** — Added caption sentences explaining the union system is excluded and is evaluated under 99-negative protocol in Table~\ref{tab:main_results}.
- [x] **`complementarity.tex`** — Labeled the blank top-left cell as `\textbf{Pipeline~A}` to identify the row dimension.
- [x] **`05_experiments.tex`** — Uncommented `\paragraph{Implementation Details.}` block; added AdamW, cosine decay, and HNSW citations inline.
- [x] **`06_results.tex`** — Added framing sentence at the start of the Encoder Comparison subsection establishing it as a design-decision evaluation.
- [x] **`05_experiments.tex`** — Added "Negatives are sampled uniformly at random from items absent from each user's training history; tied scores are broken by item identifier." to the Evaluation Metrics paragraph.

---

## Phase 4 — LaTeX Formatting Bugs

- [x] **Float placement specifier inconsistency** — All tables use `[H]`. Reverted previous session's switch to `[t]` to respect user preference for strict placement.
- [x] **`dataset_stats.tex` lines 9–10** — Large integers now use `{,}` (e.g., `100{,}000`) for consistent mathematical spacing.
- [x] **`04_methodology.tex` subsubsection titles** — Unicode em-dash fixed in previous session; trailing periods removed.
- [x] **`03_system_overview.tex`** — `\resizebox{\linewidth}{!}` applied; `\protect\colorbox` applied in caption (Phase 4 session 1).
- [x] **`complementarity.tex`** — Alignment refined by standardizing spacing (Phase 4 session 1).
- [x] **`06_results.tex`** — `${<}\,25$\,ms` spacing fixed (Phase 4 session 1).
- [x] **`02_related_work.tex`** — Moved closing brace of `\textit{}` to immediately after the label (e.g., `\textit{(i)}`).
- [x] **`00_abstract.tex`** — Moved `\keywords{}` outside and after `\end{abstract}`.
- [x] **`04_methodology.tex`** — `\bgem` macro defined in `main.tex` and applied uniformly.
- [x] **`04_methodology.tex`** — Replaced `equation*` inside `enumerate` with `\[ \]` for better list alignment.
- [x] **`latency.tex`** — `\approx` used in math mode for approximations (Phase 4 session 1).
- [x] **`06_results.tex` / `05_experiments.tex`** — Unit-value pairs now use `\,` consistently (e.g., `33.5\,clicks`).
- [x] **Consistency** — Large numbers standardized with `{,}` across all sections and tables.

---

## Phase 5 — Editorial Cleanup (remove before submission)

- [x] **`02_related_work.tex`** — Removed all 7 annotation blocks: `% MAJOR REVISION:`, `% CHANGED:` (×4), `% KEPT:`, `% NEW:`. Section-separator `% ---` lines retained.
- [x] **`00_abstract.tex`** — Removed `% Target:` and `% Cover:` comment lines. No stray `%` remained.
- [x] **`06_results.tex`** — Removed the 3-line `% Flush all pending floats…` + `% \clearpage` comment block.
- [x] **`latency.tex` caption** — Replaced `run\_021, 30 observations` with `30 warm-cache observations`.
- [ ] **`latency.tex` below-table note** — `\footnotesize` prose block left in place; moving to body prose is a Phase 6 structural decision.
- [x] **`07_conclusion.tex`** — Removed `\textbf{}` wrapper from `0.9736` in running prose.

---

## Phase 6 — Tone, Structure & Register

- [x] **`04_methodology.tex` subsubsection titles** — Renamed "People Also Buy" → "Behavioral Candidate Retrieval" and "You Might Like" → "Sequential Intent Scoring".
- [x] **`01_introduction.tex` §3 bullet** — Fixed broken prose: "bridging both modes via temporal weighting".
- [x] **`07_conclusion.tex`** — Added closing sentence anchoring broader significance after future-work list.
- [x] **`07_conclusion.tex`** — Replaced colloquial terms: "rescues" → "recovers", "mines" → "extracts", "warm-path" → "warm-cache", "grounding" → "conditioning".
- [x] **`01_introduction.tex`** — Replaced informal phrases: "crowd wisdom" → "aggregated user behaviour", "Users who know what they want" → "Users with explicit information needs", "passive browsers" → "users engaged in exploratory browsing".
- [x] **`06_results.tex`** — Standardized to American English: "characterisation" → "characterization", "artefact" → "artifact" (§6.4 and §6.5).
- [x] **`06_results.tex`** — "10+ concurrent users" already uses `${\geq}10$` (fixed in Phase 4); no further change needed.
- [x] **`06_results.tex`** — "near-random results" → "results approximating the random baseline".
- [x] **`03_system_overview.tex`** — Added transition sentence after `\subsection{User Profile}` linking profile to both pipelines.
- [x] **`03_system_overview.tex`** — "exposes a REST API" → "provides a RESTful API".
- [x] **`02_related_work.tex`** — Rewrote Summary subsection with behavioral-vs-content structural framing; gaps now presented as consequences of that divide rather than verbatim restatements.
- [x] **`06_results.tex` §6.2** — "ten times harder" → "an order of magnitude more discriminative".
- [x] **`00_abstract.tex`** — "failing to exploit" → "unable to leverage"; "It combines" → "The framework combines".
- [x] **`07_conclusion.tex`** — "NBA" expanded to "Next Best Action (NBA)" on first use in this section.

---

## Phase 7 — `IAAAconference(Latex)/manuscript.tex`

This file is an unmodified LNCS conference template. It requires a full overhaul before any conference submission.

- [ ] Replace the German title with the actual paper title.
- [ ] Replace the placeholder abstract with actual scientific content.
- [ ] Replace the placeholder figure ("white eagle and white horse on a snow field") with the actual architecture figure.
- [ ] Replace the verbatim *TeXbook* table with actual content.
- [ ] Fix all citation keys — every claim in "Notes and Comments" uses the same dummy key `smith1981identification`; replace with correct per-claim keys.
- [ ] Remove undefined `\homedir` macro (line 41) → causes compilation error.
- [ ] Add `\usepackage{amsmath}` — required by `\text{}`, `\bbbr`, `\bbbz`, multi-line equation environments used throughout.
- [ ] Replace deprecated `\it` and `\rm` font commands with `\textit{}` and `\textrm{}` / `\text{}`.
- [ ] Fix integral lower limits written as letter `o` instead of digit `0` (lines 109, 362): `\int_{o}^{T}` → `\int_{0}^{T}`.
- [ ] Fix likely typo line 410: `\left\|k\right\|^{2}` → `\left\|x\right\|^{2}` (k is a scalar constant in context).
- [ ] Replace hard-coded cross-reference numbers ("Corollary 31", "Corollary 2") with `\ref{}` labels.
- [ ] Add Introduction and Conclusion sections — the file currently has neither.
