# Capstone Project (CO4337)
## Leveraging Multimedia Data for Next Best Action Recommendation System
* **Authors:** Dang Minh Khang (2252287), Pham Tran Dang Khoa (2252360), Le Ha Nguyen Khanh (2252327)
* **Advisor:** PhD. Le Thanh Van
* **Institution:** BK HCMC University of Technology

---

## Table of Contents
1. Problem Statement & Motivation
2. Project Objectives & Scope
3. Foundational Knowledge
4. Model evaluation
5. Results, Limitations & Future Directions
*Institution:* BK HCMC University of Technology

---

## 1. Problem Statements & Motivation
*Institution:* BK HCMC University of Technology

### The Problem: Information Overload
**Traditional Gaps**
* Limited search for both keyword & long query
* Blind to recent shift in reading intents

**Our Solutions**
* Co-genre recommendation
* Dual Encoders: BGE-M3 (text), CLIP (image)
* Dual Pipelines: Behavioral Graph + Sequential Transformer
* Real-time Update: Per-interaction online fine-tuning
*Institution:* BK HCMC University of Technology

---

## Next Best Action System Concept

| Output / Logic | Classical ranking | THIS SYSTEM |
| :--- | :--- | :--- |
| **Output** | Single ranked list | Two complementary signals |
| **Logic** | Score items by relevance | Surface the right signal for the right context |
| **Hit condition** | Item in top-K list | Item in either signal |

**Two Complementary Signals**
* **Behavioural Signal:** "What do readers with similar taste also purchase?"
* **Sequential Signal:** "Based on your recent reading, what comes next?"
*Institution:* BK HCMC University of Technology

---

## Why Multimodal for Books?

**Text Modality**
* Rich reviews - 90th percentile <= 204 words, within BGE-M3's encoding window
* Rich metadata (author, genre, theme) captures plot, writing style, and tone
* Example: "Mystery novel, strong female lead, minimalist style"

**Image Modality**
* High quality book covers (99.1%) with genre conventions (colors/typography)
* Captures: aesthetics, visual patterns

**Multimodal Advantage**
* INSIDE (content) + what's OUTSIDE (aesthetics) allows for a more comprehensive understanding of user preferences
* Example: "Find books with covers similar to dark fantasy"
*Institution:* BK HCMC University of Technology

---

## 2. Project Objective & Scope
*Institution:* BK HCMC University of Technology

### Project Objective
**Multimodal & Multilingual Search**
1. Implement Dual-Encoders
2. Optimize for Speed

**Interactive Deployment**
1. Full-Stack Integration
2. Real-Time Adaptation
3. Generative AI Assistant

**Dual-Pipeline Recommendation**
1. Model Behavioral Intent (Pipeline A)
2. Model Sequential Intent (Pipeline B)
*Institution:* BK HCMC University of Technology

---

## System Scope

**User Experience**
* Multimodal Discovery, Real-time Adaptation

**Core Engines**
* **Hybrid Search:** BGE-M3 and CLIP semantic vectors fused with BM25 lexical scoring
* **Dual-Pipeline Recs:** Cleora co-purchase graphs + DIF-SASRec sequential transformers

**Data & Infrastructure**
* **Massive Scale:** 3 million catalog items and a 375,000-node behavioral graph
* **High Performance:** 59ms warm-cache latency driven by HNSW approximate indexing
*Institution:* BK HCMC University of Technology

---

## Dataset: Amazon Reviews 2023
Source: McAuley-Lab/Amazon-Reviews-2023

**1. Statistics**
* Total Reviews: ~571 million across all categories
* Books Category: ~29 million reviews
* Time Period: May 1996 - September 2023

**2. Dataset Descriptions**
| METRIC | RAW DATASET | FINAL SYSTEM |
| :--- | :--- | :--- |
| Item Metadata | 4,448,181 | 3,000,000 items |
*Institution:* BK HCMC University of Technology

---

## 3. System Analysis & Architecture
*Institution:* BK HCMC University of Technology

### Overall Architecture
* **Presentation Tier:** Javascript UI framework, CSS
* **Application Tier:** Concurrent agent pool, REST API (HTTP, Responses)
    * **[API] - Search:** Text embedding model, Visual embedding model, Neural machine translation, BM25 keyword search engine, ANN index (HNSW)
    * **[API] - Interact:** Async mongodb driver, In-memory profile manager
    * **[API] - LLM (Ask AI):** Large language model (1.5 B parameter), ANN index (HNSW), Google Books API
    * **[API] - Recommend:** Graph embedding model, Sequential transformer model, ANN index (HNSW)
