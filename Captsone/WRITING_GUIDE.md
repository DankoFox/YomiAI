# LLM Writing Guide — Capstone Report

> **Purpose**: This document is the single source of truth for any LLM continuing this capstone report.  
> **Reference chapter**: Chapter 5 (Experiments and Evaluation) is the only fully written chapter. Treat it as the canonical style reference. Every remaining section must match its tone, structure, and LaTeX conventions exactly.  
> **Status**: Chapters 1–4 are empty stubs. Chapter 5 is complete. Chapters 6, 7, and the Appendix are empty stubs awaiting content.

---

## 1. Document Context

This is a Vietnamese university capstone report (12pt Times font, A4, double-spaced, numbered chapters). The system being reported is a **data platform** with three core modules:

- **Data Ingestion Module** — ingesting raw data from external sources
- **Data Visualization Module** — displaying processed data to users
- **Data Storage Module** — persisting and querying data at scale (MongoDB, Redis, FAISS)

Chapter 5 evaluates the platform's **book recommendation system** — a dual-mode pipeline combining Cleora co-purchase graph embeddings (Pipeline A) with a DIF-SASRec transformer (Pipeline B). Chapter 6 applies the **same platform** to an **air quality monitoring** use case to demonstrate generality.

---

## 2. Writing Style (derived from Chapter 5)

### 2.1 Voice and register
- Third-person impersonal throughout. Never use "we" or "our".
  - ✓ "The experiments are conducted on..."
  - ✓ "A sampled negative protocol is adopted..."
  - ✗ "We evaluated our system..."
- British spelling conventions where they appear (e.g., "normalised", "optimisation", "artefact", "neighbourhood").
- Present tense for general facts; past tense for specific experimental runs.
  - ✓ "Table 5.1 reports the results." / "The evaluation was conducted on 100,000 users."

### 2.2 Sentence structure
- Short declarative sentences. Avoid subordinate clauses stacked more than two deep.
- Each paragraph opens with a topic sentence that states the conclusion, then provides supporting evidence.
- Use transitional phrases between paragraphs: "Several observations follow.", "The key finding is...", "This result is consistent with...".

### 2.3 Numbers and metrics
- **Always** use 4 decimal places for evaluation metrics: `0.7745`, not `0.77` or `77.45%`.
- Thousands separator: use LaTeX `{,}` inside math or table cells → `100{,}000`.
- Bold the best metric value in each table column.
- When stating improvements, give both absolute and relative: "HR@10 improved from 0.4346 to 0.9736, a 124% improvement."
- Latency values: 2 decimal places in milliseconds (e.g., `612.19 ms`).

### 2.4 Chapter introduction
Every chapter begins with an italicized overview sentence immediately after `\chapter{}`, before the first `\section{}`. This is already in `main.tex`; do not duplicate it inside the section files.

---

## 3. LaTeX Conventions

### 3.1 Structure
```latex
\section{Section Title}
\label{sec:short_identifier}

\subsection{Subsection Title}

\paragraph{Bold paragraph heading —}
Body text continues on the same line.
```

- Labels: `sec:snake_case`, `tab:snake_case`, `fig:snake_case`
- No blank line between `\paragraph{}` entries in a list.
- Use `\label{sec:...}` on every `\section` and `\subsection` that is cross-referenced.

### 3.2 Tables
```latex
\begin{table}[H]
\centering
\caption{Descriptive caption ending with context (N users, protocol).}
\label{tab:identifier}
\begin{tabular}{lrr}
\hline
\textbf{Column 1} & \textbf{Col 2} & \textbf{Col 3} \\
\hline
Row data          & value          & \textbf{best} \\
\hline
\end{tabular}
\end{table}
```

Rules:
- Always `[H]` placement.
- Caption **above** the table (`\caption` before `\begin{tabular}`).
- `\hline` at top, after header row, and at bottom only. No vertical lines.
- Column alignment: `l` for text, `r` for numbers, `c` for short labels.
- Every table is followed immediately by 1–4 sentences of prose commentary pointing to the most important finding. Never leave a table without interpretation.

### 3.3 Figures
```latex
\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{images/chapterX/fig_snake_case_name}
\caption{Full sentence caption. (a) Description of panel a. (b) Description of panel b. Key numeric takeaway stated here.}
\label{fig:identifier}
\end{figure}
```

Rules:
- Always `[H]` placement.
- No file extension in `\includegraphics{}` path.
- Image path format: `images/chapter6/fig_xxx`, `images/chapter7/fig_xxx`
- Width: `\textwidth` for full-width plots, `0.85\textwidth` or `0.9\textwidth` for narrower plots.
- Caption **below** the figure (`\caption` after `\includegraphics`).
- Multi-panel figures: describe each panel (a), (b), etc. in the caption.
- Every figure is referenced in the prose **before** it appears: "Figure~\ref{fig:xxx} shows..."

