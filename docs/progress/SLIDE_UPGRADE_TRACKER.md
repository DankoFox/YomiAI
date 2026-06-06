# Phase 2 Slide Upgrade Tracker
**Goal:** Transition Defense Deck from Phase 1 (BLaIR/CLIP) to Phase 2 (Cleora/DIF-SASRec/BGE-M3).
**Reference:** `docs/planning/phase2_slide_upgrade_analysis.md`

## 🔴 Critical Path: Structural Replacements
- [x] **NEW-SCOPE:** Replace Slide 5 (English-only) with Multilingual/Online Scope.
- [ ] **NEW-ARCH:** Replace Slide 29 (BLaIR Architecture) with Dual-Mode Architecture.
- [ ] **NEW-RESULTS:** Replace Slide 26 (BLaIR+CLIP results) with HR@10=0.9736 results.
- [ ] **NEW-ACH:** Replace Slide 37 (Future Plans) with Phase 2 Achievements.

## 🟠 Pillar Transitions: New Technical Slides
- [ ] **NEW-01 (BGE-M3):** Explain why BLaIR was abandoned for robust fuzzy-query handling and pipeline unification.
- [ ] **NEW-02 (Cleora):** Introduce the behavioral graph Markov equations.
- [ ] **NEW-03 (DIF-SASRec):** Explain decoupled attention and intent modeling.
- [ ] **NEW-04 (Union HR):** Mathematically justify the 0.9736 hit rate.

## 🟡 Refinement: Data & Logic Updates
- [ ] **Slide 9:** Update "Why Multimodal" to include graph signal.
- [ ] **Slide 14/15:** Reframe CLIP as visual-search only, not primary text encoder.
- [ ] **Slide 19:** Update scale from 38K items to 3M catalogue items.
- [ ] **Slide 20:** Update token limit logic (BLaIR 512 -> BGE 64 optimized).
- [ ] **Slide 30:** Update Orchestrator logic with unified BGE-M3 embedding routing.
- [ ] **Slide 31:** Update Latency from ~1100ms to 59ms warm-cache.

## ✅ Final Validation (Gate Check)
- [ ] **Pass 1:** No mentions of BLaIR or Late Fusion fixed-beta.
- [ ] **Pass 2:** All numbers match Capstone Report / Study Guide exactly.
- [ ] **Pass 3:** All equations have term-by-term glossaries.
- [ ] **Pass 4:** Master Order matches Section 4 of Analysis.