* **Data Tier:** Keyword index - BM25, Visual index - ANN (3M vectors), Semantic text index ANN (1.7M-3M vectors), DIF-SASRec pretrained (.pt), Columnar Store (Parquet), Dense Vector Store (behavioral graph embeddings), Per-user Model Checkpoints (.pt), Container Orchestration (Queue), Database
*Institution:* BK HCMC University of Technology

---

### Text Encoder: BAAI/BGE-M3
BAAI General Embedding - M3 provides deep semantic understanding of textual content.
* **Key Highlights:**
    1. Multi-Granularity: Handles variable-length inputs for robust fuzzy matching
    2. Zero-Shot Ready: High semantic recall out-of-the-box
    3. Unified Backbone: Single 1024-d space -> end-to-end system consistency
* **Architecture:** XLM-ROBERTa-LARGE (24 layers, ~568M parameters)
* **Dimension:** 1024-dimensional dense vectors (L2-normalized)

### Visual Encoder: CLIP
Contrastive Language-Image Pre-training handles vision-language understanding.
* **Key Highlights:**
    1. Image Encoder: Vision Transformer
    2. Text Encoder: Modified Transformer
    3. Aligned embedding space (512-d)
* **Architecture:** Vision Transformer (ViT-B/32)
* **Dimension:** 512-dimension encoding
*Institution:* BK HCMC University of Technology

---

### Fusion Strategies: Adaptive Weighted RRF
* Separate encoders: For each modality
* Combine: At decision layer

**Advantages:**
* Cross-channel consensus rewards items found by multiple retrievers
* Adaptive weighting adjusts the lexical vs. semantic balance per query
* Modality-aware visual channel activates on image input
*Institution:* BK HCMC University of Technology

---

### BM25 + HNSW + RRF Retrieval

| Characteristic | Tantivy BM25 (sparse) | FAISS HNSW (dense) |
| :--- | :--- | :--- |
| **Finds** | Exact-match token recall | Semantically similar items |
| **Misses** | Paraphrases, fuzzy queries | Exact title / author matches |
| **Complexity** | Sub-ms inverted index lookup | O(log n) ANN search |

**Reciprocal Rank Fusion (RRF)**
* k=60 acts as a smoothing constant to prevent any single top-ranked item from dominating.
* RRF features no score normalisation, making it robust to scale differences between dense and sparse systems, and it outperforms learned aggregation in low-resource settings (Cormack et al. 2009).
*Institution:* BK HCMC University of Technology

---

### DIF-SASRec Decoupled Attention
* SASRec relies on item ID embeddings only, leaving side information absent from the attention stream.
* BERT4Rec applies a bidirectional mask, but its training objective is inconsistent with next-item inference.
* DIF-SASRec decouples content and category attention, whereas prior models fuse both into a single stream, losing fine-grained intent signals.

