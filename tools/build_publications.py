#!/usr/bin/env python3
"""
Regenerate the publications block in academic.html.

One unified list per type, each entry tagged by provenance:
  - "HAL/ORCID"     : pulled automatically. Sources, in order of preference:
                        1. HAL   (IdHAL below) - gives ready-made full citations.
                        2. ORCID (linked iD)   - any DOI'd work not already in HAL.
                        3. Crossref            - for DOIs in tools/manual_publications.json
                                                 ("extra_dois") not in HAL/ORCID (e.g. a
                                                 paper published but not yet deposited).
  - "Manually added": hand-kept items from tools/manual_publications.json (talks,
                        posters, reports, in-prep, software... things not indexed).

No third-party dependencies (urllib/json/re only). Build-time only: produces static
HTML committed to the repo; the visitor downloads nothing extra. When a "Manually
added" item later appears in HAL/ORCID, delete it from manual_publications.json and it
reappears automatically tagged "HAL/ORCID".

Usage:  python3 tools/build_publications.py            # writes academic.html
        python3 tools/build_publications.py --check    # exit 1 if it WOULD change
"""

from __future__ import annotations
import json, re, sys, urllib.parse, urllib.request
from pathlib import Path
from html import escape

# --- Configuration ---------------------------------------------------------
IDHAL = "paul-robineau"
FULLNAME = "Paul Robineau"
ORCID = "0000-0002-2198-3689"
SUPPRESS_DOIS: set[str] = set()
HERE = Path(__file__).resolve().parent
PAGE = HERE.parent / "academic.html"
FEATURED_CFG = HERE / "featured.json"
MANUAL_CFG = HERE / "manual_publications.json"
START = "<!-- AUTO-PUBLICATIONS:START -->"
END = "<!-- AUTO-PUBLICATIONS:END -->"
UA = "paul-robineau.github.io publications builder (mailto:paul.robineau@proton.me)"
TIMEOUT = 30

TAG_AUTO = '<span class="tag tag--src">HAL/ORCID</span>'
TAG_MANUAL = '<span class="tag tag--manual">Manually added</span>'

# Sections in page order: (key, heading, split_by_audience)
SECTIONS = [
    ("journal",         "Peer-reviewed journal articles",        False),
    ("to-be-published", "To be published one day, maybe",        False),
    ("preprint",        "Preprints",                             False),
    ("report",          "Reports",                               False),
    ("invited",         "Invited communications",                False),
    ("oral",            "Oral communications at conferences",    True),
    ("poster",          "Poster communications at conferences",  True),
    ("seminar",         "Seminars & lectures",                   False),
    ("mediation",       "Science mediation",                     False),
    ("software",        "Software & datasets",                   False),
]
AUDIENCE_ORDER = [("international", "International"), ("national", "National")]

HAL_FIELDS = ",".join([
    "docid", "docType_s", "citationFull_s", "title_s", "doiId_s",
    "publicationDateY_i", "invitedCommunication_s", "audience_s",
])


def _get_json(url: str, headers: dict | None = None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)


def clean_citation(raw: str) -> str:
    if not raw:
        return ""
    return raw.replace('target="_blank"', 'target="_blank" rel="noopener noreferrer"').strip()


# --- Source 1: HAL ---------------------------------------------------------
def hal_section(d: dict) -> str | None:
    t = d.get("docType_s")
    if t == "ART":
        return "journal"
    if t in ("PREPRINT", "UNDEFINED") and d.get("doiId_s"):
        return "preprint"
    if t == "COMM":
        return "invited" if d.get("invitedCommunication_s") == "1" else "oral"
    if t == "POSTER":
        return "poster"
    if t == "LECTURE":
        return "seminar"
    return None  # THESE and anything else are not listed here


