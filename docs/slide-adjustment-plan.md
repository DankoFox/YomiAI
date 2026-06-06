# Slide Adjustment Plan — Defense Feedback Response
**Date:** 2026-05-26  
**Trigger:** Committee feedback after mock defense  
**Core problem:** Slides focus on *how* the system works (pipelines, multimedia) but fail to establish *what* NBA is, *who defined it first*, and *why existing approaches fall short*. Evaluation table is also missing real academic baselines.

---

## Summary of Committee Criticisms

| Criticism | Root Cause | Fix |
|---|---|---|
| "What is the traditional [approach]?" | No definition of traditional NBA | Fix 1 + Fix 2 |
| "Did you do the literature review?" | NBA lineage absent from slides | Fix 1 |
| "18.6× — what did you optimize exactly?" | Slide is too vague | Fix 5 |
| "That's not end-to-end evaluation" | System A∪B missing; routing not shown | Fix 3 + Fix 4 |
| "Who was first — that's your benchmark" | FPMC/GRU4Rec not shown as lineage | Fix 1 |
| "Need a real baseline, not weak ones" | GRU4Rec, SASRecF missing from table | Fix 3 |

---

## Fix 1 — Add NBA Lineage Slide (CRITICAL)

**Insert after:** "Problem Statements & Motivation"  
**Before:** "Next Best Action System Concept"  
**Source:** `thesis/Captsone/chapter2_nba_section.tex`

### New Slide: "15 Years of Next Best Action Research"

```
FPMC — Rendle et al. (2010)                    ← "Who was first"
  First formalization of next-item prediction
  Method: Markov chain + matrix factorization
  Limit: one-step Markov, ignores session history

GRU4Rec — Hidasi et al. (2016)
  First deep learning NBA system
  Method: GRU captures full session sequence
  Limit: sequential bottleneck, ID-only, no cold-start

SASRec — Kang & McAuley (2018)
  Transformer replaces GRU; parallel training
  Method: causal self-attention over item IDs
  Limit: still ID-only, frozen at serving

DIF-SASRec — Xie et al. (2022)
  Decoupled content + category attention streams
  Limit: offline batch only, no within-session adaptation

Our System (2024)
  Addresses ALL prior limitations:
  ✓ Multimodal content (not ID-only)
  ✓ Online per-user fine-tuning (not frozen)
  ✓ Dual pipeline: behavioral + sequential
```

**Why this matters:** This is the academic lineage the committee asked for. It answers "who was first" and positions your system as the natural next step — not a disconnected engineering project.

---

## Fix 2 — Rewrite "Traditional Gaps" Bullet (CRITICAL)

**Where:** "Problem Statements & Motivation" slide, "Traditional Gaps" section  
**Source:** `thesis/Captsone/chapter2_nba_section.tex` (failure modes paragraph)

### Current (weak):
> - Limited search for both keyword & long query  
> - Blind to recent shift in reading intents  

### Replace with:
> **Traditional NBA systems (FPMC, GRU4Rec, SASRec) share three failure modes:**
> 1. **ID-only representations** — new or infrequent items have undertrained embeddings; two visually identical books with different IDs are treated as unrelated
> 2. **Offline-only inference** — model weights are frozen at serving time; a user's shifting intent within a session is invisible to the model
> 3. **Single-signal** — systems model either behavioral co-purchase structure *or* sequential intent, never both

Then map each "Our Solution" bullet 1-to-1 to these three failures. This makes the motivation self-explanatory to the committee.

---

## Fix 3 — Replace Evaluation Table (CRITICAL)

**Where:** "End-to-end Evaluation" slide  
**Source:** `thesis/Captsone/chapter5_comparison_table.tex`

### Current table (REMOVE):
Missing GRU4Rec, SASRecF, and System A∪B. GRU-SeqDQN listed as a "baseline" when it is actually your prior system — this confuses the committee.

### New table (USE THIS):

| Method | HR@10 | NDCG@10 | Notes |
|---|---|---|---|
| Random | 0.100 | 0.045 | Lower bound |
| Content Baseline (BGE-M3 profile mean) | 0.435 | 0.302 | No sequential modelling |
| GRU4Rec — Hidasi et al. 2016 | 0.770 | 0.498 | RNN baseline |
| SASRecF — Kang & McAuley 2018 | 0.793 | 0.523 | Transformer baseline (from scratch) |
| Pipeline B — DIF-SASRec (ours) | 0.774 | 0.502 | Sequential pipeline |
| Pipeline A — Cleora + BGE-M3 (ours) | 0.905 | 0.539 | Behavioral pipeline |
| **System A∪B (ours — full system)** | **0.974** | **0.557** | **True end-to-end** |

**Evaluation protocol:** Sampled evaluation, N=99 negatives, leave-last-out split, 100,000 users, seed=42.

**Key talking point:** "9 in 10 users find a relevant book in the top 10. When both pipelines are combined, 97 in 100 users do — that 7-point gain is the value of the dual-pipeline routing."

> **Note on GRU-SeqDQN:** Move the HR@10=0.082 result from this table into the lineage slide (Fix 1) as "our prior system, superseded." It is not an academic baseline — it is evidence that the prior approach failed and motivates this project.

---

## Fix 4 — Add Holistic System Slide (IMPORTANT)

**Insert after:** evaluation table slide  
**Source:** `thesis/Captsone/chapter5_holistic.tex`

### New Slide: "System A∪B — True End-to-End Evaluation"