**Workflow:**
* Content and category attend independently through decoupled streams.
* A shared value matrix ensures category shapes attention while content carries meaning.
* A learnable alpha gate allows the model to learn the optimal content/category balance during training.
*(Sourced from: Y. Xie, P. Zhou, and S. Kim, "Decoupled Side Information Fusion for Sequential Recommendation, Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR 22) 2022)*
*Institution:* BK HCMC University of Technology

---

### Cleora Graph Propagation
* Features no random-walk sampling, making it deterministic and fully reproducible.
* It requires no contrastive objective or GPU training loop, needing only 2-3 iterations to converge.
* It scales efficiently to 375K items in mere CPU-minutes.
*Institution:* BK HCMC University of Technology

---

## 4. Model Evaluation
*Institution:* BK HCMC University of Technology

### Phase 1 - Active Search Pipeline
1.  **Query Input:** Accepts Text query or Image query
2.  **Parallel Encoding:** Text queries pass through NLLB-200 translation and encode via BGE-M3 (1024-d text). Image queries encode via CLIP (512-d image).
3.  **Hybrid Retrieval:** Encoded items hit FAISS HNSW (dense O(log n)) and Tantivy BM25 (sparse sub-ms) for text, and CLIP HNSW (3M cover images) for visual search.
4.  **Late Fusion:** Retrieves Top-10 results using Adaptive RRF weighted at k=60.
*Institution:* BK HCMC University of Technology

---

### Text Encoder – Why BGE-M3?

**What We Need:**
* **3M Books In Catalogue:** The sheer scale rules out simple keyword matching.
* **Users type short, conversational queries:** The model must handle real query style rather than basic document matching.

| Search Quality | Precision@10 (EN) |
| :--- | :--- |
| Short (EN) | 0.15 |
| Medium (EN) | 0.33 |
| Long (EN) | 0.4 |

*Note:* Precision improves as queries become more conversational, which is strictly aligned with how BGE-M3 was trained.
*Institution:* BK HCMC University of Technology

---

### Two Indices, Two Jobs - Both Stay in the System
Both indices are loaded at startup and neither is dropped.

| Characteristic | OUR: HNSW + BGE-M3 | OUR: Flat + BGE-M3 |
| :--- | :--- | :--- |
| **Scale** | 1.7M Vectors | 3M Vectors |
| **Roles** | Live text search (top-50) & DIF-SASRec candidate pool (top-200 KNN) | DIF-SASRec candidate scoring & User BGE-M3 profile building |
| **Requirement** | Must respond in < 200 ms | Zero approximation error |
| **Recall** | 0.521 | 1.000 |
| **Latency** | 120 ms | 612 ms |

* **Handling the HNSW recall gap (0.521):** Tantivy BM25 runs in parallel and merges results via RRF, ensuring an HNSW miss does not equate to an end-to-end miss.
* **Visual search:** This relies on a separate CLIP index using the same ANN pattern, operating without a quantitative recall benchmark due to its perceptual nature.
*Institution:* BK HCMC University of Technology

---

### Search Pipeline - 18.6x Latency Reduction

| Stage | Translate | Encode | E2E wall clock |
| :--- | :--- | :--- | :--- |
| Baseline | 204.51 ms | 97.89 ms | 1,101.99 ms |
| Translator optimised | 1.19 ms | 30.12 ms | 59.20 ms |
| Cold cache | 185.25 ms | 37.16 ms | 1,204.11 ms |

* **Target Latency:** < 300 ms (Warm cache achieved: 59 ms)
* **Translation Optimisation:** Latency plummeted from 204 ms to 1.19 ms using NLLB int8 quantisation and by pre-warming the model at startup.
* **Cold Cache Behaviour:** The first query after a restart registers at ~1,200 ms because NLLB loads on demand; subsequent queries return to 59 ms immediately.
*Institution:* BK HCMC University of Technology

---

### Phase 2 – Dual Recommendation Pipeline
1.  **Input:** User history click sequence is fed into a BGE-M3 profile vector.
2.  **Pipeline A — Behavioural:** Applies a Cleora KNN co-purchase graph featuring a content veto (tau=0.30).
3.  **Pipeline B — Sequential:** Uses DIF-SASRec sequential intent, also utilizing a content veto (tau=0.30).
4.  **Output:** Both pipelines flow into an NBA (Next Best Action) engine for action selection, delivering Top-10 results.
*Institution:* BK HCMC University of Technology

---

### End-to-end Evaluation

| System | HR@10 | NDCG@10 |
| :--- | :--- | :--- |
| **Pipeline A (Cleora + BGE-M3)** | 0.905 | 0.539 |
| **DIF-SASRec (Pipeline B)** | 0.775 | 0.503 |
| **Content Baseline (BGE-M3)** | 0.435 | 0.302 |
| **Random Baseline** | 0.100 | 0.045 |
| **GRU-SeqDQN (prior)** | 0.082 | 0.037 |

*Key Insight:* Using Pipeline A, 9 in 10 users find a relevant book within the top 10 results.
*Institution:* BK HCMC University of Technology

---

## 5. Results & Future Directions
*Institution:* BK HCMC University of Technology

### What we achieve
* Built an optimized dual pipeline recommendation system
* Multimodal search supporting both text queries and image
* Online per user learning - DIF-SASRec with every interaction

### Plan for future
* Scale FAISS indices to support real time item ingestion without server restarts
* Replace local .pt file storage with a centralised model registry for multi server deployment
*Institution:* BK HCMC University of Technology

---

## THANK YOU FOR LISTENING
*Institution:* BK HCMC University of Technology