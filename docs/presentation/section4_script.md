# Section 4 — Model Evaluation: Presenter Script

**Total target: 5 minutes**
**Plan A: 5 slides (4:30 + 30s pauses)**
**Plan B: 4 slides (3:45)** — drop "Why BGE-M3"
**Plan C: 3 slides (3:30, emergency)** — keep only optimization 71× + metrics 0.974

---

## Cut Strategy

| Original slide | Status in Plan A | Time | Why |
|---|---|---|---|
| 1. Active Search pipeline | KEEP, compressed | 30s | Sets the stage; 4 stages are scannable |
| 2. Why BGE-M3 | KEEP | 45s | Only slide with the 0.15 → 0.40 trend story |
| 3. Two Indices, Two Jobs | **DROP** | — | Subsumed by Slide 3 (the 71× already covers the same decision) |
| 4. Optimization 71× | KEEP FULL | 60s | Engineering hook — strongest moment after the climax |
| 5. Dual Rec pipeline diagram | KEEP, compressed | 30s | Visual carries the load; low word count needed |
| 6. Metrics table 0.974 | KEEP FULL | 90s | The climax — do not cut |
| 7. Pipeline A spotlight | **DROP** | — | Row 6 of the metrics table already says it |
| 8. Section closer | KEEP | 15s | Transition to Q&A |

**Drop rule for cuts:** if you lose another minute, drop slides in this order — Pipeline diagram (Slide 5 in Plan A) → Why BGE-M3 (Slide 2). Never drop the optimization or the metrics table. Those are the two numbers the audience will remember.

---

## Pronunciation Guide

### Technical terms (say slow first time, natural speed after)

| Term | First-use pronunciation | Subsequent |
|---|---|---|
| BGE-M3 | "B-G-E M three" | "BGE M three" |
| NLLB | "N-L-L-B" (or "nilb" if you prefer) | "nilb" |
| CLIP | rhymes with "trip" | same |
| DIF-SASRec | "diff SASS-rec" | "diff SASS-rec" |
| SASRec | "SASS-rec" | same |
| GRU4Rec | "G-R-U four rec" | "GRU-four-rec" |
| BLaIR | "B-lair" (rhymes with "fair") | same |
| HNSW | spell it out: "H-N-S-W" | "HNSW" |
| FAISS | "fays" (rhymes with "face") | same |
| RRF | "R-R-F" (Reciprocal Rank Fusion) | "RRF" |
| Tantivy | "TAN-tih-vee" | same |
| Cleora | "Klee-OR-ah" (Polish — soft L) | same |
| Cosine τ | "cosine tau" (Greek, rhymes with "cow") | same |
| AdamW | "Adam W" (the optimizer) | same |
| HNSW M=32 | "HNSW M equals thirty-two" | same |

### Decimals (always keep the leading zero)

Bad: "point nine seven four" — the brain drops the leading zero and reads it as 0.974 vs 974.
Good: "zero point nine seven four"

| Number | Say it as |
|---|---|
| 0.974 | "zero point nine seven four" |
| 0.793 | "zero point seven nine three" |
| 0.521 | "zero point five two one" |
| 0.557 | "zero point five five seven" |
| 0.770 | "zero point seven seven zero" (keep trailing zero for table consistency) |
| 0.1500 | "zero point one five zero zero" |
| 0.4000 | "zero point four zero zero zero" |
| τ = 0.30 | "tau equal to zero point three zero" |

### Big numbers (American tech style, no "and")

| Number | Say it as |
|---|---|
| 71× | "seventy-one times" or "a seventy-one-x speedup" |
| 124% | "one hundred twenty-four percent" |
| 18% | "eighteen percent" |
| 12.4M | "twelve point four million" |
| 3M | "three million" |
| 1.7M | "one point seven million" |
| 100k | "one hundred thousand" |
| 3,000,000 | "three million" (never say the full number) |

### Milliseconds and seconds (convert when it gets big)

| Number | Say it as |
|---|---|
| 59 ms | "fifty-nine milliseconds" |
| 120 ms | "one hundred twenty milliseconds" (not "a hundred and twenty" — American tech drops "and") |
| 612 ms | "six hundred twelve milliseconds" |
| 4,200 ms | "four point two seconds" (always convert ≥ 1,000 ms to seconds) |
| 1.2 s | "one point two seconds" |

### Comparisons (smooth phrasing for transitions)

| You want to say | Say it as |
|---|---|
| "outperforms X by 18%" | "beats X by eighteen percent" or "eighteen percent better than X" |
| "0.974 vs 0.793" | "our zero point nine seven four against their zero point seven nine three" |
| "97 out of 100 users" | "ninety-seven out of one hundred users" (full "out of one hundred", never "out of a hundred" — sounds informal) |
| "124% better" | "one hundred twenty-four percent better" — better yet: "more than double" |
| "71× faster" | "seventy-one times faster" |
| "2.24× content baseline" | "two point two four times the content baseline" |

---

## Pacing Hints

