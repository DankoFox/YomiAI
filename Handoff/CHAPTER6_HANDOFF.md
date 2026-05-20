# Chapter 6 Handoff

## Context

This is a LaTeX capstone thesis about a multimodal book recommendation system. The main working directory is `Captsone/` (note the typo in the folder name — keep it, the build depends on it).

Chapters 1–5 and Chapter 7 are done. **Your job is Chapter 6.**

---

## What changed in the app since the screenshots were taken

Three UI changes happened after the original screenshots were captured. Chapter 6 text and images need to reflect all three.

### 1. Cart button removed everywhere

The shopping cart button has been removed from the header and from every book card. It no longer exists in the app.

### 2. "Not Interested" button added to every card

Both the Search result cards and the Recommendation cards now have a **"Not Interested"** button (rose/red colour). Clicking it:
- Immediately removes the book from the current recommendation list (frontend filter)
- Stores the item in a per-user Redis blacklist (`user:{id}:blocked`) so it won't appear in future recommendation fetches

### 3. Emojis removed from the UI

All emoji characters have been stripped from the interface (👤 🔖 🛒 📖 🖼 were all removed). The UI now uses plain text and SVG icons only.

---

## Files you need to edit

All chapter 6 `.tex` files are in `Captsone/sections/6.Application/`.

```
6.1.AirQualityProblem.tex   ← Application overview (mostly fine, check for cart refs)
6.5.DataVisualization.tex   ← Interface description (cart refs, radar chart, strip)
6.6.Result.tex              ← Demo walkthrough (cart/reward refs throughout)
6.8.OtherFunctions.tex      ← Has a full "Shopping Cart" subsection to replace
6.3.DataIngestion.tex       ← Probably fine, just verify
6.9.SystemPerformance.tex   ← Probably fine, just verify
```

---

## Specific text fixes needed

### `6.5.DataVisualization.tex`

**Line ~28 (header description):**
```
The controls area provides a dark/light mode toggle, a shopping cart button displaying
the current in-session item count, and a toggle button that collapses or expands the right panel.
```
→ Remove the cart button mention. The controls area now only has the dark/light mode toggle and the right-panel collapse toggle.

**Line ~41 (search card interaction controls):**
```
Each card provides three interaction controls: Interested (logs a click), Ask AI (opens a
streaming book-description popover), and Add to Cart (logs a cart event).
```
→ Replace with:
```
Each card provides three interaction controls: Interested (logs a click and triggers a
DIF-SASRec gradient step), Ask AI (opens a streaming book-description popover), and
Not Interested (hides the book from future recommendations).
```

**Line ~50 (input-sequence strip):**
```
This strip shows the user's most recent click and cart interactions — up to eight items —
in chronological order...
```
→ Replace `click and cart interactions` with `click interactions`. Remove the em dash pair too (use commas).

**Line ~62 (radar chart description):**
```
The Engagement Signals card (full width) renders a ProfileRadar radar chart visualising
five dimensions derived from the session's interaction history: click rate, cart rate,
skip rate, interaction count, and recency.
```
→ Remove `cart rate,` — the chart now shows four dimensions: click rate, skip rate, interaction count, and recency.

### `6.6.Result.tex`

**Line ~37 (figure caption):**
```
... four interaction controls: Interested, Skip, Ask AI (streaming LLM popover), and Add to Cart.
```
→ Replace `Add to Cart` with `Not Interested`.

**Lines ~42–44 (interaction description):**
```
Interested logs a click event (reward 1.0), updates the in-memory user profile, and triggers
a DIF-SASRec gradient step.
Add to Cart logs a cart event (reward 5.0), appends the item to the in-session cart, and
triggers a gradient step.
```
→ Rewrite as:
```
Interested logs a click event, updates the in-memory user profile, and triggers a
DIF-SASRec gradient step.
Not Interested stores the item in a per-user blocked list and removes it from
the recommendation panels immediately, without triggering a training step.
```

**Line ~68 (strip description):**
```
This strip shows the user's most recent click and cart interactions — up to eight items —
in chronological order...
```
→ Same fix as 6.5: `click interactions`, remove em dash.

**Lines ~77–78 (online learning section):**
```
Every click or cart event triggers a sampled softmax gradient step...
```
→ `Every click event triggers a sampled softmax gradient step...`

### `6.8.OtherFunctions.tex`

