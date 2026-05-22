"""
scripts/benchmark/multilingual_search.py
=========================================
Multilingual retrieval benchmark for BGE-M3 + NLLB translation pipeline.

Sends queries in multiple languages to the running FastAPI server and
measures Precision@10 (genre hit rate) per language group.

Usage:
    python scripts/benchmark/multilingual_search.py
    python scripts/benchmark/multilingual_search.py --host localhost --port 8000
    python scripts/benchmark/multilingual_search.py --top-k 10 --langs fr de zh ja ko

Output:
    - Per-language Precision@10 table printed to stdout
    - Results saved to evaluation/multilingual_<date>.json
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Query suite ───────────────────────────────────────────────────────────────
# Each entry: (query_text, expected_genre_keywords, language_code, group_label)
# genre keywords are matched against the genre field of returned items.
# Translations were produced with NLLB-supported source languages.

QUERY_SUITE = [
    # ── English baseline (same groups as compare_encoders.py) ────────────────
    ("mystery detective crime",
     ["mystery", "detective", "crime", "thriller"], "en", "short"),
    ("fantasy magic wizard",
     ["fantasy", "magic", "wizard"], "en", "short"),
    ("self help success habits",
     ["self-help", "self help", "success", "habits"], "en", "short"),
    ("science fiction space",
     ["science fiction", "sci-fi", "space"], "en", "short"),

    ("detective mystery crime thriller investigation",
     ["mystery", "detective", "crime", "thriller"], "en", "medium"),
    ("fantasy magic sword quest adventure",
     ["fantasy", "magic", "adventure"], "en", "medium"),
    ("self improvement habits success personal growth",
     ["self-help", "self help", "success"], "en", "medium"),
    ("science fiction space travel alien civilization",
     ["science fiction", "sci-fi", "space"], "en", "medium"),

    # ── Vietnamese (previously benchmarked) ──────────────────────────────────
    ("tiểu thuyết trinh thám",
     ["mystery", "detective", "crime", "thriller"], "vi", "short"),
    ("phép thuật kỳ ảo",
     ["fantasy", "magic"], "vi", "short"),
    ("sách phát triển bản thân",
     ["self-help", "self help", "success"], "vi", "short"),
    ("khoa học viễn tưởng",
     ["science fiction", "sci-fi"], "vi", "short"),
    (
        "Câu chuyện trinh thám hấp dẫn về thám tử tài ba điều tra vụ án giết người bí ẩn"
        " trong thành phố đầy tham nhũng và phản bội",
        ["mystery", "detective", "crime", "thriller"], "vi", "long",
    ),
    (
        "Cuốn sách hướng dẫn xây dựng thói quen tốt và phát triển bản thân",
        ["self-help", "self help", "success", "habits"], "vi", "long",
    ),

    # ── French ───────────────────────────────────────────────────────────────
    ("mystère détective crime",
     ["mystery", "detective", "crime", "thriller"], "fr", "short"),
    ("fantasy magie sorcier",
     ["fantasy", "magic", "wizard"], "fr", "short"),
    ("développement personnel succès habitudes",
     ["self-help", "self help", "success", "habits"], "fr", "short"),
    ("science-fiction espace voyage",
     ["science fiction", "sci-fi", "space"], "fr", "short"),
    (
        "Un brillant détective enquête sur une série de meurtres mystérieux dans une ville"
        " sombre pleine de corruption et de trahison",
        ["mystery", "detective", "crime", "thriller"], "fr", "long",
    ),
    (
        "Conseils pratiques pour développer de bonnes habitudes et réussir sa vie"
        " personnelle et professionnelle grâce à la discipline",
        ["self-help", "self help", "success"], "fr", "long",
    ),

    # ── German ───────────────────────────────────────────────────────────────
    ("Detektiv Krimi Mord Thriller",
     ["mystery", "detective", "crime", "thriller"], "de", "short"),
    ("Fantasy Magie Zauberer Abenteuer",
     ["fantasy", "magic", "wizard"], "de", "short"),
    ("Selbsthilfe Erfolg Gewohnheiten persönliches Wachstum",
     ["self-help", "self help", "success", "habits"], "de", "short"),
    ("Science-Fiction Weltraum Alien Reise",
     ["science fiction", "sci-fi", "space"], "de", "short"),
    (
        "Ein brillanter Detektiv untersucht eine Reihe mysteriöser Morde in einer dunklen"
        " Stadt voller Korruption und Verrat",
        ["mystery", "detective", "crime", "thriller"], "de", "long",
    ),

    # ── Spanish ──────────────────────────────────────────────────────────────
    ("misterio detective crimen thriller",
     ["mystery", "detective", "crime", "thriller"], "es", "short"),
    ("fantasía magia hechicero aventura",
     ["fantasy", "magic", "wizard"], "es", "short"),
    ("superación personal éxito hábitos",
     ["self-help", "self help", "success", "habits"], "es", "short"),
    ("ciencia ficción espacio viaje alienígena",
     ["science fiction", "sci-fi", "space"], "es", "short"),
    (
        "Un brillante detective investiga una serie de misteriosos asesinatos en una ciudad"
        " oscura llena de corrupción y traición",
        ["mystery", "detective", "crime", "thriller"], "es", "long",
    ),

    # ── Chinese (Simplified) ─────────────────────────────────────────────────
    ("侦探悬疑犯罪惊悚",
     ["mystery", "detective", "crime", "thriller"], "zh", "short"),
    ("奇幻魔法巫师冒险",
     ["fantasy", "magic", "wizard"], "zh", "short"),
    ("自我提升成功习惯个人成长",
     ["self-help", "self help", "success", "habits"], "zh", "short"),
    ("科幻小说太空旅行外星文明",
     ["science fiction", "sci-fi", "space"], "zh", "short"),
    (
        "一位才华横溢的侦探在一座充满腐败和背叛的黑暗城市中调查一系列神秘谋杀案",
        ["mystery", "detective", "crime", "thriller"], "zh", "long",
    ),

    # ── Japanese ─────────────────────────────────────────────────────────────
    ("探偵 ミステリー 犯罪 スリラー",
     ["mystery", "detective", "crime", "thriller"], "ja", "short"),
    ("ファンタジー 魔法 魔法使い 冒険",
     ["fantasy", "magic", "wizard"], "ja", "short"),
    ("自己啓発 成功 習慣 個人的成長",
     ["self-help", "self help", "success", "habits"], "ja", "short"),
    ("SF 宇宙旅行 エイリアン 文明",
     ["science fiction", "sci-fi", "space"], "ja", "short"),
    (
        "腐敗と裏切りに満ちた暗い街で連続殺人事件を調査する天才探偵の物語",
        ["mystery", "detective", "crime", "thriller"], "ja", "long",
    ),

    # ── Korean ───────────────────────────────────────────────────────────────
    ("탐정 미스터리 범죄 스릴러",
     ["mystery", "detective", "crime", "thriller"], "ko", "short"),
    ("판타지 마법 마법사 모험",
     ["fantasy", "magic", "wizard"], "ko", "short"),
    ("자기계발 성공 습관 개인 성장",
     ["self-help", "self help", "success", "habits"], "ko", "short"),
    ("공상과학 우주여행 외계인 문명",
     ["science fiction", "sci-fi", "space"], "ko", "short"),
    (
        "부패와 배신으로 가득 찬 어두운 도시에서 연쇄 살인 사건을 수사하는 천재 탐정 이야기",
        ["mystery", "detective", "crime", "thriller"], "ko", "long",
    ),
]

ALL_LANGS = ["en", "vi", "fr", "de", "es", "zh", "ja", "ko"]

LANG_LABELS = {
    "en": "English",
    "vi": "Vietnamese",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
}


# ── HTTP helper ───────────────────────────────────────────────────────────────

def post_search(host: str, port: int, query: str, top_k: int) -> tuple[list, float]:
    url = f"http://{host}:{port}/search"
    body = json.dumps({"query": query, "top_k": top_k}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    wall_ms = (time.perf_counter() - t0) * 1000
    return data.get("results", []), wall_ms


# ── Precision@k ───────────────────────────────────────────────────────────────

def precision_at_k(results: list, genre_keywords: list, k: int) -> float:
    hits = 0
    for item in results[:k]:
        genre = (item.get("genre") or item.get("genres") or "").lower()
        if any(kw.lower() in genre for kw in genre_keywords):
            hits += 1
    return hits / k if k > 0 else 0.0


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Multilingual retrieval benchmark")
    parser.add_argument("--host",   default="localhost")
    parser.add_argument("--port",   type=int, default=8000)
    parser.add_argument("--top-k",  type=int, default=10)
    parser.add_argument("--langs",  nargs="*", default=ALL_LANGS,
                        help="Language codes to test (default: all)")
    args = parser.parse_args()

    # Server health check
    try:
        with urllib.request.urlopen(
            f"http://{args.host}:{args.port}/health", timeout=10
        ) as r:
            health = json.loads(r.read())
        if health.get("status") != "ready":
            print(f"WARNING: server status = {health.get('status')}")
    except Exception as e:
        print(f"ERROR: cannot reach server at {args.host}:{args.port}: {e}")
        sys.exit(1)

    selected = set(args.langs)
    suite = [q for q in QUERY_SUITE if q[2] in selected]

    # Per-lang, per-group accumulator
    scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    timings: dict[str, list[float]] = defaultdict(list)
    failures: list[str] = []

    total = len(suite)
    for i, (query, genre_kws, lang, group) in enumerate(suite, 1):
        label = f"[{LANG_LABELS.get(lang, lang)}/{group}] {query[:60]}"
        print(f"  ({i}/{total}) {label}")
        try:
            results, wall_ms = post_search(args.host, args.port, query, args.top_k)
            p10 = precision_at_k(results, genre_kws, args.top_k)
            scores[lang][group].append(p10)
            timings[lang].append(wall_ms)
            print(f"           P@{args.top_k} = {p10:.4f}  ({wall_ms:.0f} ms)")
        except Exception as e:
            print(f"           ERROR: {e}")
            failures.append(f"{lang}/{group}: {query[:40]}")

    # ── Results table ─────────────────────────────────────────────────────────
    print(f"\n{'='*64}")
    print(f"  MULTILINGUAL RETRIEVAL RESULTS — Precision@{args.top_k}")
    print(f"{'='*64}")
    print(f"  {'Language':<14} {'Short':>8} {'Long':>8} {'Medium':>8} {'Avg':>8}  {'Latency':>10}")
    print(f"  {'-'*60}")

    output_rows = {}
    for lang in args.langs:
        if lang not in scores:
            continue
        lang_scores = scores[lang]
        short_avg  = sum(lang_scores.get("short",  [0])) / max(len(lang_scores.get("short",  [1])), 1)
        medium_avg = sum(lang_scores.get("medium", [0])) / max(len(lang_scores.get("medium", [1])), 1)
        long_avg   = sum(lang_scores.get("long",   [0])) / max(len(lang_scores.get("long",   [1])), 1)
        all_vals   = [v for vs in lang_scores.values() for v in vs]
        overall    = sum(all_vals) / len(all_vals) if all_vals else 0.0
        avg_lat    = sum(timings[lang]) / len(timings[lang]) if timings[lang] else 0.0

        short_str  = f"{short_avg:.4f}"  if lang_scores.get("short")  else "  —   "
        medium_str = f"{medium_avg:.4f}" if lang_scores.get("medium") else "  —   "
        long_str   = f"{long_avg:.4f}"   if lang_scores.get("long")   else "  —   "

        print(f"  {LANG_LABELS.get(lang, lang):<14} {short_str:>8} {long_str:>8} {medium_str:>8} {overall:>8.4f}  {avg_lat:>8.0f} ms")
        output_rows[lang] = {
            "short": round(short_avg, 4),
            "medium": round(medium_avg, 4),
            "long": round(long_avg, 4),
            "overall": round(overall, 4),
            "avg_latency_ms": round(avg_lat, 1),
            "n_queries": len(all_vals),
        }

    print(f"{'='*64}")
    if failures:
        print(f"\n  FAILED ({len(failures)}):")
        for f in failures:
            print(f"    {f}")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    out_dir = ROOT / "evaluation"
    out_dir.mkdir(exist_ok=True)
    run_id  = datetime.now().strftime("%Y-%m-%d_%H-%M")
    out_path = out_dir / f"multilingual_{run_id}.json"
    payload = {
        "run_date": datetime.now().isoformat(),
        "server": f"{args.host}:{args.port}",
        "top_k": args.top_k,
        "languages_tested": args.langs,
        "results": output_rows,
        "failures": failures,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved → {out_path}")


if __name__ == "__main__":
    main()
