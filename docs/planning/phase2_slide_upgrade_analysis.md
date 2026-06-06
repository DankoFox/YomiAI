# Senior Academic Reviewer: Defense Slide Architecture — Phase 2 Upgrade Analysis
## Version 3.0 — Grounded in Actual PDF Content

---

## Section 1 — Confirmed Staleness Audit Table

| Slide | Title | Status | One-line reason |
|:---:|---|:---:|---|
| 1 | Title | ✅ | Still valid; same students and advisor. |
| 2 | Table of Contents | ✅ | Structure is preserved but section contents are updated. |
| 3 | Section 1 divider | ✅ | Framing divider. |
| 4 | Project Objective | ✅ | Still valid high-level goals. |
| 5 | Project Scope | 🔴 RETIRE | Phase 1 limitations (English only, frozen encoders) are resolved in Phase 2. |
| 6 | Section 2 divider | ✅ | Framing divider. |
| 7 | The Problem | ✅ | Market and failure modes remain relevant. |
| 8 | NBA System Concept | ✅ | Architecture-agnostic concept remains valid. |
| 9 | Why Multimodal | 🟡 REFRAME | Data insight is true, but "Inside/Outside" misses the Cleora/Graph dimension. |
| 10 | Section 3 divider | ✅ | Framing divider. |
| 11 | Contrastive Learning | ✅ | BGE-M3 is also contrastively trained. |
| 12 | Encoder Arch: BLaIR | 🔴 RETIRE | BLaIR is replaced by BGE-M3 (Multilingual). |
| 13 | Encoder Arch: BLaIR (diagram) | 🔴 RETIRE | References obsolete model. |
| 14 | Encoder Arch: CLIP | 🟡 REFRAME | CLIP is now part of the visual search/profile, not the primary text/item matching. |
| 15 | Encoder Arch: CLIP (diagram) | 🟡 REFRAME | Keep only as visual search component documentation. |
| 16 | Fusion Strategies Comparison | 🔴 RETIRE | Phase 2 uses a dual-pipeline union, not simple Late Fusion of BLaIR+CLIP. |
| 17 | Late Fusion | 🔴 RETIRE | Equation uses BLaIR and a fixed $\beta$ that is now obsolete. |
| 18 | Section 4 divider | ✅ | Framing divider. |
| 19 | Dataset: Amazon Reviews 2023 | 🟡 UPDATE | Scale increased from 38K books to 3M catalogue items. |
| 20 | Text Length Distributions | 🔴 UPDATE | BGE-M3 token limits and optimization (cap=64) supersede BLaIR's 512 limit. |
| 21 | Multimodal Asymmetry | 🟡 PARTIALLY VALID | Data observation is true, but Phase 1 fusion gain (+12.7%) is obsolete. |
| 22 | EDA Conclusion | 🟡 REFRAME | Must include Behavioral Graph (Cleora) as a core pillar. |
| 23 | Section 5 divider | ✅ | Framing divider. |
| 24 | Baselines: BLaIR wins | 🔴 FULL REPLACE | Phase 1 encoder benchmarks are irrelevant; need Phase 2 end-to-end results. |
| 25 | Visual Signal: CLIP Standalone | 🔴 RETIRE | CLIP-only retrieval metrics are obsolete. |
| 26 | Multimodal Fusion: BLaIR+CLIP | 🔴 RETIRE | Replaced by Cleora+BGE-M3+DIF-SASRec union results. |
| 27 | Final Takeaways | 🔴 RETIRE | Every decision listed (BLaIR, CLIP fusion $\beta=0.8$) has been superseded. |
| 28 | Section 6 divider | ✅ | Framing divider. |
| 29 | Core System Components | 🔴 FULL REPLACE | Architecture now includes Cleora, BGE-M3, DIF-SASRec, and NLLB. |
| 30 | Layer 1: FastAPI Orchestrator | 🟡 UPDATE | Token limits and encoder references must be updated. |
| 31 | Layer 2: Embedding Service | 🔴 FULL REPLACE | Both encoders replaced; latency reduced to 59ms warm-cache. |
| 32 | Layer 3: Data Layer | 🟡 UPDATE | Stored vectors are now 1024-d (BGE) and includes Cleora embeddings. |
| 33 | Layer 4: NBA Decision Engine | 🔴 FULL REPLACE | Replaced by Dual-Pipeline (Pipeline A + Pipeline B) union logic. |
| 34 | Overall Architecture | 🔴 FULL REPLACE | Diagram must show BGE-M3/Cleora/DIF-SASRec/NLLB flow. |
| 35 | Design Trade-offs | 🔴 RETIRE | Limitations listed are resolved in Phase 2. |
| 36 | Section 7 divider | ✅ | Framing divider. |
| 37 | Achievements / Future Plan | 🔴 RETIRE | Phase 2 has implemented the system; "Future plans" are now "Achievements". |
| 38 | Gantt Chart | 🔴 RETIRE | Historical timeline is no longer relevant for final defense. |
| 39 | Thank You | ✅ | Update with final HR@10 = 0.9736. |

