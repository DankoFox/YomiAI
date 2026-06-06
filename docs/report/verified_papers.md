# Step 1C — Verified Papers for Citation

**Rule:** Each paper must appear in ≥2 databases to be citable.
**Verified on:** 2026-05-24

---

## Section A — Founding Papers

### Paper A1 — FPMC
| Field | Value |
|-------|-------|
| **BibTeX key** | `rendle2010fpmc` |
| **Title** | Factorizing personalized Markov chains for next-basket recommendation |
| **Authors** | Steffen Rendle, Christoph Freudenthaler, Lars Schmidt-Thieme |
| **Year** | 2010 |
| **Venue** | WWW '10: Proceedings of the 19th international conference on World Wide Web |
| **DOI** | 10.1145/1772690.1772773 |
| **Citations** | 2,665 (OpenAlex) |
| **Databases** | OpenAlex ✓ · Crossref ✓ |
| **Status** | **CITABLE** (2 databases) |

**Why Section A:** Earliest sequential recommendation paper in the set; combines MF with first-order Markov transitions; defines the personalized next-item prediction problem that all later methods build on.

---

### Paper A2 — GRU4Rec
| Field | Value |
|-------|-------|
| **BibTeX key** | `hidasi2016gru4rec` |
| **Title** | Session-based Recommendations with Recurrent Neural Networks |
| **Authors** | Balázs Hidasi, Alexandros Karatzoglou, Linas Baltrunas, Domonkos Tikk |
| **Year** | 2016 |
| **Venue** | ICLR 2016 |
| **arXiv** | 1511.06939 |
| **Citations** | 559 arXiv version (OpenAlex); full citation count ~3,000+ including CIKM 2018 follow-up |
| **Databases** | arXiv ✓ · OpenAlex ✓ |
| **Status** | **CITABLE** (2 databases) |

**Why Section A:** First deep-learning (RNN) approach to session-based recommendation; introduces GRU into the recommendation pipeline; sets the benchmark that SASRec later surpasses.

---

## Section B — Traditional Approaches

### Paper B1 — FPMC (Markov / factorized approach)
*Same as Paper A1 above — refer to `rendle2010fpmc`.*

**Label in report:** "traditional Markov-chain approach to sequential recommendation"

---

### Paper B2 — GRU4Rec (RNN approach)
*Same as Paper A2 above — refer to `hidasi2016gru4rec`.*

**Label in report:** "GRU4Rec (traditional RNN-based session recommendation)"

---

### Paper B3 — SASRec
| Field | Value |
|-------|-------|
| **BibTeX key** | `kang2018sasrec` |
| **Title** | Self-Attentive Sequential Recommendation |
| **Authors** | Wang-Cheng Kang, Julian McAuley |
| **Year** | 2018 |
| **Venue** | ICDM 2018 |
| **arXiv** | 1808.09781 |
| **Citations** | ~85 arXiv version (OpenAlex); full ~3,000+ across venues |
| **Databases** | arXiv ✓ · OpenAlex ✓ |
| **Status** | **CITABLE** (2 databases) |

**Why Section B:** Canonical self-attention architecture for sequential recommendation; balances Markov Chains and RNNs via sparse attention; standard baseline for all subsequent sequential rec papers including DIF-SASRec.

**Label in report:** "SASRec (self-attention sequential recommendation)"

---

## Section C — Multimedia Papers 2022+

### Paper C1 — MMSSL
| Field | Value |
|-------|-------|
| **BibTeX key** | `wei2023mmssl` |
| **Title** | Multi-Modal Self-Supervised Learning for Recommendation |
| **Authors** | Wei Wei, Chao Huang, Lianghao Xia, Chuxu Zhang |
| **Year** | 2023 |
| **Venue** | WWW '23: The ACM Web Conference 2023 |
| **DOI** | 10.1145/3543507.3583206 |
| **Citations** | 189 (OpenAlex) |
| **Databases** | OpenAlex ✓ · Crossref ✓ |
| **Status** | **CITABLE** (2 databases) |

**Why Section C:** Proposes inter-modality contrastive learning to align visual and textual item representations for recommendation; directly supports the claim that multimodal signals improve over single-modality approaches.

---

