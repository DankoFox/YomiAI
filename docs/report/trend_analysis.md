# Step 1A — NBA Research Trend Analysis

**Field:** Next Best Action / Sequential Recommendation in E-Commerce
**Scope:** 2010–2024
**Created:** 2026-05-24
**Method:** Cross-database search via arXiv, OpenAlex, Crossref, Semantic Scholar MCP

---

## Year NBA Peaks in Citations

Based on cross-database analysis:

| Period | Dominant Method | Representative Papers | Peak Citation Era |
|--------|----------------|----------------------|-------------------|
| 2008–2012 | Markov Chains, Matrix Factorization | FPMC (Rendle 2010, 2,665 citations) | 2013–2016 (cited during rise of deep learning) |
| 2015–2017 | RNN / GRU-based | GRU4Rec (Hidasi 2016) | 2017–2019 |
| 2018–2021 | Transformer / Self-Attention | SASRec (Kang 2018), BERT4Rec (Sun 2019) | 2019–2022 |
| 2022–2024 | Multimodal + LLM-augmented | MMSSL, BM3, LGMRec, LLaRA | Current (still accumulating) |

**Peak NBA citation period:** 2019–2021, driven by SASRec derivatives and adoption in industry systems (Amazon, JD.com, Alibaba).

---

## Venue Dominance

| Venue | Role | Representative Papers |
|-------|------|-----------------------|
| **RecSys** | Core recommendation venue | BERT4Rec, UniSRec, cross-domain rec |
| **WWW / The Web Conference** | Multimodal + graph rec | FPMC (WWW 2010), MMSSL (WWW 2023), BM3 (WWW 2023) |
| **ICDM** | Transformer-based rec | SASRec (ICDM 2018) |
| **SIGIR** | IR-focused rec + LLM-rec | LLaRA (SIGIR 2024), IISAN (SIGIR 2024) |
| **AAAI / KDD** | Graph + multi-task rec | LGMRec (AAAI 2024) |

**Dominant venue for multimodal NBA:** WWW 2023 saw a surge of multimodal recommendation papers (MMSSL, BM3, IDvs.MoRec); AAAI 2024 extended this to graph-multimodal fusion.

---

## Method Family Evolution

```
2010  FPMC → Markov + MF (first personalized sequential rec)
  |
2015  GRU4Rec → RNN/GRU (session-level sequential modeling)
  |
2018  SASRec → Transformer / Self-Attention (scalable, long-range)
  |
2019  BERT4Rec → Bidirectional transformer (cloze-style training)
  |
2021  Graph-based → SURGE, CL4SRec (contrastive + graph)
  |
2022  UniSRec → Universal / transferable (content-based ID-free)
  |
2023  Multimodal → MMSSL, BM3 (visual + text alignment)
       LLM-augmented → LLMRec, LLaRA
  |
2024  Multimodal + Graph → LGMRec
       Decoupled multimodal → IISAN (PEFT for multimodal seq rec)
```

**What replaced what:**
- Markov Chains → replaced by GRU (captured long-range context)
- GRU → replaced by Transformer/SASRec (parallelizable, selective attention)
- ID-only Transformer → augmented by content/multimodal (handles cold-start)
- Static embeddings → now updated via self-supervised contrastive learning or LLM features

---

## Key Research Gaps Identified (for Chapter 2 Paragraph 2)

All three traditional methods (FPMC, GRU4Rec, SASRec) share these failure modes:

1. **Visual attribute blindness:** Item representations are learned ID embeddings, carrying no visual semantics. Two visually identical products with different IDs are treated as unrelated.
2. **Cold-start fragility:** New or sparse items have undertrained embeddings; sequential models cannot reason about items not seen in training.
3. **Session-shift rigidity:** Model weights are fixed at inference — no mechanism to adapt within a single session based on real-time user signals.

These three gaps motivate the dual-pipeline design:
- **Pipeline A** (Cleora + BGE-M3): Behavioral co-purchase graph + semantic text embedding handles sparse, new items with rich content.
- **Pipeline B** (DIF-SASRec, based on SASRec with decoupled content/category streams): Sequential intent with visual content signals.
- **AgentPool online fine-tuning**: Each user click triggers a gradient step on the per-user personal model weights — addressing gap 3 (session-shift rigidity).

---

## Saved Narrative for trend_analysis.md

**Paragraph for thesis narrative:**

> Sequential recommendation research evolved in three distinct waves. The Markov era (2010–2016) established that next-item prediction benefits from explicit transition modeling, formalized by FPMC \cite{rendle2010fpmc}. The deep learning wave (2016–2021) replaced transition matrices with RNNs and Transformers: GRU4Rec \cite{hidasi2016gru4rec} demonstrated session-level RNN superiority; SASRec \cite{kang2018sasrec} then showed that sparse self-attention outperforms full-history RNNs by selectively attending to decision-relevant items. The current multimodal wave (2022–present) addresses the shared limitation of all prior work: item ID blindness. Systems such as MMSSL \cite{wei2023mmssl}, BM3 \cite{zhou2023bm3}, and LGMRec \cite{guo2024lgmrec} demonstrated that aligning visual and textual item content with collaborative signals — rather than relying on ID embeddings alone — unlocks significant gains, particularly for cold-start and long-tail items.