---

## Section 2 — Slide Change Specifications

**`SLIDE:`** 5 — Project Scope

**`STATUS:`** 🔴 RETIRE / 🔴 FULL REPLACE

**`WHAT IS WRONG RIGHT NOW:`**
The slide lists "English only" and "Frozen encoders" as limitations. "Multimodal search" is listed as a primary goal but the scope is limited to a "Dev environment".

**`WHY IT IS WRONG:`**
Phase 2 implements a multilingual system (Vietnamese support via NLLB-200 + BGE-M3) and includes per-session online fine-tuning of the DIF-SASRec model. It is a deployed production-grade API, not just a dev proof-of-concept.

**`REPLACEMENT CONTENT:`**
**Title:** System Scope: Multilingual Personalization at Scale
- **Linguistic Scope:** Native support for English and Vietnamese (NLLB-200 + BGE-M3).
- **Model Scope:** Sequential Transformer (DIF-SASRec) with **Online Fine-Tuning** triggered by user interactions.
- **Data Scope:** 3M catalogue items; 375K item behavioral graph (Cleora).
- **Performance Scope:** <60ms warm-cache latency; sub-ms lexical search (Tantivy).

**`SOURCE FOR REPLACEMENT:`**
```
Study guide section: Overview
Capstone report section: 1.Introduction, §1.3 Scope
app/ reference: app/core/environment.py
```

**`COMMITTEE RISK IF NOT FIXED:`**
"You say the system is English-only, but your results show Vietnamese search performance. Which is it?"

---

**`SLIDE:`** 19 — Dataset: Amazon Reviews 2023

**`STATUS:`** 🟡 UPDATE

**`WHAT IS WRONG RIGHT NOW:`**
"34,048 users, 38,654 books, 76,347 reviews working dataset."

**`WHY IT IS WRONG:`**
Phase 2 scales to the full 2023 dataset: 3,082,126 catalogue items and a test set of 100,000 users. The Cleora index covers 375,280 active items.

**`REPLACEMENT CONTENT:`**
**Title:** Scaled Dataset: Amazon Books 2023
- **Total Catalogue:** 3,082,126 items (Tantivy/BM25 index).
- **Behavioral Subset:** 375,280 items in Cleora co-purchase graph.
- **Evaluation Set:** 100,000 users (Leave-one-out protocol).
- **Modality Coverage:** 99.1% of items have cover images; 100% have text descriptions.

**`SOURCE FOR REPLACEMENT:`**
```
Study guide section: Overview
Capstone report section: 5.ExperimentsEvaluation, §5.1 Experiment Setup
```

**`COMMITTEE RISK IF NOT FIXED:`**
"Your system claims to be scalable, but you are evaluating on a tiny dataset of 38K books."

---

**`SLIDE:`** 34 — Overall Architecture

**`STATUS:`** 🔴 FULL REPLACE

**`WHAT IS WRONG RIGHT NOW:`**
The diagram shows "BLaIR/CLIP → pgvector → Late Fusion → NBA".

**`WHY IT IS WRONG:`**
Phase 2 uses a completely different stack: NLLB-200 for translation, BGE-M3 and CLIP for encoding, Cleora for behavioral signal, DIF-SASRec for sequential intent, and Tantivy for lexical search.

**`REPLACEMENT CONTENT:`**
**Visual Guide:**
[Oval: User Query/Action] --"NLLB-200"--> [Rectangle: Multi-modal Encoder (BGE-M3/CLIP)]
[Rectangle: Multi-modal Encoder] --"Embed"--> [Cylinder: Search Indices (FAISS HNSW / Tantivy)]
[Cylinder: Search Indices] --"RRF"--> [Oval: Ranked Results]
[Oval: User History] --"Sequence"--> [Rectangle: DIF-SASRec]
[Oval: User History] --"Centroid"--> [Rectangle: Cleora KNN]
[Rectangle: DIF-SASRec] & [Rectangle: Cleora KNN] --"Union"--> [Oval: Recommendations]