### 3.4 Citations
- Use `\cite{key}` inline, e.g., `~\cite{ni2019justifying}`.
- Non-breaking space `~` before `\cite`.
- Add new entries to `sections/ref.bib` using the existing format (inproceedings/article, all fields).
- Citation keys follow the pattern `authorYYYYkeyword` (e.g., `chen2024bge`).

### 3.5 Cross-references
- Always use `\ref{}` (not hardcoded numbers): `Table~\ref{tab:xxx}`, `Figure~\ref{fig:xxx}`, `Section~\ref{sec:xxx}`.
- Non-breaking space `~` before `\ref`.

### 3.6 Lists
```latex
\begin{itemize}
    \item \textbf{Label}: Description.
\end{itemize}

\begin{enumerate}
    \item Step one.
\end{enumerate}
```

Use `\itemize` for unordered observations; `\enumerate` for ordered steps or ranked results.

### 3.7 Math
- Inline math: `$x$`, `$N = 99$`, `$\tau = 0.3$`
- Display math: `\begin{equation}...\end{equation}` with `\label{eq:xxx}`
- Vectors/matrices: bold upright `\mathbf{x}`
- Set notation: `$A \cup B$`, `$A \cap B$`

---

## 4. Section-by-Section Content Briefs

### Chapter 6 — Application (Air Quality)

This chapter demonstrates the platform's generality by applying the data ingestion, preparation, visualization, and retrieval modules to an air quality monitoring domain. Every subsection should parallel the structure used in Chapter 5: state the goal → describe the method → report the result → interpret it.

#### 6.1 AirQualityProblem (`6.1.AirQualityProblem.tex`)
**Current content**: Just `\section{Problem Statement}` with no body.  
**Goal**: Motivate the air quality use case.  
**Cover**:
- Why air quality monitoring matters (health impact, urban growth, regulatory context).
- The core problem: heterogeneous data sources, high-frequency sensor streams, need for real-time visualization and historical retrieval.
- One paragraph linking back to the platform's three modules (ingestion, visualization, storage) and explaining why this domain exercises all of them.
- Do NOT yet describe data formats — that belongs in 6.2.

**Length**: ~300–400 words, no tables or figures required.

#### 6.2 DataDescription (`6.2.DataDescription.tex`)
**Goal**: Describe the air quality dataset.  
**Cover**:
- Data source(s): sensor type, geographic coverage, time range.
- Key statistics in a `\begin{table}[H]` (same style as Table 5.1 in Ch. 5): number of stations, sampling frequency, features (PM2.5, PM10, NO2, CO2, temperature, humidity — use whatever applies), date range, total records.
- Feature schema: a table listing field name, type, unit, description.
- A brief note on data quality issues to be addressed in 6.4 (mention them now, detail them later).

**Length**: ~250–350 words, 1–2 tables.

#### 6.3 DataIngestion (`6.3.DataIngestion.tex`)
**Goal**: Show how the Data Ingestion Module (from Chapter 4.2) handles the air quality data stream.  
**Cover**:
- Source → ingestion pipeline: how raw sensor data enters the system (API polling, MQTT, CSV upload — whichever applies).
- The pipeline steps: schema validation, timestamp normalization, duplicate detection.
- A table listing ingestion throughput / latency before and after the Ch. 4.2 improvements.
- How data lands in the storage layer (MongoDB collection schema, Redis cache keys).
- Cross-reference Chapter 4 improvements where relevant: e.g., "The batching mechanism introduced in Section~\ref{sec:xxx} reduces..."

**Length**: ~400–500 words, 1 table, optionally 1 figure (pipeline diagram or latency chart).

#### 6.4 DataPreparation (`6.4.DataPreparation.tex`)
**Goal**: Cleaning and feature engineering steps applied to the raw ingested data.  
**Cover**:
- Missing value strategy: interpolation, forward-fill, or removal — with justification.
- Outlier detection: statistical method (IQR, z-score) and threshold used.
- Normalization/scaling if applied.
- Feature engineering: rolling averages, AQI computation formula (if used), derived features.
- A table showing data quality before and after preparation (% missing, outlier rate, record count).

**Length**: ~350–450 words, 1 table.

#### 6.5 DataVisualization (`6.5.DataVisualization.tex`)
**Goal**: Demonstrate the Data Visualization Module (Chapter 4.3) applied to air quality data.  
**Cover**:
- What visualizations are produced: time-series charts, geographic heatmaps, pollutant comparisons.
- Reference actual screenshots (figures) from the application UI: `images/chapter6/fig_dashboard_xxx`.
- Describe 2–3 specific UI components and what insight they surface.
- One paragraph on user-facing performance: dashboard load time, chart rendering latency (cross-reference latency improvements from Ch. 4.3).

**Length**: ~300–400 words, 2–3 figures.

#### 6.6 Result (`6.6.Result.tex`)
**Goal**: Report the end-to-end outcome of applying the platform to the air quality domain.  
**Cover**:
- A summary table of system-level metrics: data ingestion rate, pipeline latency (E2E), query response time, storage footprint.
- Comparison to baseline (before the Chapter 4 improvements) if measurable.
- 2–3 key observations, formatted the same way as Section 5.4 (paragraph → finding → interpretation).
- A qualitative note on data insights discovered (e.g., pollution peaks at certain hours, sensor drift patterns).