def fetch_hal() -> list[dict]:
    q = urllib.parse.urlencode({
        "q": f'authIdHal_s:{IDHAL} OR authFullName_s:"{FULLNAME}"',
        "fl": HAL_FIELDS, "rows": "500",
        "sort": "publicationDateY_i desc", "wt": "json",
    })
    docs = _get_json(f"https://api.archives-ouvertes.fr/search/?{q}")["response"]["docs"]
    recs = []
    for d in docs:
        if (d.get("doiId_s") or "") in SUPPRESS_DOIS:
            continue
        sec = hal_section(d)
        if not sec:
            continue
        aud = {"2": "international", "1": "national"}.get(d.get("audience_s") or "")
        recs.append({
            "section": sec, "year": d.get("publicationDateY_i"),
            "audience": aud, "citation": clean_citation(d.get("citationFull_s", "")),
            "source": "auto", "doi": (d.get("doiId_s") or "").lower() or None,
        })
    return recs


# --- Crossref (citation by DOI, formatted to match the HAL style) ----------
CROSSREF_SECTION = {
    "journal-article": "journal", "posted-content": "preprint",
    "proceedings-article": "oral", "paper-conference": "oral",
    "dataset": "software", "report": "report",
}


def crossref_record(doi: str) -> dict | None:
    try:
        m = _get_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}",
                      {"User-Agent": UA})["message"]
    except Exception as e:
        sys.stderr.write(f"warning: Crossref lookup failed for {doi}: {e}\n")
        return None
    section = CROSSREF_SECTION.get(m.get("type"))
    if not section:   # e.g. dissertation/thesis – not listed among publications
        return None
    authors = []
    for a in m.get("author", []):
        given, family = a.get("given", ""), a.get("family", "")
        authors.append(f"{given} {family}".strip() if given else family)
    title = (m.get("title") or [""])[0].strip().rstrip(".")
    journal = (m.get("container-title") or [""])[0]
    year = ((m.get("issued", {}).get("date-parts") or [[None]])[0] or [None])[0]
    vol, issue = m.get("volume"), m.get("issue")
    page = m.get("page") or m.get("article-number")
    bits = []
    if journal:
        bits.append(f"<i>{escape(journal)}</i>")
    if year:
        bits.append(str(year))
    if vol:
        bits.append(escape(str(vol)) + (f" ({escape(str(issue))})" if issue else ""))
    if page:
        bits.append(f"pp.{escape(str(page))}")
    link = (f'<a target="_blank" rel="noopener noreferrer" '
            f'href="https://doi.org/{escape(doi)}">⟨{escape(doi)}⟩</a>')
    citation = f"{escape(', '.join(authors))}. {escape(title)}. {', '.join(bits)}. {link}."
    return {
        "section": section, "year": year, "audience": None, "citation": citation,
        "source": "auto", "doi": doi.lower(),
    }


# --- Source 2: ORCID (DOI'd works not already in HAL) ----------------------
def fetch_orcid_dois(known: set[str]) -> list[str]:
    try:
        d = _get_json(f"https://pub.orcid.org/v3.0/{ORCID}/works",
                      {"Accept": "application/json", "User-Agent": UA})
    except Exception as e:
        sys.stderr.write(f"warning: ORCID fetch failed: {e}\n")
        return []
    out = []
    for g in d.get("group", []):
        s = g["work-summary"][0]
        doi = next((e["external-id-value"].lower()
                    for e in (s.get("external-ids", {}) or {}).get("external-id", [])
                    if e.get("external-id-type") == "doi"), None)
        if doi and doi not in known and doi not in out:
            out.append(doi)
    return out


# --- Rendering -------------------------------------------------------------
def _li(rec: dict) -> str:
    tag = TAG_AUTO if rec["source"] == "auto" else TAG_MANUAL
    return f'          <li>{rec["citation"]} {tag}</li>'


def _sort(recs: list[dict]) -> list[dict]:
    # newest first; undated/forthcoming (year None) float to the top, order kept stable
    return sorted(recs, key=lambda r: (r.get("year") is not None, r.get("year") or 0),
                  reverse=True)


def render_section(recs: list[dict], split: bool) -> str:
    if not split:
        items = "\n".join(_li(r) for r in _sort(recs))
        return f'        <ol class="pub-list">\n{items}\n        </ol>'
    out = []
    for key, label in AUDIENCE_ORDER:
        group = [r for r in recs if (r.get("audience") or "international") == key]
        if not group:
            continue
        items = "\n".join(_li(r) for r in _sort(group))
        out.append(f'        <p class="pub-sub">{label}</p>')
        out.append(f'        <ol class="pub-list">\n{items}\n        </ol>')
    return "\n".join(out)


