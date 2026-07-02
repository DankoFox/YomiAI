#!/usr/bin/env python3
"""
check_lncs_compliance.py — Static checker for Springer LNCS paper format.

Usage:
    python scripts/test/check_lncs_compliance.py [<paper_dir>]

Without argument, defaults to thesis/paper/.

Exits with 0 if all checks pass, 1 if any FAIL, 2 on internal error.
Output: [PASS] [WARN] [FAIL] [SKIP] per check.
"""
import os
import re
import sys
import subprocess
from pathlib import Path

# ── ANSI colors ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}PASS{RESET}"
WARN = f"{YELLOW}WARN{RESET}"
FAIL = f"{RED}FAIL{RESET}"
SKIP = f"{CYAN}SKIP{RESET}"

n_pass = 0
n_fail = 0
n_warn = 0
n_skip = 0


def ok(msg: str):
    global n_pass
    n_pass += 1
    print(f"  [{PASS}] {msg}")


def warn(msg: str):
    global n_warn
    n_warn += 1
    print(f"  [{WARN}] {msg}")


def fail(msg: str):
    global n_fail
    n_fail += 1
    print(f"  [{FAIL}] {msg}")


def skip(msg: str):
    global n_skip
    n_skip += 1
    print(f"  [{SKIP}] {msg}")


# ── Helpers ──────────────────────────────────────────────────────────────────

def read_all_tex(paper_dir: Path) -> dict[str, str]:
    """Read all .tex files in paper_dir (recursive). Returns {rel_path: content}."""
    files = {}
    for fpath in sorted(paper_dir.rglob("*.tex")):
        rel = fpath.relative_to(paper_dir)
        files[str(rel)] = fpath.read_text(encoding="utf-8", errors="replace")
    return files


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_main_tex(paper_dir: Path) -> Path | None:
    """Find the main .tex file (contains \\documentclass or \\begin{document})."""
    for fpath in paper_dir.rglob("*.tex"):
        content = fpath.read_text(encoding="utf-8", errors="replace")
        if re.search(r"\\documentclass", content):
            return fpath
    return None


def grep(content: str, pattern: str, flags=0) -> list[str]:
    """Return all matching lines."""
    return re.findall(r"^.*" + pattern + r".*$", content, flags=re.MULTILINE | flags)


def count_words(text: str) -> int:
    """Rough word count (splits on whitespace)."""
    return len(text.split())


# ── Checks ───────────────────────────────────────────────────────────────────

def check_documentclass(files: dict[str, str], paper_dir: Path):
    main = find_main_tex(paper_dir)
    if main is None:
        fail("No \\documentclass found in any .tex file")
        return
    content = main.read_text(encoding="utf-8")
    m = re.search(r"\\documentclass(?:\[([^\]]*)\])?\{([^}]*)\}", content)
    if not m:
        fail("No \\documentclass found")
        return
    opts, cls = m.group(1) or "", m.group(2)
    if cls != "llncs":
        fail(f"Document class is '{cls}', expected 'llncs'")
        return
    if "runningheads" not in opts:
        fail("llncs class missing 'runningheads' option: \\documentclass[runningheads]{llncs}")
        return
    ok(f"\\documentclass[runningheads]{{llncs}} in {main.name}")


