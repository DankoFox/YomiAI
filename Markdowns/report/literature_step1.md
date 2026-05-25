# Step 1B — Literature Review

**Purpose:** Input for Chapter 2 NBA section.
**Papers must come from verified_papers.md only.**
**Created:** 2026-05-24

---

## Section A — Founding Papers

### A1 · FPMC (2010) — The Markov Origin
**Cite as:** \cite{rendle2010fpmc}

Rendle, Freudenthaler, and Schmidt-Thieme (2010) introduced Factorizing Personalized Markov Chains (FPMC), combining matrix factorization with first-order Markov chain transitions to model item sequences. Operating on basket-level interaction data, FPMC is among the earliest methods to frame sequential product recommendation as a personalized next-item prediction problem. The model's sequential inductive bias — that the next action depends on the previous — directly instantiates the Next Best Action (NBA) paradigm in recommender systems.

**Key contribution:** Unified MF + Markov into a single factorized tensor; enabled tractable inference for sparse, long-tail item spaces.

**Publication:** WWW 2010 | DOI: 10.1145/1772690.1772773 | 2,665 citations

---

### A2 · GRU4Rec (2016) — The Deep Learning Transition
**Cite as:** \cite{hidasi2016gru4rec}

Hidasi et al. (2016) demonstrated that Gated Recurrent Units (GRU) can capture session-level sequential dependencies substantially better than Markov models. GRU4Rec treats the recommendation problem as a sequence-to-next-item prediction task, trained with ranking losses (BPR-max, TOP1-max) directly optimized for recall. Its success marked the transition from hand-crafted transition matrices to learned representation of sequential patterns, defining the RNN era of NBA recommendation.

**Key contribution:** First GRU-based session recommendation; introduced ranking loss adaptation for RNN recommenders.

**Publication:** ICLR 2016 (workshop) | arXiv: 1511.06939

---

## Section B — Traditional Approaches (3 papers)

### B1 · FPMC — Markov/Bandit Approach
**Cite as:** \cite{rendle2010fpmc}

*(See Section A above for full details.)*

**Role in Section B:** Represents the Markov-chain family. FPMC's limitation — it can only model first-order transitions, with no capacity to encode long-range session context or item content — makes it the baseline "non-deep" approach that motivates GRU4Rec and SASRec.

---

### B2 · GRU4Rec — RNN Approach
**Cite as:** \cite{hidasi2016gru4rec}

*(See Section A above for full details.)*

**Role in Section B:** Represents the RNN family. GRU4Rec captures unbounded sequential history but processes items as one-hot IDs — no semantic content, no visual attributes. Users with sparse histories receive degraded recommendations. The absence of self-attention means the model cannot selectively attend to the most decision-relevant past items.

---

### B3 · SASRec — Self-Attention Approach
**Cite as:** \cite{kang2018sasrec}

Kang and McAuley (2018) proposed the Self-Attentive Sequential Recommendation (SASRec) model, which applies a causally-masked Transformer architecture to sequential recommendation. By attending to relevant past items rather than processing all history equally, SASRec outperforms GRU4Rec on sparse and dense datasets alike. Its scalable O(L²d) attention mechanism became the foundation for subsequent sequential models including BERT4Rec, DIF-SASRec variants, and the present work.

**Key contribution:** Introduced causal self-attention to sequential recommendation; best accuracy/cost trade-off at the time; replaced GRU as the dominant sequential baseline.

**Publication:** ICDM 2018 | arXiv: 1808.09781

**Role in Section B:** Represents the attention/Transformer family. Core shared limitation of B1–B3: none incorporate visual product attributes, multimodal content signals, or per-user in-session weight updates. All three encode items as learned ID embeddings — brittle to new or sparse items.

---

## Shared Gap (closing sentence for Paragraph 2)

> Across FPMC, GRU4Rec, and SASRec, the fundamental limitation is consistent: sequential patterns are captured over item IDs rather than item content. Without access to visual attributes, textual descriptions, or multimodal signals, these systems fail on cold-start items and cannot model fine-grained semantic preferences — precisely the gap that our dual-pipeline system addresses.

---

## Section C — Multimedia Papers 2022+

### C1 · MMSSL (2023) — Contrastive Multimodal Alignment
**Cite as:** \cite{wei2023mmssl}

Wei et al. (2023) proposed Multi-Modal Self-Supervised Learning for Recommendation (MMSSL), which employs inter-modality contrastive learning to align visual and textual item representations without requiring labeled multimodal annotation. MMSSL demonstrates that visual-textual alignment provides recommendation signals orthogonal to collaborative filtering — bridging the ID-embedding gap with rich semantic content.

**Key result:** Superior to ID-only models on multiple e-commerce benchmarks; alignment between image and text modalities is the critical signal.

**Publication:** WWW 2023 | DOI: 10.1145/3543507.3583206 | 189 citations

---

### C2 · BM3 (2023) — Bootstrap-Based Multimodal Representations
**Cite as:** \cite{zhou2023bm3}

Zhou et al. (2023) introduced BM3 (Bootstrap Multi-Modal Multi-task), which bootstraps contrastive views of item visual and textual embeddings through dropout augmentation, avoiding auxiliary interaction graphs and negative sampling. BM3 achieves 2–9× training speedups over graph-based multimodal methods while maintaining competitive accuracy, demonstrating that lightweight self-supervised alignment is sufficient for multimodal recommendation.

**Key result:** Negative-sampling-free multimodal training with superior speed and comparable accuracy to heavier graph approaches.

**Publication:** WWW 2023 | arXiv: 2207.05969

---

### C3 · LGMRec (2024) — Local + Global Graph with Multimodal Features
**Cite as:** \cite{guo2024lgmrec}

Guo et al. (2024) proposed LGMRec, combining local item-level and global user-level hypergraph structures with multimodal (visual + text) item features. By modeling both fine-grained item relationships and global user community patterns, LGMRec demonstrates that structural graph signals and visual content are complementary — neither alone is sufficient for the full recommendation picture.

**Key result:** Graph + multimodal fusion consistently outperforms graph-only and multimodal-only ablations across three benchmarks.

**Publication:** AAAI 2024 | DOI: 10.1609/aaai.v38i8.28688 | 105 citations

---

## Narrative Thread for Chapter 2

1. **FPMC (2010)** introduces sequential next-item prediction with Markov transitions.
2. **GRU4Rec (2016)** replaces hand-crafted transitions with learned RNN representations.
3. **SASRec (2018)** introduces self-attention, capturing long-range sequential dependencies efficiently.
4. **Gap:** All three encode items as IDs — no visual attributes, cold-start vulnerable.
5. **MMSSL + BM3 (2023)** fill the gap: visual-textual self-supervised alignment is the missing signal.
6. **LGMRec (2024)** extends this to structured graph settings, confirming multimodal content + structure as the new standard.
7. **Our system:** Pipeline A (Cleora + BGE-M3) covers the behavioral co-purchase graph with content re-ranking; Pipeline B (DIF-SASRec, based on SASRec) handles sequential intent with visual content signals. Online fine-tuning via AgentPool addresses the cold-start and session-shift limitations.
