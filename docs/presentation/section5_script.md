# Section 5 — Conclusion: Presenter Script + Rewrite

**Target time: 60–90 seconds**
**Structure: What we built / Limitations / What's next**

---

## Design Rules (apply these to any future slide rewrite)

1. **One idea per bullet.** No noun stacks like "real-time delta item ingestion transformations." If a bullet needs more than 15 words, split it.
2. **Active voice.** Subject–verb–object. "We built X" not "X was built by us" or worse, "an X was built."
3. **Add limitations.** Judges scan for self-awareness. A slide that says "we built everything perfectly" reads as naive. Three honest bullets beats zero.
4. **Concrete over abstract.** "59 ms" beats "low latency." "3M items" beats "massive scale." Numbers anchor claims.
5. **No marketing words.** Drop: "robust," "scalable," "leverage," "seamless," "cutting-edge." All empty calories.
6. **One future item = one sentence + one reason.** "Streaming FAISS: add new books without restart" tells WHAT and WHY in 7 words.

---

## SLIDE TEXT — Drop-in Replacement

```markdown
### SECTION 5: RESULTS, LIMITATIONS & FUTURE DIRECTIONS

#### What we built
* Dual-pipeline recommendation: behavioral graph + sequential transformer, combined as a union
* Multimodal search: text queries and cover images, 59 ms end-to-end
* Online fine-tuning: every click updates that user's model

#### Limitations
* Adding new books requires a server restart to rebuild FAISS indices
* Single-GPU deployment only (16 GB VRAM); no horizontal scaling
* Cold-start users (<5 clicks) get random recommendations, not personalized

#### What we'd build next
* Streaming FAISS: add new books without restarting the server
* Model registry: shared model store for multi-server deployment
* Hard-negative mining: stronger training signal for DIF-SASRec

#### THANK YOU FOR LISTENING
*Questions & Discussion*
```

### Why this beats the original

| Original | Rewrite | Why |
|---|---|---|
| "Built an optimized dual pipeline recommendation system environment" | "Dual-pipeline recommendation: behavioral graph + sequential transformer, combined as a union" | Says WHAT, not adjectives |
| "Online per user loop updates - online fine-tuning execution cascades tracking with every incoming customer interaction" | "Online fine-tuning: every click updates that user's model" | 8 words vs 16 |
| "Scale active FAISS index infrastructures to natively support real-time delta item ingestion transformations without triggering full application restarts" | "Streaming FAISS: add new books without restarting the server" | Specific, no jargon |
| (no limitations section) | 3 honest bullets | Judges scan for self-awareness |
| "Replace static local model file storage deployments (.pt) with centralized enterprise model registries designed for clustered multi-server high-availability configurations" | "Model registry: shared model store for multi-server deployment" | No acronym soup |

---

## Presenter Script

**Time: 60–90 seconds** | **Words: ~120**

> "Section 5. Three things: what we built, what we couldn't solve, and what comes next.
>
> What we built: dual-pipeline recommendation combining a behavioral graph with a sequential transformer, multimodal search that handles text queries and cover images in fifty-nine milliseconds, and online fine-tuning that updates each user's model on every click.
>
> What we didn't solve — and this matters for honesty. Adding new books requires a server restart to rebuild the FAISS indices. The system is single-GPU only. Cold-start users with fewer than five clicks get random recommendations, not personalized.
>
> What we'd build next: streaming FAISS to update indices without restart, a centralized model registry for multi-server deployment, and hard-negative mining to improve the sequential model's training signal.
>
> Thank you. Questions?"

---

## Pronunciation Notes (Section 5 specific)