**The entire "Shopping Cart" subsection (lines ~12–17) must be replaced:**

Current text:
```latex
\subsection{Shopping Cart}

A cart button in the header tracks items added during the current session and displays
the running item count.
When a user selects Add to Cart on any book card, the item is appended to the in-session
cart array, the header count increments, and a success notification is shown.
The cart state is held in React component state only — it is not persisted to the backend —
and resets on page reload.
The cart interaction also dispatches a cart event to the POST /interact endpoint (reward 5.0),
which triggers a DIF-SASRec gradient step identical to the click path.
```

Replace with:
```latex
\subsection{Not Interested}

Each book card provides a Not Interested button.
Clicking it immediately removes the item from the current recommendation panels on the
frontend and sends a \texttt{POST /interact} request with \texttt{action = "not\_interested"}.
The backend stores the item identifier in a per-user Redis set (\texttt{user:\{id\}:blocked});
subsequent calls to \texttt{GET /recommend} filter out any blocked items before enriching
the candidate lists, so the dismissed book will not reappear across sessions.
No gradient step is triggered for not-interested events.
```

**Lines ~21–23 (interaction logging subsection):**
```
The POST /interact endpoint accepts user_id, item_id, and action (click, skip, or cart).
The backend assigns the corresponding reward, updates the in-memory user profile, and pushes
the event to the Redis queue for asynchronous MongoDB persistence.
For click and cart actions, the endpoint borrows a DIF-SASRec agent from the pool...
```
→ Update to:
```
The POST /interact endpoint accepts user_id, item_id, and action (click, skip, or not_interested).
For click actions, the endpoint borrows a DIF-SASRec agent from the pool, loads the user's
personal checkpoint, runs one sampled softmax gradient step, saves the updated checkpoint,
and returns the resulting sasrec_loss value.
Not-interested actions are written to a per-user Redis blocked set with no training step.
The frontend appends the returned loss value to the sparkline on response, providing
sub-second visual confirmation that the model has updated.
```

---

## Screenshots to retake (5 images)

All images live in `Captsone/images/chapter6/`. Replace the following files with fresh screenshots from the running app.

| File | What to capture | Key things to show |
|---|---|---|
| `fig_app_interface.png` | Full app with both panels visible | No cart button in header; user badge has no emoji |
| `fig_search_text.png` | Search results for a text query | Cards show **Interested**, **Ask AI**, **Not Interested** buttons; no cart |
| `fig_search_multimodal.png` | Search results with both text + image query active | Same — three buttons, no cart; CLIP badge visible |
| `fig_rec_pab.png` | Recommendations tab, warm user, People Also Buy column visible | No cart in header; recommendation cards show correct buttons |
| `fig_rec_yml.png` | Recommendations tab, You Might Like column | DIF-SASRec cards, same button set |

To run the app for screenshots:
```bash
# Terminal 1 — infrastructure
docker-compose up -d

# Terminal 2 — backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3 — frontend
cd frontend
npm install   # first time only
npm run dev
```

Frontend is at `http://localhost:5173`. Use a user ID that has at least 5 interactions to get the warm/personalised recommendation views.

---

## Figure caption that references the old interface

After retaking `fig_app_interface.png`, update its caption in `6.5.DataVisualization.tex` (the `\caption{}` block under `\label{fig:app_interface}`):

Current caption mentions *"cart, and right-panel toggle"*. Update to *"dark/light mode toggle and right-panel toggle"*.

---

## What you do NOT need to touch

- Chapters 1–5 and Chapter 7 are finalised — do not edit them.
- `Captsone/sections/6.Application/6.2.DataDescription.tex` — data description, no UI references.
- `Captsone/sections/6.Application/6.4.DataPreparation.tex` — data pipeline, no UI references.
- `Captsone/sections/6.Application/6.7.DataRetrieval.tex` — retrieval details, no UI references.
- All backend code changes are already committed — you only need to edit `.tex` files and replace images.

---

## Useful skills available in this Claude Code session

- `/humanizer` — removes AI writing patterns (em dashes, rule-of-three, vague language). Run it on any section after editing.
- `/format-latex` — enforces strict LaTeX citation rules with `\cite{}`.
- `/review-latex` — reviews tone, structure, and LaTeX syntax of a draft.

---

## Build command (sanity check after edits)

```bash
cd Captsone
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Or open `Captsone/main.tex` directly in Overleaf / TeXstudio.