### Paper C2 — BM3
| Field | Value |
|-------|-------|
| **BibTeX key** | `zhou2023bm3` |
| **Title** | Bootstrap Latent Representations for Multi-modal Recommendation |
| **Authors** | Xin Zhou, Hongyu Zhou, Yong Liu, Zhiwei Zeng, Chunyan Miao, Pengwei Wang, Yuan You, Feijun Jiang |
| **Year** | 2023 |
| **Venue** | WWW '23: The ACM Web Conference 2023 |
| **arXiv** | 2207.05969 |
| **Citations** | 11 (OpenAlex arXiv version); full count ~200+ published |
| **Databases** | arXiv ✓ · OpenAlex ✓ |
| **Status** | **CITABLE** (2 databases) |

**Why Section C:** Bootstraps contrastive views via dropout augmentation across modalities; avoids negative sampling and auxiliary graphs; achieves 2–9× speedup. Shows visual + text alignment is sufficient for strong multimodal recommendation.

---

### Paper C3 — LGMRec
| Field | Value |
|-------|-------|
| **BibTeX key** | `guo2024lgmrec` |
| **Title** | LGMRec: Local and Global Graph Learning for Multimodal Recommendation |
| **Authors** | Zhiqiang Guo, Jianjun Li, Guohui Li, Chaoyang Wang, Si Shi, Bin Ruan |
| **Year** | 2024 |
| **Venue** | AAAI 2024: Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 38 Issue 8 |
| **DOI** | 10.1609/aaai.v38i8.28688 |
| **Citations** | 105 (OpenAlex) |
| **Databases** | OpenAlex ✓ · Crossref ✓ |
| **Status** | **CITABLE** (2 databases) |

**Why Section C:** Combines local item-level and global user-level graph structures with multimodal features (visual + text); most recent confirmed multimodal recommendation paper in the set; bridges graph-based collaborative filtering with visual signals.

---

## DIF-SASRec — CONFIRMED: Published Paper

**DIF-SASRec IS a published paper**, already in `ref.bib` as `xie2022difsasrec`:

| Field | Value |
|-------|-------|
| **BibTeX key** | `xie2022difsasrec` (already in ref.bib) |
| **Title** | Decoupled Side Information Fusion for Sequential Recommendation |
| **Authors** | Yueqi Xie, Peilin Zhou, Sunghun Kim |
| **Year** | 2022 |
| **Venue** | SIGIR '22: The 45th International ACM SIGIR Conference |
| **DOI** | 10.1145/3477495.3531963 |
| **Citations** | 111 (Crossref) |
| **Databases** | Crossref ✓ · OpenAlex ✓ |
| **Status** | **CITABLE** (2 databases) — already in ref.bib |

**Description:** Proposes decoupled side information fusion — separate attention streams for ID-based and content-based (side information: category, text, visual) features — which is exactly the architecture implemented in `app/services/dif_sasrec.py` with `DIFAttentionLayer` content/category stream decoupling.

**Recommended citation strategy:** Cite `xie2022difsasrec` for DIF-SASRec, and `kang2018self` for the SASRec base architecture.

---

## Summary Table

| BibTeX key | Section | Databases | Citations | Status |
|-----------|---------|-----------|-----------|--------|
| `rendle2010fpmc` | A + B(Markov) | OpenAlex + Crossref | 2,665 | ✅ CITABLE |
| `hidasi2016gru4rec` | A + B(RNN) | arXiv + OpenAlex | ~3,000 | ✅ CITABLE (already in ref.bib) |
| `kang2018self` | B(Attention) | arXiv + OpenAlex | ~3,000 | ✅ CITABLE (already in ref.bib as kang2018self) |
| `xie2022difsasrec` | B/System | Crossref + OpenAlex | 111 | ✅ CITABLE (already in ref.bib) |
| `wei2023mmssl` | C | OpenAlex + Crossref | 189 | ✅ CITABLE — needs ref.bib entry |
| `zhou2023bm3` | C | arXiv + OpenAlex | ~200 | ✅ CITABLE — needs ref.bib entry |
| `guo2024lgmrec` | C | OpenAlex + Crossref | 105 | ✅ CITABLE — needs ref.bib entry |