| Term | Say it as |
|---|---|
| FAISS | "fays" (rhymes with "face") |
| DIF-SASRec | "diff SASS-rec" |
| Hard-negative mining | "hard-negative mining" (no acronym — say all three words) |
| Model registry | "model registry" (no need to expand) |
| Streaming FAISS | "streaming FAISS" or "streaming fays" (your call) |
| 59 ms | "fifty-nine milliseconds" |
| 16 GB | "sixteen gigabytes" |
| <5 clicks | "fewer than five clicks" (not "less than five clicks" — countable noun) |
| 100k | "one hundred thousand" |

---

## Delivery Hints

- **Pacing on limitations:** slower than achievements. The honesty of this section is the credibility move. Don't speed through it.
- **Eye contact on "fewer than five clicks":** this is your most human line. The committee reads vulnerability.
- **Drop pitch on "streaming FAISS":** this is the future-work headline. Make it land.
- **The "Questions?" line:** pause 2 full seconds after saying it. Don't fill the silence. The first questioner is gathering courage.

---

## Q&A Anticipation Hooks (Section 5 specific)

| Question | Anchor answer |
|---|---|
| "Why can't you just rebuild FAISS incrementally?" | "FAISS doesn't natively support incremental inserts. You'd need a custom index wrapper or a different ANN library — PISA, ScaNN, or a streaming variant. We flagged it as future work because the implementation is non-trivial and would require benchmark re-validation." |
| "Why single-GPU? Why not multi-GPU?" | "The agent pool is sized to fit one sixteen-gigabyte RTX fifty-oh-six Ti. Adding GPUs requires sharding users across agents, which means cross-shard candidate retrieval — a real engineering problem. We chose single-GPU to ship the demo; multi-GPU is the production path." |
| "What's hard-negative mining?" | "When training DIF-SASRec, we currently sample negatives uniformly from the catalog. Hard negatives are items the model thinks are relevant but aren't — they sharpen the training signal. There's a planning doc on this in our docs folder." |
| "How long would streaming FAISS take to build?" | "Depends on the library. Wrapping an existing HNSW index for incremental updates is a few weeks. Migrating to a streaming-native library like PISA is one to two months plus re-benchmarking." |
| "What's the biggest risk if you deploy this tomorrow?" | "The restart requirement for new books. A book that goes viral at 9am and we don't notice until 4pm means six hours of missed recommendations. That's the production-readiness gap." |
| "Did you do user studies?" | "Quantitative metrics on one hundred thousand user profiles, no live user studies. The thesis defense focuses on offline HR at ten and NDCG at ten. Live A-B testing is the next milestone." |
| "Can the system handle ten thousand concurrent users?" | "Single-GPU no. The agent pool saturates around fifty to one hundred concurrent recommendation requests. Multi-server deployment is the future work item, and it requires the model registry." |

---

## Slide Order Reminder (if 2 indices moved to appendix)

| Original | New location | Script impact |
|---|---|---|
| Section 4: "Two Indices, Two Jobs" | **Appendix: new slide** | Section 4 script unchanged (Slide was already dropped in 5-min cut) |
| Section 4: "BGE-M3 vs BLaIR ablation" | Stays in appendix (already there) | No change |
| Section 4: "Content veto τ phase transition" | Stays in appendix (already there) | No change |
| Section 5: Conclusion | Stays in Section 5 | This script |

The 5-minute Section 4 cut is **unchanged** by the 2-indices move. Just remove the slide from Section 4 deck and add a fresh slide to the appendix with the same table.

---

## Appendix Slide Addition (2 Indices, Two Jobs)

If you want a script for the new appendix slide, here's a 30-second version:

> "One technical decision that often gets misunderstood: we run two BGE-M3 indices in parallel — HNSW for live search, Flat for offline scoring. HNSW is approximate at one hundred twenty milliseconds and zero point five two one recall. Flat is exact at six hundred twelve milliseconds. HNSW gaps are caught by BM25 running in parallel, and the final merge uses Adaptive RRF. Visual search runs on a separate CLIP space."

**Time: 30s** | **Words: ~65**

This is the speaker-script version of the original Section 4 slide content, now appendix-bound.