**`SOURCE FOR REPLACEMENT:`**
```
Study guide section: Overview
Capstone report section: 3.SystemAnalysis, §3.1 Overall Architecture (Fig 3.1)
```

**`COMMITTEE RISK IF NOT FIXED:`**
"Your architecture diagram doesn't match the components mentioned in your results."

---

## Section 3 — New Slide Specifications

**`SLIDE_ID:`** NEW-01

**`PROPOSED TITLE:`**
BGE-M3 Replaces BLaIR: Multilingual Contrastive Training as a Structural Requirement

**`PLACEMENT:`**
INSERT BETWEEN: Slide 11 ("Contrastive Learning") and Slide 12 (to be replaced)
NARRATIVE ROLE: Bridges the gap between general contrastive theory and the specific model choice for a Vietnamese context.

**`GAP TYPE:`** 🔴 Hard Gap

**`THE SCIENTIFIC WHY (from defense_study_guide.html):`**
BLaIR is trained on Amazon review-description pairs (English-only) and fails on short descriptive queries and non-English input. BGE-M3's multi-granularity training on 100+ languages is required to support the project's multilingual goal.

**`THE FORMALISM (from Capstone report):`**
```latex
% Source: Capstone/sections/2.Theory/2.1.Foundation-knowledge.tex
\text{sim}(q, d) = \mathbf{q} \cdot \mathbf{d} = \cos(\theta) \quad [\text{when } \|\mathbf{q}\|_2, \|\mathbf{d}\|_2 = 1]
```
Term-by-term gloss:
- $\mathbf{q}$: 1024-dim L2-normalized query embedding from BGE-M3.
- $\mathbf{d}$: 1024-dim L2-normalized item embedding stored in FAISS.

**`VISUAL GUIDE:`**
[Rectangle: Query] --"NLLB-200"--> [Rectangle: English Query] --"BGE-M3"--> [Oval: 1024-d Vector]
[Oval: 1024-d Vector] --"Inner Product"--> [Cylinder: FAISS HNSW Index]

**`DEFENSE SCRIPT:`**
> BGE-M3 replaces the legacy BLaIR encoder to provide native support for Vietnamese queries, which previously achieved near-random Precision@10 of 0.025. By utilizing BGE-M3's multilingual contrastive representations, we achieve a Precision@10 of 0.55 on Vietnamese descriptive queries.

---

**`SLIDE_ID:`** NEW-02

**`PROPOSED TITLE:`**
Cleora Behavioral Graph: Capturing Co-Purchase Signals Beyond Modality

**`PLACEMENT:`**
INSERT BETWEEN: Slide 22 ("EDA Conclusion") and Slide 23 (divider)
NARRATIVE ROLE: Introduces the behavioral pillar that was absent in Phase 1.

**`GAP TYPE:`** 🔴 Hard Gap

**`THE SCIENTIFIC WHY (from defense_study_guide.html):`**
Encoders (BGE/CLIP) only capture what items *are*. Cleora captures how users *behave*. Co-purchase patterns reveal relationships (e.g., books in a series) that textual descriptions alone cannot fully recover.

**`THE FORMALISM (from Capstone report):`**
```latex
% Source: Capstone/sections/2.Theory/2.1.Foundation-knowledge.tex
\mathbf{e}_v^{(t)} = \frac{\sum_{u \in \mathcal{N}(v)} w_{uv}\, \mathbf{e}_u^{(t-1)}}{\left\| \sum_{u \in \mathcal{N}(v)} w_{uv}\, \mathbf{e}_u^{(t-1)} \right\|_2}
```
Term-by-term gloss:
- $\mathcal{N}(v)$: Neighbors of item $v$ in the co-purchase hypergraph.
- $w_{uv}$: Edge weight representing co-occurrence frequency.
- $\mathbf{e}_u^{(t-1)}$: Embedding of neighbor $u$ from the previous iteration.

**`VISUAL GUIDE:`**
[Cylinder: Interaction Data] --"Group by User"--> [Rectangle: Hypergraph]
[Rectangle: Hypergraph] --"Iterative Markov Propagation"--> [Oval: 1024-d Cleora Embeddings]

**`DEFENSE SCRIPT:`**
> Cleora allows us to embed 375,000 items in a behavioral space in under 10 minutes on a CPU. This behavioral signal provides a hit rate of 0.9047 in isolation, proving that user-item relationships are as critical as item content features.

