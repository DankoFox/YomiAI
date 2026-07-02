# LNCS Paper Formatting Guide — Springer Computer Science Proceedings

Extracted from official `Instructions_for_Authors_PDF.pdf` + `LaTeX2e_Proceedings_Template_ZIP` (llncs.cls v2.24, splncs04.bst).

**Target**: CSoNet 2026 (Springer LNCS). **Page limit**: 14 pages including references.

---

## [CLASS SETUP]

```latex
\documentclass[runningheads]{llncs}
\usepackage[T1]{fontenc}
\usepackage{graphicx}
% Optional hyperref (comment out if not needed):
% \usepackage{color}
% \renewcommand\UrlFont{\color{blue}\rmfamily}
% \urlstyle{rm}
```

| Property | Value |
|---|---|
| Base class | `article` (twoside) |
| Text width | 12.2 cm |
| Text height | 19.3 cm |
| Odd/even margin | 63 pt |
| Head separation | 16 pt |
| Font | CMR (Computer Modern Roman) |

### Class Options

| Option | Effect |
|---|---|
| `runningheads` | **(Required)** Enables running headers |
| `envcountreset` | Reset theorem/lemma counters per section |
| `envcountsame` | Use same counter for all theorem-like environments |
| `envcountsect` | Number theorems by section (e.g. Theorem 1.1) |
| `citeauthoryear` | Enable author-year citations instead of numbered |
| `oribibl` | Use plain bibliography style instead of splncs04 |
| `openbib` | Use open-format bibliography |

---

## [PREAMBLE — TITLE, AUTHORS, AFFILIATIONS]

```latex
\title{Your Full Paper Title Here}

% Optional: abbreviated running head (if title > ~60 chars)
\titlerunning{Abbreviated Title}

\author{
  First Author\inst{1}\orcidID{0000-1111-2222-3333} \and
  Second Author\inst{2,3}\orcidID{1111-2222-3333-4444} \and
  Third Author\inst{3}\orcidID{2222-3333-4444-5555}
}

% Running head for top of pages
\authorrunning{F. Author et al.}

\institute{
  Princeton University, Princeton NJ 08544, USA \and
  Springer Heidelberg, Tiergartenstr. 17, 69121 Heidelberg, Germany
  \email{lncs@springer.com}\\
  \url{http://www.springer.com/gp/computer-science/lncs} \and
  ABC Institute, University of Heidelberg, Heidelberg, Germany\\
  \email{\{abc,lncs\}@uni-heidelberg.de}
}

\maketitle
```

### Rules for Author Block

- **Corresponding author**: Must be clearly marked (use `\Envelope` from `bbding` package). Only ONE corresponding author per paper.
- **Email**: Mandatory for corresponding author. Strongly encouraged for all authors.
- **ORCID**: Encouraged for all authors. Use `\orcidID{...}` in `\author{}`.
- **Names**: Must be final before submission — no additions, deletions, or reordering after submission.
- **Multiple family names**: Clarify display format.
- **Author running**: `\authorrunning{F. Author et al.}` — First names abbreviated. If >2 authors, use "et al."

---

## [ABSTRACT]

```latex
\begin{abstract}
The abstract should briefly summarize the contents of the paper in
150--250 words.

\keywords{First keyword  \and Second keyword \and Another keyword.}
\end{abstract}
```

- **Length**: 150–250 words.
- **No footnotes** in abstract.
- **Keywords**: 3–5 keywords separated by `\and`. End with period.

---

## [BODY STRUCTURE]

### Section Headings

| Level | Format | Font |
|---|---|---|
| Title (centered) | `\title{...}` | 14 pt bold |
| 1st-level | `\section{Introduction}` | 12 pt bold |
| 2nd-level | `\subsection{Printing Area}` | 10 pt bold |
| 3rd-level | `\subsubsection{Run-in Heading.} Text follows` | 10 pt bold, run-in |
| 4th-level | `\paragraph{Lowest Level.} Text follows` | 10 pt italic, run-in |

- **Only first 2 levels numbered**. Do NOT use "Section 0" or zero-numbered sections.
- Capitalize nouns, verbs, main words. Skip articles/prepositions/conjunctions.
- First paragraph after section heading is **NOT indented**. Subsequent paragraphs ARE indented.
- Hyphenated headings: capitalize second word if first can stand alone.

### Theorems, Lemmas, Propositions

```latex
\begin{theorem}
Statement here. Run-in heading bold, text in italics.
\end{theorem}

\begin{proof}
Proof text. "Proof" in italics, body in normal font.
\end{proof}
```

Available environments: `theorem`, `definition`, `lemma`, `proposition`, `corollary`, `remark`, `example`, `proof`.

- **Numbering**: Use consecutive numbers (Lemma 1, Lemma 2, ...). NOT section-based (no "Theorem 1.1").
- Exception: Use `envcountsect` class option if section-based numbering is required.

---

## [FIGURES & TABLES]

### Figures

```latex
\begin{figure}
\includegraphics[width=\textwidth]{fig1.eps}
\caption{Caption below the figure.} \label{fig1}
\end{figure}
```

- **Caption position**: BELOW the figure.
- **Format**: Vector graphics (EPS/PDF) preferred. Avoid rasterized images for diagrams.
- **Resolution**: Line drawings ≥ 800 dpi (preferably 1200 dpi).
- **Font size**: No smaller than 6 pt (~2 mm character height) within figures.
- **Color**: NO color in printed text/tables/equations. Color figures OK in electronic version only.
- **Captions**: 9 pt. If short → centered. If >1 line → justified. No period if not full sentence.

### Tables

```latex
\begin{table}
\caption{Table captions ABOVE the table.}\label{tab1}
\begin{tabular}{|l|l|l|}
\hline
...
\end{tabular}
\end{table}
```