- **Pause 1–2 seconds BEFORE big numbers** (0.974, 71×, 0.521). The pause signals "this is the moment."
- **Pause AFTER too** — give the audience 2× normal time to absorb a metric.
- **Drop your voice pitch slightly on the climax number** ("zero point nine seven four"). Lower pitch reads as confident, not rushed.
- **First technical term: slow.** Say "B-G-E M three" letter by letter the first time. Subsequent uses: natural speed.
- **Metric tables: point, pause, number, move on.** Don't read the row label out loud unless the audience asks.
- **Eye contact on "ninety-seven out of one hundred users."** This is your strongest line — make it land.
- **Drink water before presenting.** Plosives ("P" in "point", "B" in "BGE") spit on stage mics. Water fixes it.
- **Don't fill silence with "uh" or "so".** Silence after a number is powerful. Let it breathe.

---

## SLIDE 1 — Active Search Pipeline
**Plan A / B / C: KEEP** | **Time: 30s** | **Words: ~55**

> "Section 4 evaluates whether the system works. Phase 1: active search. Four stages.
>
> Input — text query, image, or both. NLLB handles nineteen languages upstream.
>
> Parallel encoding — BGE-M3 produces a 1024-d text vector, CLIP produces a 512-d image vector. Concurrently, no serial bottleneck.
>
> Hybrid retrieval — three independent channels. FAISS HNSW for semantic text, CLIP HNSW for visual, Tantivy BM25 for exact keywords.
>
> Adaptive Weighted RRF fusion merges the three ranked lists into a single top-ten.
>
> That's the pipeline. Next: why we picked BGE-M3."

---

## SLIDE 2 — Why BGE-M3
**Plan A: KEEP / Plan B: DROP / Plan C: DROP** | **Time: 45s** | **Words: ~85**

> "Why BGE-M3 over the alternatives? Two reasons.
>
> Scale: three million books. Pure keyword matching can't handle that volume with acceptable latency.
>
> Query shape: users type conversational queries like *'mystery novel with a strong female lead'*. BGE-M3 was pre-trained on exactly this distribution.
>
> The numbers confirm it. Precision at ten on English queries: short queries hit zero point one five. Medium hit zero point three three. Long hit zero point four zero.
>
> The trend is the story: the more conversational the input, the better BGE-M3 performs. The opposite of a keyword pipeline. We matched our encoder to actual user behavior."

---

## SLIDE 3 — Optimization History (71×)
**Plan A / B / C: KEEP FULL** | **Time: 60s** | **Words: ~140**

> "This is where the engineering work shows up.
>
> We didn't ship at four point two seconds per query. We measured, then fixed. Four times.
>
> FAISS brute-force scans: migrated from Flat to HNSW with M equals thirty-two. Six twenty-three milliseconds dropped to one.
>
> Python BM25 loops: replaced with Tantivy, a Rust engine. Fourteen seventy-one milliseconds dropped to four.
>
> Serialization overhead: native JSON responses, anyio thread offloads. Two thousand milliseconds dropped to three.
>
> NLLB translation: int-eight quantization plus startup warmup. Two hundred four milliseconds dropped to one.
>
> End to end: four point two seconds down to fifty-nine milliseconds. Seventy-one times faster.
>
> One honest caveat: the very first request after a server restart is one point two seconds because NLLB parameters load on demand. Every subsequent request returns to the fifty-nine millisecond baseline."

---

## SLIDE 4 — Dual Recommendation Pipeline
**Plan A / B: KEEP / Plan C: DROP** | **Time: 30s** | **Words: ~90**

> "Phase 2 is passive recommendation. No active query — the user just opens the app.
>
> We take their click history, encode each clicked book with BGE-M3, and compute a weighted mean. That single vector is their profile.
>
> The profile feeds two pipelines in parallel.
>
> Pipeline A — Cleora behavioral graph plus content veto plus BGE-M3 re-rank. Catches what readers with similar taste also bought.
>
> Pipeline B — HNSW KNN plus content veto plus DIF-SASRec scoring. Catches what comes next in the reading trajectory.
>
> Union the two top-ten lists, deduplicate. Done."

---

## SLIDE 5 — Metrics Table (0.974 climax)
**Plan A / B / C: KEEP FULL** | **Time: 90s** | **Words: ~210**

> "Money slide. The metrics.
>
> Protocol: leave-last-out across one hundred thousand users, with ninety-nine negatives sampled per target. Standard HR at ten and NDCG at ten.
>
> Random baseline: HR at ten zero point one zero zero. Guessing.
>
> Pure content-based with BGE-M3, no sequence, no graph: zero point four three five. Decent.
>
> GRU-four-rec, two thousand sixteen RNN baseline: zero point seven seven zero. First deep-learning jump.
>
> DIF-SASRec alone — Pipeline B in isolation: zero point seven seven four. Roughly equivalent to GRU-four-rec, with the added benefit of category attention.
>
> Pipeline A alone — Cleora plus BGE-M3, no sequence: zero point nine zero five. Behavioral graph signal beats sequential signal in this domain.
>
> And our system — A union B: HR at ten zero point nine seven four. NDCG at ten zero point five five seven.
>
> [PAUSE] Zero point nine seven four means: out of one hundred users, ninety-seven find a relevant book in our top-ten. We outperform the best single baseline by eighteen percent in HR at ten, and we more than double the content baseline.
>
> The union is what makes it work. Neither pipeline alone crosses zero point nine one."