def check_required_packages(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    needed = {
        "T1 fontenc":  r"\\usepackage(?:\[T1\])?\{fontenc\}",
        "graphicx":    r"\\usepackage\{graphicx\}",
        "amsmath":     r"\\usepackage\{amsmath\}",
    }
    for name, pattern in needed.items():
        if re.search(pattern, all_text):
            ok(f"Package '{name}' loaded")
        else:
            fail(f"Package '{name}' not loaded")


def check_maketitle(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    if re.search(r"\\maketitle", all_text):
        ok("\\maketitle present")
    else:
        fail("\\maketitle missing")


def check_abstract(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    if not re.search(r"\\begin\{abstract\}", all_text):
        fail("\\begin{abstract} missing")
        return
    if not re.search(r"\\end\{abstract\}", all_text):
        fail("\\end{abstract} missing")
        return
    # Extract abstract body
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", all_text, re.DOTALL)
    if m:
        # Remove \keywords{} from abstract body for word count
        body = re.sub(r"\\keywords\{.*?\}", "", m.group(1), flags=re.DOTALL)
        wc = count_words(body)
        if wc < 100:
            warn(f"Abstract too short ({wc} words, recommended 150-250)")
        elif wc > 350:
            warn(f"Abstract too long ({wc} words, recommended 150-250)")
        else:
            ok(f"Abstract length ~{wc} words (recommended 150-250)")
    else:
        fail("Could not extract abstract body")


def check_keywords(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    if re.search(r"\\keywords\{", all_text):
        ok("\\keywords{} present")
    else:
        fail("\\keywords{} missing")


def check_ack_disclosure(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    has_ack = bool(re.search(r"\\ackname|acknowledgment|Acknowledgments?|Acknowledgment", all_text, re.IGNORECASE))
    has_disc = bool(re.search(
        r"\\discintname|disclosure|competing\s+interests|no\s+competing",
        all_text, re.IGNORECASE
    ))
    if has_ack:
        ok("Acknowledgments section present")
    else:
        fail("Acknowledgments section missing (use \\ackname or equivalent)")
    if has_disc:
        ok("Disclosure of Interests present")
    else:
        fail("Disclosure of Interests missing (use \\discintname or equivalent)")


def check_bibliography(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    m = re.search(r"\\bibliographystyle\{([^}]*)\}", all_text)
    if m:
        style = m.group(1)
        if style == "splncs04":
            ok(f"BibTeX style: {style}")
        else:
            warn(f"BibTeX style is '{style}', expected 'splncs04' for LNCS")
    else:
        fail("\\bibliographystyle not found")
    if re.search(r"\\bibliography\{", all_text):
        ok("\\bibliography{} present")
    else:
        # Check for inline thebibliography
        if re.search(r"\\begin\{thebibliography\}", all_text):
            ok("Inline thebibliography present (consider using .bib + splncs04)")
        else:
            fail("No bibliography found (\\bibliography{} or thebibliography)")


def check_titlerunning(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    # Count non-commented occurrences
    matches = re.findall(r"\\titlerunning\{", all_text)
    commented = len(re.findall(r"^[^%\n]*%\s*\\titlerunning\{", all_text, re.MULTILINE))
    active = len(matches) - commented
    if active >= 1:
        ok("\\titlerunning{} present")
    else:
        fail("\\titlerunning{} missing or commented out")


def check_authorrunning(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    if re.search(r"\\authorrunning\{", all_text):
        ok("\\authorrunning{} present")
    else:
        fail("\\authorrunning{} missing")


def check_institute(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    if re.search(r"\\institute\{", all_text):
        ok("\\institute{} present")
    else:
        fail("\\institute{} missing")


def check_no_forbidden_patterns(files: dict[str, str], paper_dir: Path):
    all_text = "\n".join(files.values())
    # Remove commented lines so we don't flag commented-out code
    clean = "\n".join(
        line for line in all_text.split("\n")
        if not line.strip().startswith("%")
    )

    # Forbidden: \pagestyle (LNCS handles this)
    if re.search(r"\\pagestyle\{", clean):
        fail("\\pagestyle{} found — LNCS handles page style. Remove it.")
    else:
        ok("No forbidden \\pagestyle")

    # Forbidden: \thispagestyle (except empty)
    matches = re.findall(r"\\thispagestyle\{([^}]*)\}", clean)
    bad = [m for m in matches if m.lower() != "empty"]
    if bad:
        fail(f"\\thispagestyle{{{', '.join(bad)}}} found — LNCS handles page style. Remove or use 'empty'.")
    else:
        ok("No forbidden \\thispagestyle")

    # Forbidden: section-based theorem numbering (e.g., \theorem{1.1})
    if re.search(r"\\theorem\{?\d+\.\d+\}?", clean) or re.search(r"\\lemma\{?\d+\.\d+\}?", clean):
        fail("Section-based theorem/lemma numbering detected — use consecutive numbering")
    else:
        ok("No section-based theorem numbering")

    # Forbidden: section-based equation numbering patterns in source
    if re.search(r"\\tag\{\d+\.\d+\}", clean):
        warn("\\tag{} with section-based equation numbering (e.g., \\tag{1.1})")
    else:
        ok("No section-based equation numbering")

    # Forbidden: mainmatter (LNCS doesn't use it)
    if re.search(r"\\mainmatter", clean):
        warn("\\mainmatter present — LNCS does not use \\mainmatter. Consider removing.")
    else:
        ok("No \\mainmatter" if not re.search(r"\\mainmatter", clean) else None)


def check_llncs_cls_exists(paper_dir: Path):
    """Check that llncs.cls is accessible (in paper dir, parent, or system)."""
    search_dirs = [paper_dir, paper_dir.parent, paper_dir.parent.parent]
    for d in search_dirs:
        if (d / "llncs.cls").exists():
            ok(f"llncs.cls found in {d.name}/")
            return
    # Also check if the template copy is accessible
    if Path("/tmp/lncs_template/llncs.cls").exists():
        ok("llncs.cls found in /tmp/lncs_template/ (copy to paper dir for compilation)")
        return
    fail("llncs.cls not found in paper directory or parent — copy from template")


def check_figure_formats(files: dict[str, str], paper_dir: Path):
    """Check that included figures exist and are vector formats."""
    all_text = "\n".join(files.values())
    includes = re.findall(r"\\(?:includegraphics|input)\{([^}]*)\}", all_text)
    raster_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    for path in includes:
        # Skip non-figure inputs
        if not any(c in path for c in ["fig", "img", "figure", "chart", "plot", "diagram"]):
            # Check if the file extension suggests a figure
            ext = Path(path).suffix.lower()
            if ext == "" or ext in {".tex", ".cls", ".sty", ".bst"}:
                continue
            if ext in raster_exts:
                warn(f"Figure '{path}' uses raster format {ext} — prefer EPS/PDF")
            elif ext and ext not in {".eps", ".pdf"}:
                warn(f"Unknown figure format for '{path}' — use EPS or PDF")
    ok("Figure format check complete (review WARNs above)")


def check_doi_in_references(paper_dir: Path):
    """Check .bib file for DOI entries."""
    bib_files = list(paper_dir.rglob("*.bib"))
    if not bib_files:
        skip("No .bib file found to check DOIs")
        return
    all_bib = ""
    for bf in bib_files:
        all_bib += bf.read_text(encoding="utf-8", errors="replace")
    doi_count = len(re.findall(r"\bdoi\s*=|doi\s*\{|DOI\s*=", all_bib))
    total_refs = all_bib.count("@") - all_bib.count("@comment") - all_bib.count("@Comment")
    if total_refs <= 0:
        skip("No references in .bib to check")
        return
    pct = (doi_count / total_refs) * 100
    if pct >= 50:
        ok(f"DOIs in {doi_count}/{total_refs} references ({pct:.0f}%)")
    elif doi_count > 0:
        warn(f"DOIs in only {doi_count}/{total_refs} references ({pct:.0f}%) — add more DOIs")
    else:
        warn(f"No DOIs found in any of {total_refs} references — strongly recommended")


def check_no_svproc_artifacts(files: dict[str, str], paper_dir: Path):
    """Check that no LNNS (svproc) artifacts remain."""
    all_text = "\n".join(files.values())
    if re.search(r"svproc", all_text):
        fail("svproc references found — LNCS uses llncs.cls, not svproc")
        return
    if re.search(r"splncs03", all_text):
        fail("splncs03_unsrt.bst references found — LNCS uses splncs04.bst")
        return
    if re.search(r"\\tocauthor", all_text):
        fail("\\tocauthor{} found — LNCS does not use this command")
        return
    ok("No svproc/LNNS artifacts remaining")


def check_mainmatter_not_used(paper_dir: Path):
    # Handled in check_no_forbidden_patterns already but we have it here
    # as part of svproc cleanup
    pass


def try_compile_paper(paper_dir: Path):
    """Optionally compile with latexmk to check for errors."""
    latexmk = subprocess.run(["which", "latexmk"], capture_output=True, text=True).stdout.strip()
    if not latexmk:
        skip("latexmk not found — skipping compilation check")
        return

    main = find_main_tex(paper_dir)
    if main is None:
        skip("No main .tex found — skipping compilation check")
        return

    # Copy llncs.cls and splncs04.bst if needed
    for needed in ["llncs.cls", "splncs04.bst"]:
        src = Path(f"/tmp/lncs_template/{needed}")
        dst = paper_dir / needed
        if src.exists() and not dst.exists():
            import shutil
            shutil.copy2(src, dst)
            print(f"    (Copied {needed} to paper directory)")

    print(f"    Running latexmk on {main.name}...")
    result = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
         str(main.absolute())],
        capture_output=True, text=True, timeout=300,
        cwd=paper_dir,
    )
    if result.returncode == 0:
        ok("Paper compiles successfully")

        # Check page count
        pdf_path = main.with_suffix(".pdf")
        if pdf_path.exists():
            try:
                import fitz
                doc = fitz.open(str(pdf_path))
                pages = len(doc)
                doc.close()
                if pages <= 14:
                    ok(f"Page count: {pages} (≤14)")
                else:
                    fail(f"Page count: {pages} — exceeds 14-page limit!")
            except ImportError:
                # Use pdfinfo
                pinfo = subprocess.run(
                    ["pdfinfo", str(pdf_path)],
                    capture_output=True, text=True, timeout=30
                )
                m = re.search(r"Pages:\s*(\d+)", pinfo.stdout)
                if m:
                    pages = int(m.group(1))
                    if pages <= 14:
                        ok(f"Page count: {pages} (≤14)")
                    else:
                        fail(f"Page count: {pages} — exceeds 14-page limit!")
                else:
                    skip("Could not determine page count")
    else:
        # Show first few errors
        errors = re.findall(r"^! .*$", result.stdout, re.MULTILINE)[:5]
        for err in errors:
            print(f"    {RED}LaTeX error: {err.strip()}{RESET}")
        fail("Paper compilation failed — check LaTeX errors above")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    paper_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("thesis/paper")
    if not paper_dir.exists():
        print(f"{RED}Error{RESET}: {paper_dir} not found")
        sys.exit(2)
    paper_dir = paper_dir.resolve()
    print(f"\n{BOLD}LNCS Compliance Checker{RESET}")
    print(f"Paper directory: {paper_dir}\n")
    print(f"{'─' * 60}")

    files = read_all_tex(paper_dir)

    # Structural checks
    print(f"\n{BOLD}[Structure]{RESET}")
    check_documentclass(files, paper_dir)
    check_required_packages(files, paper_dir)
    check_maketitle(files, paper_dir)
    check_abstract(files, paper_dir)
    check_keywords(files, paper_dir)
    check_titlerunning(files, paper_dir)
    check_authorrunning(files, paper_dir)
    check_institute(files, paper_dir)

    # Content checks
    print(f"\n{BOLD}[Content]{RESET}")
    check_ack_disclosure(files, paper_dir)
    check_bibliography(files, paper_dir)

    # Prohibited patterns
    print(f"\n{BOLD}[Prohibited Patterns]{RESET}")
    check_no_forbidden_patterns(files, paper_dir)

    # Migration checks
    print(f"\n{BOLD}[Migration (svproc → llncs)]{RESET}")
    check_no_svproc_artifacts(files, paper_dir)

    # Asset checks
    print(f"\n{BOLD}[Assets]{RESET}")
    check_llncs_cls_exists(paper_dir)
    check_figure_formats(files, paper_dir)
    check_doi_in_references(paper_dir)

    # Compilation (optional)
    print(f"\n{BOLD}[Compilation]{RESET}")
    try_compile_paper(paper_dir)

    # Summary
    print(f"\n{'─' * 60}")
    total = n_pass + n_fail + n_warn + n_skip
    print(f"{BOLD}Summary:{RESET}  {GREEN}{n_pass} passed{RESET}  "
          f"{RED}{n_fail} failed{RESET}  {YELLOW}{n_warn} warnings{RESET}  "
          f"{CYAN}{n_skip} skipped{RESET}  ({total} total)")

    if n_fail > 0:
        print(f"\n{RED}❌ {n_fail} failing check(s) — fix before submission{RESET}")
    else:
        print(f"\n{GREEN}✅ All mandatory checks pass{RESET}")

    sys.exit(1 if n_fail > 0 else 0)


if __name__ == "__main__":
    main()
