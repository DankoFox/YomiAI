# LaTeX Review — Action Plan & Progress Tracker

Generated from `/review-latex` audit of all 18 `.tex` files in `paper/` and `IAAAconference(Latex)/`.
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

- [ ] **Float placement specifier inconsistency** — All tables use `[H]` except `dataset_stats.tex` which uses `[t]`. Standardize. For most conference venues `[H]` is disallowed by the style file; switch to `[t]` or `[htb]` throughout.
- [ ] **`dataset_stats.tex` lines 9–10** — Large integers use plain commas (`29,475,453`). Replace with `{,}` or `\num{}` (siunitx) to match the convention used in `complementarity.tex`.
- [ ] **`04_methodology.tex` subsubsection titles** — Literal Unicode em-dash `—` should be `---`; trailing `.` inside `\subsubsection{}` argument produces a double period. Fix both.
- [ ] **`03_system_overview.tex`** — `\resizebox{1.25\textwidth}{!}` inside `\makebox[\textwidth][c]` overflows into the margin on two-column layouts. Reduce or add a conditional guard.
- [ ] **`03_system_overview.tex`** — `\colorbox{blue!4}{\strut ...}` inside `\caption` is fragile under `hyperref`. Wrap with `\protect`.
- [ ] **`complementarity.tex`** — `~~` double non-breaking space used for column alignment. Replace with siunitx `S` columns or a two-sub-column layout.
- [ ] **`06_results.tex`** — `$<$25\,ms` produces inconsistent spacing. Use `{<}\,25\,ms` or `$<\!25$\,ms`.
- [ ] **`02_related_work.tex`** — `\textit{(i)~full sentence...}` italicises the full clause instead of just the label. Move the closing brace to immediately after the label character.
- [ ] **`00_abstract.tex`** — `\keywords{}` is inside `\begin{abstract}...\end{abstract}`. Most classes (`acmart`, `IEEEtran`) require it outside; move it after `\end{abstract}`.
- [ ] **`04_methodology.tex`** — `$\text{BGE-M3}(q_t)$` mixes `\text{}` and math inconsistently across the paper. Define `\newcommand{\bge}{\mathrm{BGE\text{-}M3}}` in the preamble and use it uniformly.
- [ ] **`04_methodology.tex`** — `\begin{equation*}` inside an `enumerate` item may not align with list indentation. Verify rendered output or switch to `\[ \]` with explicit spacing.
- [ ] **`latency.tex`** — `$\sim$` used as an approximation sign in running text. Use `\approx` inside math mode (`$\approx 900$\,ms`) for consistent style.
- [ ] **`06_results.tex`** — Verify all unit-value pairs use thin-space `\,` consistently (e.g., `1\,127\,ms`, `1.18\,GB`).

---

## Phase 5 — Editorial Cleanup (remove before submission)

- [ ] **`02_related_work.tex`** — Remove all `% CHANGED:`, `% NEW:`, `% KEPT:` revision comment lines (lines 4, 9, 54, 82, 99, 117). These expose internal revision history.
- [ ] **`00_abstract.tex`** — Remove `% Target:`, `% Cover:`, and stray `%` comment lines.
- [ ] **`06_results.tex` line 140** — Remove or uncomment the stray `\clearpage`.
- [ ] **`latency.tex` caption** — Replace internal identifier `run\_021` with a reproducible description (e.g., "30 observations, warm-cache benchmark").
- [ ] **`latency.tex` below-table note** — The `\footnotesize` prose block appended after `\end{tabular}` should be a formal `\footnote{}` or moved to the paper body.
- [ ] **`07_conclusion.tex`** — `\textbf{0.7886}` bolds a metric value in running prose; per convention, bold is reserved for table entries. Remove `\textbf{}`.

---

## Phase 6 — Tone, Structure & Register

- [ ] **`04_methodology.tex` subsubsection titles** — Rename "People Also Buy" → "Behavioral Candidate Retrieval" and "You Might Like" → "Sequential Intent Scoring" (or equivalent neutral academic terms).
- [ ] **`01_introduction.tex` §3 bullet** — Fix broken prose: "bridging both modes  temporal weighting" — insert missing word/connector (e.g., "bridging both modes via temporal weighting").
- [ ] **`07_conclusion.tex`** — Add a closing sentence anchoring the paper's broader significance after the future-work list.
- [ ] **`07_conclusion.tex`** — Replace colloquial terms: "rescues" → "recovers", "mines" → "extracts", "warm-path" → define or use standard latency-tier term, "grounding" → "conditioning".
- [ ] **`01_introduction.tex`** — Replace informal phrases: "crowd wisdom" → "aggregated user behaviour", "Users who know what they want" → "Users with explicit information needs", "passive browsers" → "users engaged in exploratory browsing".
- [ ] **`06_results.tex` / `main.tex`** — Standardize spelling to American English throughout: "characterisation" → "characterization", "artefact" → "artifact" (appears in §6.4 and §6.5).
- [ ] **`06_results.tex`** — "10+ concurrent users" → "more than 10 concurrent users" or "$\geq 10$ concurrent users".
- [ ] **`06_results.tex`** — "near-random results" → "results approximating the random baseline".
- [ ] **`03_system_overview.tex`** — Add a closing/transition sentence after `\subsection{User Profile}` linking the profile back to the two pipelines.
- [ ] **`03_system_overview.tex`** — "exposes a REST API" → "provides a RESTful API".
- [ ] **`02_related_work.tex` lines 119–135** — The Summary subsection repeats each prior subsection nearly verbatim. Rewrite to add synthesis across the literature rather than restating.
- [ ] **`main.tex` §6.2** — "ten times harder" → "an order of magnitude more discriminative" (describing the 999-negative protocol).
- [ ] **`00_abstract.tex`** — "failing to exploit" → "unable to leverage"; fix vague pronoun "It combines" → use explicit subject.
- [ ] **`07_conclusion.tex`** — "NBA" acronym re-used without expansion; expand on first use in this section.

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