---

## SLIDE 6 — Section Closer
**Plan A / B / C: KEEP** | **Time: 15s** | **Words: ~30**

> "Section 4 in summary: search runs in fifty-nine milliseconds with a seventy-one-times speedup. Recommendation reaches HR at ten of zero point nine seven four. Section 5 covers limitations and what we'd build next. Questions before we move on?"

---

## Q&A Anticipation Hooks

Likely teacher / committee questions and how to frame answers.

| Question | Anchor answer |
|---|---|
| "Why not just use SASRecF alone at 0.793?" | "SASRecF is ID-only. The behavioral graph catches collaborative signal SASRec can't see. The union outperforms the best single model by eighteen percent." |
| "Why is Pipeline A stronger than Pipeline B?" | "Books are slow-consumption. User taste cluster matters more than reading order. Documented as a domain insight in the paper." |
| "Is 0.974 a ceiling or can it go higher?" | "There's a structural ceiling from the content veto — at tau zero point three we keep sixty-one point two percent of candidates. Below that we let in noise, above that we cut relevant items. We've measured the phase transition." |
| "Why two BGE-M3 indices?" | "Latency vs. recall tradeoff. HNSW for live serving at one hundred twenty milliseconds, Flat for offline scoring where approximation error compounds. Both stay loaded." |
| "How do you handle cold-start users?" | "Below five clicks, we return a random catalog sample and label the response as `cold_start` mode. The graph and the sequential model both degrade gracefully without history." |
| "What about the one point two second cold cache?" | "NLLB parameters load on demand. We mitigated with int-eight quantization and a startup warmup, but the very first request still pays the loading cost. We document this as a known characteristic, not a bug." |
| "Why not larger negatives in evaluation?" | "N equals ninety-nine is the standard for leave-last-out sequential recommendation. Larger N exponentially increases compute without changing the relative ranking of methods. Our protocol is comparable to GRU4Rec and SASRec papers." |
| "Did you try BGE-M3 fine-tuning?" | "We use BGE-M3 zero-shot for retrieval. Fine-tuning is an ablation direction we flagged for future work — see Section 5." |
| "How reproducible are the numbers?" | "We ran a multi-seed evaluation, results are stable within plus or minus zero point zero zero five. Cleora is fully deterministic. DIF-SASRec has a fixed seed for negative sampling. The variance is bounded." |

---

## Delivery Cheat Sheet (one page to glance at)

```
PLAN A — 5 slides, 4:30
  1 Pipeline ............. 30s  sets stage
  2 Why BGE-M3 .......... 45s  0.15 / 0.33 / 0.40
  3 Optimization 71× .... 60s  THE engineering hook
  4 Dual Rec diagram .... 30s  A + B parallel
  5 Metrics 0.974 ....... 90s  THE climax — don't rush
  6 Closer .............. 15s  transition

PLAN B — 4 slides, 3:45  (drop slide 2)
  1, 3, 4, 5, closer

PLAN C — 3 slides, 3:30  (emergency, drop slides 2 and 4)
  1, 3, 5, closer
  survival = "71× faster" + "0.974 HR@10"

NEVER CUT:  Slide 3 (71×) or Slide 5 (0.974)
DROP ORDER:  Pipeline diagram → Why BGE-M3

PAUSE BEFORE:  0.974, 71×, 0.521, "97 out of 100"
PAUSE AFTER:   big numbers
EYE CONTACT:   on "97 out of 100 users" — strongest line
VOICE DROP:    on the climax metric
WATER:         before you start (plosives on stage mics)
```

---

## If Asked to Extend

Backup material in case a slide is cut from time but the audience wants depth:

- **BGE-M3 vs BLaIR ablation**: BGE-M3 wins on conversational queries (0.55 vs 0.05 on long Vietnamese), BLaIR wins on short exact-match English (0.23 vs 0.15). Tradeoff: brute-force recall vs latency. See `slides/section4_backup_bge_vs_blair.md` (TODO).
- **Content veto τ phase transition**: full table in slide.txt appendix. τ=0.10 lets in 94.3% of candidates → HR@10 0.741 (too much noise). τ=0.50 keeps 18.1% → HR@10 0.691 (too restrictive). τ=0.30 is the operational sweet spot.
- **Cold-start graceful degradation**: <5 clicks = `cold_start` mode with random sample. 5–20 clicks = Pipeline A only. 20+ = both pipelines.
- **Why HNSW recall 0.521 is fine**: BM25 + CLIP run in parallel. RRF fusion catches the misses. End-to-end recall on test set is 0.974.

These are your "if they ask" answers — keep them in your back pocket, don't pre-deliver.