- **Caption position**: ABOVE the table.
- Must be editable (not pasted as images).
- Cross-reference all figures/tables in text: `Fig.~\ref{fig1}`, `Table~\ref{tab1}`.

---

## [EQUATIONS]

```latex
\begin{equation}
x + y = z
\end{equation}
```

- Centered, separate line with extra space above/below.
- Numbers in parentheses, right-aligned, consecutive (NOT section-based like (1.1)).
- **NO color** in equations.
- Punctuate equations like normal text.
- Must be editable (not pasted as images).

---

## [CITATIONS & REFERENCES]

### Citation Style

| Pattern | Example |
|---|---|
| Single | `[9]` |
| Multiple | `[4--6, 9]` (numerical order) |
| Author in text | `Miller \cite[9]` or Miller [9] |

- Arabic numbers in **brackets** (not superscript).
- Order: either **alphabetical** (preferred) or **order of citation** — must match the reference list.
- If >6 authors → truncate to first author + "et al."

### Bibliography

```latex
\bibliographystyle{splncs04}
\bibliography{mybibliography}
```

Or inline:

```latex
\begin{thebibliography}{8}
\bibitem{ref_article1}
Author, F.: Article title. Journal \textbf{2}(5), 99--110 (2016)

\bibitem{ref_lncs1}
Author, F., Author, S.: Title of a proceedings paper. In: Editor,
F., Editor, S. (eds.) CONFERENCE 2016, LNCS, vol. 9999, pp. 1--13.
Springer, Heidelberg (2016). \doi{10.10007/1234567890}
\end{thebibliography}
```

- Use `\doi{...}` command for DOIs — strongly encouraged.
- All references in **Latin alphabet**. If original is non-Latin, add "(in Russian)" etc.
- `splncs04.bst` is the standard LNCS BibTeX style (numbered, alphabetic sorting).

---

## [ACKNOWLEDGMENTS & DISCLOSURE]

```latex
\begin{credits}
\subsubsection{\ackname}
This study was funded by X (grant number Y).

\subsubsection{\discintname}
The authors have no competing interests to declare that are relevant
to the content of this article.
\end{credits}
```

- Both are **required**.
- Placed at end of paper, before references.
- 9 pt font, bold run-in heading.

---

## [APPENDIX]

```latex
\appendix
% If single: heading is "Appendix"
% If multiple: heading is "Appendix 1", "Appendix 2", etc.
```

- Must be placed **before references**.
- Continue numbering of tables, figures, equations from main body (no restart).

---

## [PROHIBITED / MUST NOT DO]

| Rule | Detail |
|---|---|
| No page numbers | Springer adds them |
| No running heads | Springer adds them (use `\titlerunning` for custom short title) |
| No color | In text, tables, equations (figures OK in electronic version) |
| No section-based theorem numbers | Use consecutive (Lemma 1, Lemma 2) not "Theorem 1.1" |
| No "Section 0" | No zero-numbered headings |
| No section-based equation numbers | Use (1), (2) not (1.1), (1.2) |
| No Framemaker files | Must be LaTeX or Word (docx) |
| No docm files | Word with macros not accepted |
| No footnotes in abstract | |
| No pasted-in images for tables/equations | Must be editable |
| No font size < 6 pt | In figures |
| No author changes after submission | Names, order, corresponding author all frozen |
| No digital signatures on license | Must be hand-signed |

---

## [CHECKLIST — Before Submission to CSoNet]

1. Source files: `.tex`, `.bib` (or `.bbl`), class file, images (EPS/PDF)
2. Final PDF matching source files exactly
3. License-to-publish agreement, hand-signed by corresponding author
4. Abbreviated running head suggestion (if title > ~60 chars)
5. Correct representation of authors' names clarified
6. Alt text for all figures (accessibility requirement)
7. Disclosure of Interests statement included
8. Page count ≤ **14 pages** including references
9. Abstract 150–250 words
10. References use `splncs04.bst` with DOIs where possible

---

## [DIMENSIONS SUMMARY (from llncs.cls)]

```
textwidth  = 12.2 cm
textheight = 19.3 cm
oddsidemargin  = 63 pt  (~2.22 cm)
evensidemargin = 63 pt
headsep        = 16 pt
```

---

## [MINIMAL WORKING TEMPLATE]

```latex
\documentclass[runningheads]{llncs}
\usepackage[T1]{fontenc}
\usepackage{graphicx}

\begin{document}

\title{Paper Title}
\titlerunning{Short Title}

\author{Author One\inst{1}\orcidID{0000-0000-0000-0000} \and
        Author Two\inst{2}}
\authorrunning{A. One et al.}

\institute{
  University A, City, Country \email{author1@uni.edu} \and
  University B, City, Country \email{author2@uni.edu}
}

\maketitle

\begin{abstract}
Abstract text 150--250 words.
\keywords{Keyword1 \and Keyword2 \and Keyword3.}
\end{abstract}

\section{Introduction}
First paragraph not indented.

Subsequent paragraphs indented.

\subsection{Related Work}
Content here.

\begin{figure}
\centering
\includegraphics[width=0.8\textwidth]{figure.eps}
\caption{Caption below figure.}
\label{fig:example}
\end{figure}

\begin{table}
\caption{Caption above table.}
\label{tab:example}
\begin{tabular}{lll}
\toprule
Col1 & Col2 & Col3 \\
\midrule
A & B & C \\
\bottomrule
\end{tabular}
\end{table}

\begin{equation}
E = mc^2
\label{eq:example}
\end{equation}

\begin{credits}
\subsubsection{\ackname}
Acknowledgments text.

\subsubsection{\discintname}
The authors have no competing interests.
\end{credits}

\bibliographystyle{splncs04}
\bibliography{references}

\end{document}
```
