"""Build the document corpus for retrieval-augmented answers (D30).

Corpus: official documents whose licence allows reuse with attribution, plus the project's own logs.
- Bank of Canada (R1-R4): "freely use, copy, distribute and transmit" with attribution (bankofcanada.ca/terms).
- Canada Gazette (R9-R11) and Statistics Canada (S3, S10): Open Government Licence - Canada.
- Project decision logs (EN, FR) and one-page summaries.
Commercial sources (Food Price Report, news articles, law-firm notes) are left out.

    python src/rag/build_corpus.py

Raw files go to data/raw/docs/ (not versioned); the chunks the app needs go to app/data/rag_chunks.csv.
Chunking: paragraphs are packed into passages of about 1,000 characters with an overlap of up to 150
characters, so that a sentence cut at a boundary still appears whole in one passage. The overlap starts at a
sentence start (or, failing that, a word start), so no passage begins in the middle of a word (A29).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "docs"
OUT = ROOT / "app" / "data" / "rag_chunks.csv"
CHUNK, OVERLAP = 1000, 150
UA = {"User-Agent": "Mozilla/5.0 (research project; public data)"}

DOCS = [
    ("R1", "Bank of Canada (2026). How Canada's counter-tariffs impacted consumer prices (Sparks at Bank 2026-13)",
     "https://www.bankofcanada.ca/2026/05/sparks-at-bank-article-2026-13/", "html", "Bank of Canada terms: reuse with attribution"),
    ("R2", "Bank of Canada (2026). The price impact of Canadian retaliatory tariffs (Staff Working Paper 2026-22)",
     "https://www.bankofcanada.ca/wp-content/uploads/2026/06/swp2026-22.pdf", "pdf", "Bank of Canada terms: reuse with attribution"),
    ("R3", "Bank of Canada (2025). Assessing tariff pass-through to consumer prices in Canada: Lessons from 2018 (SAN 2025-18)",
     "https://www.bankofcanada.ca/2025/06/staff-analytical-note-2025-18/", "html", "Bank of Canada terms: reuse with attribution"),
    ("R4", "Bank of Canada (2026). The production network amplification of retaliatory tariffs (Staff Working Paper 2026-35)",
     "https://www.bankofcanada.ca/wp-content/uploads/2026/10/swp2026-35.pdf", "pdf", "Bank of Canada terms: reuse with attribution"),
    ("R9", "Canada Gazette (2019). Order Repealing the United States Surtax Order (Other Goods), SOR/2019-144",
     "https://canadagazette.gc.ca/rp-pr/p2/2019/2019-05-29/html/sor-dors144-eng.html", "html", "Open Government Licence - Canada"),
    ("R10", "Canada Gazette (2018). United States Surtax Order (Other Goods), SOR/2018-153",
     "https://canadagazette.gc.ca/rp-pr/p2/2018/2018-07-11/html/sor-dors153-eng.html", "html", "Open Government Licence - Canada"),
    ("R11", "Canada Gazette (2019). Order Amending the United States Surtax Order (Other Goods), SOR/2019-111",
     "https://canadagazette.gc.ca/rp-pr/p2/2019/2019-05-15/html/sor-dors111-eng.html", "html", "Open Government Licence - Canada"),
    ("S3", "Statistics Canada (2024). Monthly average retail prices for selected products, January 2024",
     "https://www.statcan.gc.ca/o1/en/app/5754-monthly-average-retail-prices-selected-products-january-2024", "html", "Open Government Licence - Canada"),
    ("S10", "Statistics Canada (2014). The Canadian Consumer Price Index Reference Paper (62-553-X2014001)",
     "https://www150.statcan.gc.ca/n1/pub/62-553-x/62-553-x2014001-eng.pdf", "pdf", "Open Government Licence - Canada"),
]
LOCAL = [
    ("LOG-EN", "Project decision log (English)", "docs/en/decision-log.md"),
    ("LOG-FR", "Journal des décisions du projet (français)", "docs/fr/journal-decisions.md"),
    ("SUM-EN", "Project results in one page (English)", "docs/en/summary.md"),
    ("SUM-FR", "Résultats du projet en une page (français)", "docs/fr/resume.md"),
]


def fetch(doc_id: str, url: str, kind: str) -> Path:
    path = RAW / f"{doc_id}.{kind}"
    if not path.exists():
        r = requests.get(url, headers=UA, timeout=120)
        r.raise_for_status()
        path.write_bytes(r.content)
    return path


def text_of(path: Path, kind: str) -> str:
    if kind == "pdf":
        import pymupdf
        doc = pymupdf.open(path)
        return "\n\n".join(p.get_text() for p in doc)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body
    return "\n\n".join(p.get_text(" ", strip=True) for p in main.find_all(["p", "li", "h1", "h2", "h3", "h4", "td"]))


SENTENCE_START = re.compile(r"(?<=[.!?;:])\s+(?=[\"'«(\[]?[A-Z0-9À-Ý])")


def tail(text: str, n: int = OVERLAP) -> str:
    """Last n characters of text, moved forward to the first sentence start inside them (else to a word start)."""
    if len(text) <= n:
        return text
    t = text[-n:]
    m = SENTENCE_START.search(t)
    if m:
        return t[m.end():]
    space = t.find(" ")
    return t[space + 1:] if space >= 0 else ""


def chunks(text: str) -> list[str]:
    """Pack paragraphs into ~CHUNK-character passages with OVERLAP characters carried over."""
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paras = [p for p in paras if len(p) > 40]
    out, cur = [], ""
    for p in paras:
        while len(p) > CHUNK:  # very long paragraph: cut at a sentence end when possible
            cut = p.rfind(". ", 0, CHUNK) + 1 or p.rfind(" ", 0, CHUNK) + 1 or CHUNK
            out.append((cur + " " + p[:cut]).strip()); cur = tail(p[:cut]); p = p[cut:].strip()
        if len(cur) + len(p) + 1 > CHUNK and cur:
            out.append(cur.strip()); cur = tail(cur)
        cur = f"{cur} {p}".strip()
    if cur:
        out.append(cur)
    return out


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    rows = []
    for doc_id, title, url, kind, licence in DOCS:
        txt = text_of(fetch(doc_id, url, kind), kind)
        for i, c in enumerate(chunks(txt)):
            rows.append({"chunk_id": f"{doc_id}-{i:03d}", "doc_id": doc_id, "title": title, "url": url, "licence": licence, "text": c})
        print(f"{doc_id}: {len(txt):,} characters")
    for doc_id, title, rel in LOCAL:
        txt = (ROOT / rel).read_text(encoding="utf-8")
        txt = re.sub(r"(?m)^#{1,4} ", "\n\n", txt)
        for i, c in enumerate(chunks(txt)):
            rows.append({"chunk_id": f"{doc_id}-{i:03d}", "doc_id": doc_id, "title": title,
                         "url": f"https://github.com/david-doe/canada-grocery-prices/blob/main/{rel}", "licence": "Project document", "text": c})
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"{len(df)} passages from {df.doc_id.nunique()} documents -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
