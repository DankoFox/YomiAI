# Handoff — CSoNet 2026 Paper (LNCS)

## State

Paper compiles to **14 pages** (within limit). LNCS format compliant (23/23 checks pass). All build artifacts cleaned.

## What was done

### LNNS → LNCS migration (svproc → llncs)
- `main.tex`: `svproc.cls` → `llncs.cls`, added `T1/fontenc`, removed `url`/`float`/`mainmatter`
- Bib style: `splncs03_unsrt` → `splncs04`
- Added DOIs to all 21 references
- All `[H]` floats → `[tbp]`

### Page trim (16 → 14 pages)
- **§2 Related Work**: collapsed 6 subsections → 4, removed overlap with intro
- **§5 Experiments**: condensed dataset properties from 3 paragraphs → 1
- **§6 Results**: tightened every subsection — ablation merged into one block, robustness/latency/encoder trimmed
- Applied humanizer patterns throughout (redundant signposting, filler phrases, verbose descriptions removed)

### Compliance tooling
- Created `scripts/test/check_lncs_compliance.py` — 23 automated tests
- Created `thesis/lncs_paper_guide.md` — Springer LNCS formatting reference

## Key files

| File | Purpose |
|---|---|
| `thesis/paper/main.tex` | Entry point, preamble, section includes |
| `thesis/paper/sections/02_related_work.tex` | Related work (trimmed) |
| `thesis/paper/sections/05_experiments.tex` | Experiments (trimmed) |
| `thesis/paper/sections/06_results.tex` | Results (trimmed) |
| `thesis/lncs_paper_guide.md` | Springer LNCS formatting rules |
| `scripts/test/check_lncs_compliance.py` | 23-test compliance checker |

## Build

```bash
docker run --rm -v "$(pwd)/thesis/paper:/paper" texlive/texlive:latest \
  bash -c "cd /paper && latexmk -pdf -interaction=nonstopmode main.tex"
```

Cleans build artifacts:
```bash
rm -f thesis/paper/main.{pdf,aux,bbl,blg,fdb_latexmk,fls,log,out}
```

## Remaining work / known issues

1. **Abstract**: ~140 words, target 150–250. Slightly short but acceptable
2. **DOIs**: 13/21 references have DOIs — could add 8 more
3. **Figures**: `figures/` directory may need final hi-res versions
4. **Blind review**: if CSoNet requires double-blind, add `\documentclass[anonymous]{llncs}`
5. **Abstract** may need expansion to hit 150+ word target
6. No local texlive installed — all compilation via Docker (5.5 GB image)