**Length**: ~350–450 words, 1–2 tables, optionally 1 figure.

#### 6.7 DataRetrieval (`6.7.DataRetrieval.tex`)
**Goal**: Describe how users query historical air quality data through the platform.  
**Cover**:
- Query types supported: time-range queries, station-specific queries, aggregation queries (hourly/daily averages).
- The storage and indexing strategy enabling fast retrieval (MongoDB indexes, Redis caching — from Chapter 4.4).
- Retrieval latency: a table with P50/P95 latency for each query type (same format as Table 5.3 in Ch. 5).
- Caching effectiveness: cache hit rate and latency improvement.

**Length**: ~300–400 words, 1 table.

#### 6.8 OtherFunctions (`6.8.OtherFunctions.tex`)
**Goal**: Describe additional system capabilities not covered above.  
**Cover** (pick whichever are implemented):
- Alert/notification system (threshold breaches for PM2.5 etc.)
- Data export (CSV/JSON download)
- User authentication / role-based access
- System monitoring / health dashboard
- API endpoint documentation (brief, not exhaustive)

**Length**: ~200–300 words; use `\subsection{}` per feature. No tables required unless comparing before/after.

---

### Chapter 7 — Conclusion (`7.Conclusion/summary.tex`)

**Goal**: Wrap up the entire capstone. The conclusion must reference **specific numbers** from Chapter 5 and Chapter 6, not vague claims.  
**Structure** (use `\section{}` headings within the single file):

#### 7.1 Summary of Achievements
- One paragraph per chapter (Chapters 2–6), each opening with the chapter's core contribution and ending with the key result.
- For Chapter 5: state HR@10 = 0.9736, 18.6× latency improvement, multilingual capability.
- For Chapter 6: state the air quality application key metrics from 6.6.
- Do not simply restate the chapter intro sentences from `main.tex`.

#### 7.2 Evaluation of Objectives
- Return to the goals stated in Chapter 1 (Section 1.2). For each goal, state whether it was met and cite the evidence (table number, metric value).
- Use a table with columns: Objective | Status (Met / Partially Met) | Evidence.

#### 7.3 Limitations
- 3–5 bullet-point limitations, derived from the error analysis in Section 5.4.3 and any shortcomings identified in Chapter 6.
- Be specific: "The content veto threshold τ = 0.3 causes over-filtering for users with sparse histories (Section~\ref{sec:qualitative})."

#### 7.4 Future Work
- 3–5 concrete, actionable directions. Each should reference a specific limitation or observed gap.
- Examples: relaxing the veto for cold-start users; extending the Cleora index from 375k to the full 3M catalogue; adding real-time anomaly detection to the air quality pipeline.

**Length**: ~600–800 words total.

---

### Appendix

#### appendix.tex
Typical content:
- System deployment diagrams (architecture diagrams, Docker-compose service map).
- Full hyperparameter tables if not included in Chapter 5.
- Raw data samples (show a few rows of the air quality dataset).
- API endpoint reference table (endpoint, method, parameters, response).
Use `\section{...}` within `\appendix\chapter{Appendix}`. Figure labels in appendix: `fig:app_xxx`.

#### plan.tex
Typically a Gantt-chart or workload table showing the team's task allocation and timeline. Use a `longtable` or `tabularx` for the Gantt layout (same style as existing tables).

---

## 5. Consistency Checklist (before finalizing any section)

- [ ] All figures referenced in prose before they appear.
- [ ] All tables followed by prose commentary.
- [ ] All `\label{}` defined and all cross-references use `\ref{}`, not hard-coded numbers.
- [ ] Numbers: 4 decimal places for metrics, `{,}` for thousands.
- [ ] Best values in tables are `\textbf{...}`.
- [ ] Voice is third-person impersonal throughout.
- [ ] British spelling used consistently.
- [ ] All new citations added to `sections/ref.bib` before using `\cite{}`.
- [ ] Image paths follow `images/chapterX/fig_name` (no extension).
- [ ] Chapter conclusion section (`X.X ChapterConclusion.tex`) summarizes all findings with specific numbers — no vague statements.

---

## 6. What NOT to do

- Do not add a "Related Work" section inside Chapters 6 or 7 — that belongs in Chapter 2.
- Do not repeat the system architecture description in Chapter 6 — say "as described in Chapter 4" and cross-reference.
- Do not write `\chapter{}` declarations in section files — those are in `main.tex` only.
- Do not use `\textbf{}` for emphasis of arbitrary phrases — reserve it for best metric values in tables and the single most important finding per section.
- Do not write in bullet points in prose — use `\itemize` only for genuinely list-like content (failure modes, feature lists), not as a substitute for paragraphs.
- Do not include placeholder text like "TODO" or "[to be filled]" in any `.tex` file.