---

**`SLIDE_ID:`** NEW-03

**`PROPOSED TITLE:`**
DIF-SASRec: Decoupled Attention for Sequential Personalization

**`PLACEMENT:`**
INSERT BETWEEN: Slide 32 ("Data Layer") and Slide 33 (to be replaced)
NARRATIVE ROLE: Replaces the rule-based NBA engine with a learned sequential model.

**`GAP TYPE:`** 🔴 Hard Gap

**`THE SCIENTIFIC WHY (from defense_study_guide.html):`**
Static fusion rules cannot model intent drift. DIF-SASRec's decoupled streams allow the model to attend to "what" (content) and "genre" (category) separately, improving robustness to cold-start items via BGE-M3 side information.

**`THE FORMALISM (from Capstone report):`**
```latex
% Source: Capstone/sections/2.Theory/2.1.Foundation-knowledge.tex
\mathbf{A}^{\text{fused}} = \alpha\,\mathbf{A}^{\text{cat}} + (1 - \alpha)\,\mathbf{A}^{\text{content}}
```
Term-by-term gloss:
- $\mathbf{A}^{\text{cat}}$: Attention map derived from item categories.
- $\mathbf{A}^{\text{content}}$: Attention map derived from BGE-M3 content embeddings.
- $\alpha$: Learnable scalar initialized at 0.7.

**`VISUAL GUIDE:`**
[Rectangle: Content Stream] --"Self-Attn"--> [Diamond: Fusion]
[Rectangle: Category Stream] --"Self-Attn"--> [Diamond: Fusion]
[Diamond: Fusion] --"Values (Content)"--> [Oval: Next-Item Intent]

**`DEFENSE SCRIPT:`**
> Unlike standard SASRec which uses only item IDs, DIF-SASRec decouples content and category signals. This architecture achieved an HR@10 of 0.7745 and supports real-time online fine-tuning, allowing the model to adapt to a user's intent within a single session.

---

**`SLIDE_ID:`** NEW-04

**`PROPOSED TITLE:`**
Union Hit Rate: Evaluating Complementary Dual-Pipeline Signals

**`PLACEMENT:`**
INSERT BETWEEN: Slide 26 (to be replaced) and Slide 27 (to be replaced)
NARRATIVE ROLE: Bridges the Phase 1 vs Phase 2 metric gap and justifies the 0.9736 claim.

**`GAP TYPE: 🟠 Formalism Gap`**

**`THE SCIENTIFIC WHY (from defense_study_guide.html):`**
The system presents two distinct UI sections. HR@10 = 0.9736 measures the union of these signals, reflecting the true probability of a successful recommendation across both panels.

**`THE FORMALISM (from Capstone report):`**
```latex
% Source: Capstone/sections/5.3.EndToEndEvaluation.tex
\text{HR}_{A \cup B} = P(\text{hit}_A \cup \text{hit}_B) = P(A) + P(B) - P(A \cap B)
```
Populated values:
- $P(A)$ (Cleora): 0.9047
- $P(B)$ (DIF-SASRec): 0.7745
- $P(A \cup B)$ (Union): 0.9736

**`VISUAL GUIDE:`**
[Rectangle: Top-10 (Pipeline A)] --"OR"--> [Oval: Final Recommendation Set]
[Rectangle: Top-10 (Pipeline B)] --"OR"--> [Oval: Final Recommendation Set]

**`DEFENSE SCRIPT:`**
> Our final system achieves a Hit Rate of 0.9736. This is a union hit rate representing the success of our dual-mode UI. Inclusion-exclusion analysis shows that 29.1% of hits are unique to DIF-SASRec, confirming that sequential modeling rescues cases where behavioral graph clusters are insufficient.

---

## Section 4 — Revised Master Slide Order