def render_featured(by_doi: dict[str, str]) -> str:
    if not FEATURED_CFG.exists():
        return ""
    cfg = json.loads(FEATURED_CFG.read_text(encoding="utf-8"))
    cards = []
    for entry in cfg.get("featured", []):
        doi = (entry.get("doi") or "").lower()
        citation = by_doi.get(doi) or clean_citation(entry.get("citation", ""))
        if not citation:
            sys.stderr.write(f"warning: featured entry without citation: {doi}\n")
            continue
        img, alt = entry.get("image"), escape(entry.get("alt", "Graphical abstract"))
        media = (f'        <div class="feat__media"><img src="{escape(img)}" '
                 f'loading="lazy" alt="{alt}" /></div>\n') if img else ""
        cards.append('      <article class="feat">\n' + media +
                     f'        <div class="feat__body"><p>{citation}</p></div>\n'
                     '      </article>')
    if not cards:
        return ""
    return ('      <h2>Featured publications</h2>\n      <div class="feat-grid">\n'
            + "\n".join(cards) + "\n      </div>\n")


def build_block(records: list[dict]) -> str:
    by_doi = {r["doi"]: r["citation"] for r in records if r.get("doi")}
    parts = [
        render_featured(by_doi),
        '      <h2 id="publications">Publications</h2>',
        '      <p class="section-intro">Automatically gathered from '
        f'<a href="https://hal.science/search/index/?q=*&authIdHal_s={IDHAL}" '
        'target="_blank" rel="noopener noreferrer">HAL</a> and '
        f'<a href="https://orcid.org/{ORCID}" target="_blank" rel="noopener noreferrer">ORCID</a>'
        ' (tagged <span class="tag tag--src">HAL/ORCID</span>); other items are '
        '<span class="tag tag--manual">Manually added</span>.</p>',
    ]
    for key, heading, split in SECTIONS:
        recs = [r for r in records if r["section"] == key]
        if not recs:
            continue
        parts.append('      <div class="pub-group">')
        parts.append(f'        <h3>{escape(heading)}</h3>')
        parts.append(render_section(recs, split))
        parts.append('      </div>')
    return "\n".join(p for p in parts if p)


def gather() -> list[dict]:
    records = fetch_hal()
    known = {r["doi"] for r in records if r.get("doi")}

    manual_cfg = json.loads(MANUAL_CFG.read_text(encoding="utf-8")) if MANUAL_CFG.exists() else {}

    # ORCID DOIs not in HAL, then extra DOIs not in HAL/ORCID -> Crossref
    extra = list(fetch_orcid_dois(known))
    for doi in manual_cfg.get("extra_dois", []):
        if doi.lower() not in known and doi.lower() not in extra:
            extra.append(doi.lower())
    for doi in extra:
        rec = crossref_record(doi)
        if rec:
            records.append(rec)
            known.add(rec["doi"])

    # Manually added (skip any that became auto via DOI)
    for e in manual_cfg.get("manual", []):
        records.append({
            "section": e["section"], "year": e.get("year"),
            "audience": e.get("audience"), "citation": clean_citation(e["citation"]),
            "source": "manual", "doi": (e.get("doi") or "").lower() or None,
        })
    return records


def main() -> int:
    check = "--check" in sys.argv
    records = gather()
    block = build_block(records)
    html = PAGE.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(html):
        sys.stderr.write(f"error: markers {START} / {END} not found in {PAGE.name}\n")
        return 2
    new = pattern.sub(f"{START}\n{block}\n      {END}", html)
    if new == html:
        print("No change.")
        return 0
    if check:
        print("academic.html would change.")
        return 1
    PAGE.write_text(new, encoding="utf-8")
    n_auto = sum(1 for r in records if r["source"] == "auto")
    n_man = sum(1 for r in records if r["source"] == "manual")
    print(f"Updated {PAGE.name} ({n_auto} HAL/ORCID + {n_man} manual entries).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