```
Routing Logic (app/api/routes/recommend.py):
  ├── < 5 interactions → cold-start random path
  └── ≥ 5 interactions → dual-pipeline engine
        ├── Pipeline A: Cleora KNN → BGE-M3 re-rank
        └── Pipeline B: DIF-SASRec → content veto (τ=0.30)
        └── NBA engine: union → deduplicate → Top-10

Coverage:
  97.4% of test users received personalized results
  2.6% excluded (below cold-start threshold or index miss)

Online Fine-Tuning (Phase 2):
  Every click → AgentPool borrows one DIFSASRecAgent
  → load user weights → 1 gradient step → save back
  In-session HR@10 delta: [DELTA_RESULT] (zero-click → post-click)
  8 agents × 148 MB VRAM = 1.18 GB total footprint
```

**Why this matters:** This is the slide that answers "that's not end-to-end." Show the routing logic, coverage number, and the Phase 2 online uplift.

> **BLOCKER:** `[DELTA_RESULT]` must be filled by Khoa before the defense. See the section below.

---

## Fix 5 — Expand Latency Optimization Slide (MODERATE)

**Where:** "Search Pipeline — 18.6× Latency Reduction"  
**Current:** Only says "NLLB int8 quantisation and pre-warming"  

### Add a per-component breakdown table:

| Component | Before | After | Optimization applied |
|---|---|---|---|
| NLLB Translation | 204.51 ms | 1.19 ms | int8 ONNX quantization + model pre-warm at startup |
| BGE-M3 Encoding | 97.89 ms | 30.12 ms | Batched inference, GPU CUDA path |
| HNSW ANN Search | ~50 ms | ~28 ms | ef_search tuning (already fast by design) |
| **E2E warm cache** | **1,101.99 ms** | **59.20 ms** | **18.6× total** |

**Add cold-cache note:** "First query after restart = 1,204 ms (NLLB loads on demand). All subsequent queries: 59 ms."

**Talking point for committee:** "The dominant win was translation: 204 ms → 1.19 ms, a 171× reduction. int8 quantization alone cut the model to a quarter of its original size with negligible quality loss on Vietnamese→English."

---

## Slide Order After Changes

```
1. Title
2. Table of Contents
3. Problem Statements & Motivation          ← Fix 2: rewrite "Traditional Gaps"
4. [NEW] 15 Years of NBA Research           ← Fix 1: lineage slide
5. Next Best Action System Concept
6. Why Multimodal for Books?
7. Project Objective & Scope
8. System Scope
9. Dataset: Amazon Reviews 2023
10. System Analysis & Architecture (Overall)
11. Text Encoder: BGE-M3
12. Visual Encoder: CLIP
13. Fusion Strategies: Adaptive RRF
14. BM25 + HNSW + RRF Retrieval
15. DIF-SASRec Decoupled Attention
16. Cleora Graph Propagation
17. Phase 1 — Active Search Pipeline
18. Text Encoder — Why BGE-M3?
19. Two Indices, Two Jobs
20. Search Pipeline — 18.6× Latency         ← Fix 5: add component table
21. Phase 2 — Dual Recommendation Pipeline
22. [REVISED] Evaluation Table              ← Fix 3: full 7-row table
23. [NEW] System A∪B — True End-to-End     ← Fix 4: holistic routing slide
24. Results & Future Directions
25. Thank You
```

---

## The [DELTA_RESULT] Placeholder — What It Is and How to Get It

### What it measures
`[DELTA_RESULT]` is the **in-session HR@10 improvement** from online fine-tuning (Phase 2).

Specifically: after a user clicks one item, the system performs one gradient step on the DIF-SASRec model for that user. `[DELTA_RESULT]` measures how much HR@10 improves in the next recommendation compared to the cold (zero-click) state.

- **Zero-click state:** DIF-SASRec recommendation using pretrained weights before any interaction in the current session.
- **Post-click state:** DIF-SASRec recommendation after one gradient step triggered by the first click.
- **Delta = HR@10(post-click) − HR@10(zero-click)**

### Why the committee cares
This number is the entire justification for Phase 2 (the `AgentPool`, per-user `.pt` files, online fine-tuning). Without it, the committee can correctly say: "you built an expensive real-time training system but have no evidence it actually helps."

### How to measure it (Khoa's task)
The measurement requires a simulation experiment:

```python
# Pseudocode for the delta measurement
for each user in eval_users:
    # Step 1: get recommendation with zero-click (pretrained weights only)
    hr_cold = evaluate_user(user, clicks_seen=0)
    
    # Step 2: simulate user clicking the first item in their history
    simulate_click(user, item=history[0])  # triggers AgentPool gradient step
    
    # Step 3: get recommendation again (post-click weights)
    hr_warm = evaluate_user(user, clicks_seen=1)
    
    delta = hr_warm - hr_cold

# Report: mean delta across users, and % of users who improved
```

### What a defensible result looks like
- A positive delta (even +0.5–2 pp) proves Phase 2 is not dead weight.
- Report both the mean delta and the direction (what % of users improved).
- If the delta is near zero, the framing should shift: "Phase 2 does not degrade quality and enables session-level personalization that cannot be captured in offline eval."

### If there is no time to run the experiment
Use a qualitative demonstration: show a before/after example where a user clicks "Dune" and the next recommendation shifts from generic sci-fi toward Frank Herbert / space opera. This is a weaker defense but better than leaving the placeholder blank.

---

## Priority Order for Implementation

| # | Task | Owner | Urgency |
|---|---|---|---|
| 1 | Add NBA lineage slide (Fix 1) | Slides editor | Before defense |
| 2 | Rewrite "Traditional Gaps" (Fix 2) | Slides editor | Before defense |
| 3 | Replace evaluation table (Fix 3) | Slides editor | Before defense |
| 4 | Measure [DELTA_RESULT] | Khoa | Before defense — BLOCKER |
| 5 | Add holistic system slide (Fix 4) | Slides editor (after #4) | Before defense |
| 6 | Expand latency slide (Fix 5) | Slides editor | Day before defense |