| Position | ID | Title | Status | Replaces |
|---|---|---|---|---|
| 1 | PDF-01 | Title Slide | ✅ | — |
| 2 | PDF-02 | Table of Contents | ✅ | — |
| 3 | PDF-03 | Section 1: Objective & Scope | ✅ | — |
| 4 | PDF-04 | Project Objective | ✅ | — |
| 5 | **NEW-SCOPE** | System Scope: Multilingual Personalization at Scale | 🔴 FULL REPLACE | PDF-05 |
| 6 | PDF-06 | Section 2: Problem Statements | ✅ | — |
| 7 | PDF-07 | The Problem | ✅ | — |
| 8 | PDF-08 | NBA System Concept | ✅ | — |
| 9 | PDF-09 | Why Multimodal (Behavioral Reframe) | 🟡 REFRAME | PDF-09 |
| 10 | PDF-10 | Section 3: Foundational Knowledge | ✅ | — |
| 11 | PDF-11 | Contrastive Learning | ✅ | — |
| 12 | **NEW-01** | BGE-M3: Multilingual Contrastive Training | **NEW** | PDF-12, 13 |
| 13 | **NEW-02** | Cleora Behavioral Graph | **NEW** | — |
| 14 | PDF-14 | Visual Encoder: CLIP | 🟡 REFRAME | PDF-14, 15 |
| 15 | PDF-18 | Section 4: Exploratory Data Analysis | ✅ | — |
| 16 | **NEW-DATA** | Scaled Dataset: Amazon Books 2023 (3M Items) | 🟡 UPDATE | PDF-19 |
| 17 | **NEW-TEXT** | Text Handling: Multilingual BGE-M3 Context | 🔴 UPDATE | PDF-20 |
| 18 | PDF-21 | Multimodal Asymmetry | 🟡 UPDATE | PDF-21 |
| 19 | PDF-22 | EDA Conclusion (including Graph Signal) | 🟡 REFRAME | PDF-22 |
| 20 | PDF-23 | Section 5: Model Evaluation | ✅ | — |
| 21 | **NEW-04** | Union Hit Rate: Dual-Pipeline Evaluation | **NEW** | PDF-24, 25 |
| 22 | **NEW-RESULTS** | Final Recommendation Results: HR@10 = 0.9736 | 🔴 FULL REPLACE | PDF-26 |
| 23 | **NEW-TAKE** | Final Takeaways: Cleora + DIF-SASRec | 🔴 FULL REPLACE | PDF-27 |
| 24 | PDF-28 | Section 6: System Design & Architecture | ✅ | — |
| 25 | **NEW-ARCH** | Dual-Mode System Architecture | 🔴 FULL REPLACE | PDF-29 |
| 26 | PDF-30 | Layer 1: FastAPI Orchestrator | 🟡 UPDATE | — |
| 27 | **NEW-EMBED** | Layer 2: Optimized Embedding Service (59ms) | 🔴 FULL REPLACE | PDF-31 |
| 28 | PDF-32 | Layer 3: Scalable Data Layer (HNSW/BM25) | 🟡 UPDATE | — |
| 29 | **NEW-03** | DIF-SASRec: Decoupled Sequential Modeling | **NEW** | PDF-33 |
| 30 | **NEW-DIAG** | End-to-End System Data Flow | 🔴 FULL REPLACE | PDF-34 |
| 31 | **NEW-LIMIT** | Current Limitations & Scalability Analysis | 🔴 FULL REPLACE | PDF-35 |
| 32 | PDF-36 | Section 7: Achievements | ✅ | — |
| 33 | **NEW-ACH** | Achievements: 843% HR Improvement | 🔴 FULL REPLACE | PDF-37, 38 |
| 34 | PDF-39 | Thank You (0.9736 Update) | 🟡 UPDATE | — |

---

## Section 5 — Cross-Reference Index

| Slide ID | Claim | Source File | Section | Metric/Equation |
|---|---|---|---|---|
| NEW-SCOPE | Vietnamese search support | Capstone/1.Introduction | §1.3 Scope | NLLB-200 Stage |
| NEW-01 | BGE-M3 vs BLaIR P@10 | Capstone/3.SystemAnalysis | §3.3 Challenges | 0.55 vs 0.025 |
| NEW-02 | Cleora Markov Eq | Capstone/2.Theory | §2.1 Foundation | $\ell_2$ Norm Markov |
| NEW-03 | DIF-SASRec Fusion Eq | Capstone/2.Theory | §2.1 Foundation | $\alpha$ Attn Fusion |
| NEW-04 | HR@10 = 0.9736 | study_guide.html | Overview | Union $P(A \cup B)$ |
| NEW-ARCH | 59ms Latency | update_regular/BGE... | Timing Results | Avg 12.6ms (optimized) |
| NEW-RESULTS| 843% Improvement | Capstone/5.Experiments... | §5.3 End-to-End | vs GRU-SeqDQN |
| NEW-EMBED | Stage 1-3 Optimizations | update_regular/BGE... | Implemented Opts | max_seq_len = 64 |
