#!/usr/bin/env python3
"""Job Autopilot engine: ATS-style match scoring + honest resume tailoring + PDF rendering.

Usage:
  python3 engine.py score  <jd.txt> [--resume tailored.json]
  python3 engine.py tailor <jd.txt> --title "Job Title" --out out_prefix
"""
import json, re, sys, os, argparse, subprocess, copy, tempfile, glob, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
# Your private profile folder (base_resume.json, confirmed_skills.json). Never commit it.
PROFILE_DIR = os.environ.get("JOBPILOT_PROFILE", os.path.join(os.getcwd(), "profile"))
_BASE_PATH = os.path.join(PROFILE_DIR, "base_resume.json")
if not os.path.exists(_BASE_PATH):
    sys.exit(f"No profile found at {_BASE_PATH}. Run: python jobpilot.py init")
BASE = json.load(open(_BASE_PATH, encoding="utf-8"))
CANDIDATE_YEARS = float(BASE.get("years_experience", 2))

# canonical term -> regex alternatives (lowercase). Covers analyst / ops / supply chain / PM JDs.
TAXONOMY = {
    "sql": r"\bsql\b|mysql|postgres|t-sql|pl/sql",
    "excel": r"\bexcel\b|spreadsheet",
    "advanced excel": r"advanced (ms |microsoft )?excel|pivot|vlookup|xlookup|macros?",
    "power bi": r"power ?bi",
    "tableau": r"tableau",
    "looker": r"looker",
    "python": r"\bpython\b",
    "vba": r"\bvba\b|macros?",
    "databricks": r"databricks",
    "google sheets": r"google sheets",
    "dashboards": r"dashboard",
    "mis": r"\bmis\b",
    "reporting": r"\breport(ing|s)?\b",
    "data analysis": r"data analy(sis|tics|ze|zing)|analy[sz]e data",
    "data visualization": r"visuali[sz]ation",
    "kpi": r"\bkpis?\b|metrics",
    "forecasting": r"forecast",
    "trend analysis": r"trend",
    "root cause analysis": r"root[- ]cause|\brca\b",
    "process improvement": r"process (improvement|optimi[sz]ation|excellence|re-?engineering)|continuous improvement|lean|six sigma",
    "process mapping": r"process (mapping|flows?|documentation)|workflow mapping|as-is|to-be",
    "sop": r"\bsops?\b|standard operating procedure",
    "automation": r"automat",
    "stakeholder management": r"stakeholder",
    "cross-functional": r"cross[- ]functional",
    "project management": r"project management|manage projects|project planning|project delivery",
    "program management": r"program(me)? management",
    "operations": r"\boperations?\b|\bops\b",
    "supply chain": r"supply[- ]chain",
    "logistics": r"logistic",
    "procurement": r"procurement|sourcing|purchase|rfq",
    "inventory": r"inventory",
    "vendor management": r"vendor",
    "capacity planning": r"capacity|workforce planning|resource (planning|allocation)",
    "compliance": r"complian|regulator|\baudit",
    "sla": r"\bslas?\b|\btat\b|turnaround",
    "business analysis": r"business analy",
    "requirements gathering": r"requirement",
    "documentation": r"documentation",
    "data validation": r"data (validation|quality|accuracy|integrity)",
    "budgeting": r"budget|\baop\b|annual operating plan",
    "crm": r"\bcrm\b|salesforce|freshdesk",
    "customer experience": r"customer (experience|service|support|fulfil)",
    "financial services": r"financial services|nbfc|lending|bank|fintech",
    "productivity": r"productivity|efficiency",
    "business insights": r"insight",
    "communication": r"communication",
    "problem solving": r"problem[- ]solving",
    "statistics": r"statistic",
    "machine learning": r"machine learning|\bml\b",
    "erp": r"\berp\b|\bsap\b|oracle",
    "jira": r"\bjira\b|confluence",
    "agile": r"agile|scrum",
    "pmp": r"\bpmp\b|prince2",
    "genai": r"genai|generative ai|\bllm|chatgpt",
    "bpm": r"\bbpm\b|business process management",
    "mba": r"\bmba\b|pgdm|post[- ]graduat",
}
# terms that are never auto-added unless the profile confirms them
UNSUPPORTED = {"erp", "machine learning", "inventory"}

FAMILY_RULES = [
    ("supply_chain", r"supply chain|logistics|procurement|sourcing|fulfil"),
    ("program", r"program|project manager|project coordinator|pmo"),
    ("operations", r"operations|ops\b|process"),
    ("data", r"data analyst|bi analyst|analytics"),
    ("analyst", r"analyst|mis"),
]


def family_for(title):
    t = title.lower()
    for fam, rx in FAMILY_RULES:
        if re.search(rx, t):
            return fam
    return "analyst"


def jd_terms(jd):
    jl = jd.lower()
    out = {}
    for term, rx in TAXONOMY.items():
        n = len(re.findall(rx, jl))
        if n:
            out[term] = 2 if n >= 2 else 1
    return out


def resume_text(r):
    parts = [r["headline"], r["summary"]]
    for e in r["experience"]:
        parts += [e["title"], e["company"]] + e["bullets"]
    parts += r["projects"]
    for k, v in r["skills"].items():
        parts += v
    for ed in r["education"]:
        parts.append(ed["degree"])
    return re.sub(r"\]\([^)]*\)|\*\*|\[", "", "\n".join(parts))


def years_required(jd):
    m = re.findall(r"(\d+)\s*(?:\+|-|–|to)?\s*(\d+)?\s*\+?\s*(?:years|yrs)", jd.lower())
    mins = [int(a) for a, b in m if int(a) < 15]
    return min(mins) if mins else None


def score(jd, title, r, pdf_path=None):
    terms = jd_terms(jd)
    rt = resume_text(r).lower()
    total = sum(terms.values()) or 1
    hit, missing = 0, []
    for t, w in terms.items():
        if re.search(TAXONOMY[t], rt):
            hit += w
        else:
            missing.append(t)
    kw = hit / total
    # title alignment
    tw = [w for w in re.findall(r"[a-z]+", title.lower()) if w not in {"senior", "sr", "junior", "jr", "associate", "i", "ii", "and", "the", "of", "lead"}]
    head = (r["headline"] + " " + " ".join(e["title"] for e in r["experience"]) + " " + r["summary"][:200]).lower()
    ta = (sum(1 for w in tw if w in head) / len(tw)) if tw else 1
    # experience
    yr = years_required(jd)
    if yr is None or yr <= CANDIDATE_YEARS + 0.6:
        ex = 1.0
    elif yr <= 4:
        ex = 0.6
    else:
        ex = 0.2
    edu = 1.0
    # parsability
    parse = 1.0
    if pdf_path and os.path.exists(pdf_path):
        txt = pdf_text(pdf_path).upper()
        need = ["PROFESSIONAL EXPERIENCE", "SKILLS", "EDUCATION", r["name"].upper()]
        parse = sum(1 for n in need if n in txt) / len(need)
    total_score = round(100 * (0.55 * kw + 0.15 * ta + 0.15 * ex + 0.05 * edu + 0.10 * parse), 1)
    return {
        "score": total_score,
        "keyword_match": round(100 * kw, 1),
        "title_match": round(100 * ta, 1),
        "experience_fit": round(100 * ex, 1),
        "years_required": yr,
        "parsability": round(100 * parse, 1),
        "jd_terms": sorted(terms),
        "missing": missing,
        "missing_unclaimable": [m for m in missing if m in UNSUPPORTED],
    }


def base_variant(fam):
    r = copy.deepcopy(BASE)
    r["headline"] = BASE["headlines"][fam]
    r["summary"] = BASE["summaries"][fam]
    return r


# JD term -> supported extra skill phrases that evidence it
EXTRA_FOR_TERM = {
    "sop": ["SOP Documentation"], "process mapping": ["Process Mapping"], "bpm": ["Business Process Management (BPM)"],
    "capacity planning": ["Capacity Planning"], "cross-functional": ["Cross-functional Coordination"],
    "logistics": ["Logistics Operations"], "procurement": ["Procurement Analytics"], "sla": ["SLA Monitoring"],
    "compliance": ["Regulatory Compliance"], "budgeting": ["Annual Operating Plan (AOP)"],
    "requirements gathering": ["Requirements Gathering"], "data validation": ["Data Validation"],
    "documentation": ["Reporting & Documentation"], "customer experience": ["Customer Fulfilment"],
    "vendor management": ["Vendor Coordination"], "program management": ["Program Coordination"],
    "project management": ["Project Coordination & Implementation Support"],
    "google sheets": ["Google Sheets"], "advanced excel": ["Pivot Tables", "VLOOKUP / XLOOKUP"],
    "business insights": ["Business Insights"], "crm": ["CRM Analytics (Freshdesk)"],
    "statistics": ["Statistical Analysis"], "productivity": ["Productivity Analysis"],
    "business analysis": ["Business Analysis"], "data analysis": ["Data Analysis & Ad-hoc Analysis"], "sql": ["SQL (Joins, CTEs, Window Functions)"],
    "communication": ["Stakeholder Communication"], "problem solving": ["Structured Problem Solving"],
    "data visualization": ["Data Visualization"],
}
CAT_FOR = {"Google Sheets": "Data Analysis & BI", "Pivot Tables": "Data Analysis & BI", "VLOOKUP / XLOOKUP": "Data Analysis & BI",
           "Business Insights": "Data Analysis & BI", "CRM Analytics (Freshdesk)": "Data Analysis & BI",
           "Statistical Analysis": "Data Analysis & BI", "Data Analysis & Ad-hoc Analysis": "Data Analysis & BI", "Data Visualization": "Data Analysis & BI"}


def tailor(jd, title):
    fam = family_for(title)
    r = base_variant(fam)
    terms = jd_terms(jd)

    def rel(text):
        tl = text.lower()
        return sum(w for t, w in terms.items() if re.search(TAXONOMY[t], tl))

    for e in r["experience"]:
        lead, rest = e["bullets"][0], e["bullets"][1:]
        e["bullets"] = [lead] + sorted(rest, key=lambda b: -rel(b))
    rt = resume_text(r).lower()
    for t in terms:
        if t in UNSUPPORTED or re.search(TAXONOMY[t], rt):
            continue
        allowed = {x for v in BASE.get("supported_extra_skills", {}).values() if isinstance(v, list) for x in v}
        for phrase in EXTRA_FOR_TERM.get(t, []):
            if phrase not in allowed:
                continue
            cat = next((k for k, v in BASE.get("supported_extra_skills", {}).items() if isinstance(v, list) and phrase in v), "Business Operations")
            if phrase not in r["skills"][cat]:
                r["skills"][cat].append(phrase)
    for cat in r["skills"]:
        r["skills"][cat] = sorted(r["skills"][cat], key=lambda s: -rel(s))
    # for ops / PM / supply chain roles, lead with Business Operations skills
    if fam in ("operations", "program", "supply_chain"):
        first = [k for k in r["skills"] if "operation" in k.lower() or "business" in k.lower()]
        r["skills"] = {k: r["skills"][k] for k in first + [k for k in r["skills"] if k not in first]}
    r["family"] = fam
    for k in ("headlines", "summaries", "supported_extra_skills", "evidence_map", "needs_confirmation",
              "never_claim", "target_titles", "years_experience"):
        r.pop(k, None)
    return r


# ---------------- PDF rendering ----------------
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER

def _find_font_dir():
    """Carlito (metric-compatible with Calibri) if installed, else Calibri itself, else built-in Helvetica."""
    cands = [os.environ.get("JOBPILOT_FONT_DIR", ""), "/usr/share/fonts/truetype/crosextra/",
             "/usr/share/fonts/crosextra-carlito/", "/usr/local/share/fonts/", os.path.expanduser("~/Library/Fonts/"),
             "/Library/Fonts/", os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts/")]
    for d in cands:
        if d and os.path.exists(os.path.join(d, "Carlito-Regular.ttf")):
            return d, ("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf")
        if d and os.path.exists(os.path.join(d, "calibri.ttf")):
            return d, ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf")
    return None, None


FD, _FILES = _find_font_dir()
if FD:
    for name, f in zip(("Body", "Body-B", "Body-I", "Body-BI"), _FILES):
        pdfmetrics.registerFont(TTFont(name, os.path.join(FD, f)))
    from reportlab.lib.fonts import addMapping
    addMapping("Body", 0, 0, "Body"); addMapping("Body", 1, 0, "Body-B"); addMapping("Body", 0, 1, "Body-I"); addMapping("Body", 1, 1, "Body-BI")
    FONT, FONT_B, FONT_I, FONT_BI = "Body", "Body-B", "Body-I", "Body-BI"
else:  # no Carlito/Calibri: Helvetica is a little wider, so render_fit may trim one more bullet
    FONT, FONT_B, FONT_I, FONT_BI = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"

NAVY = HexColor("#1F3864")


def md(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" color="#1F5FBF"><u>\1</u></a>', s)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def render(r, path, size=9.5):
    st = lambda **k: ParagraphStyle("x", **{"fontName": FONT, "fontSize": size, "leading": size * 1.18, **k})
    name = st(fontSize=16, leading=19, alignment=TA_CENTER, textColor=NAVY, fontName=FONT_B)
    center = st(alignment=TA_CENTER)
    headl = st(alignment=TA_CENTER, textColor=NAVY, fontName=FONT_B)
    sec = st(fontSize=11, leading=13, textColor=NAVY, fontName=FONT_B, spaceBefore=4)
    body = st()
    bul = st(leftIndent=0)
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=31, rightMargin=31, topMargin=28, bottomMargin=28,
                            title=f"{r['name']} Resume", author=r["name"])
    W = A4[0] - 62
    f = [Paragraph(r["name"], name), Paragraph(md(r["contact"]), center), Paragraph(md(r["headline"]), headl)]

    def section(t):
        f.append(Paragraph(t, sec))
        f.append(HRFlowable(width="100%", thickness=0.8, color=NAVY, spaceBefore=1, spaceAfter=3))

    def row(left, right, lst, rst):
        t = Table([[Paragraph(left, lst), Paragraph(right, rst)]], colWidths=[W * 0.7, W * 0.3])
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        f.append(t)

    rb = st(alignment=2, fontName=FONT_B); ri = st(alignment=2, fontName=FONT_I)
    bodyb = st(fontName=FONT_B); bodyi = st(fontName=FONT_I)

    def bullets(items):
        f.append(ListFlowable([ListItem(Paragraph(md(b), bul), leftIndent=12, value="•") for b in items],
                              bulletType="bullet", start="•", leftIndent=12, bulletFontSize=size))

    section("PROFESSIONAL SUMMARY")
    f.append(Paragraph(md(r["summary"]), body))
    section("PROFESSIONAL EXPERIENCE")
    for e in r["experience"]:
        row(md(e["company"]), md(e["location"]), bodyb, rb)
        row(md(e["title"]), md(e["dates"]), bodyi, ri)
        bullets(e["bullets"])
    section("PROJECTS")
    bullets(r["projects"])
    section("SKILLS")
    for k, v in r["skills"].items():
        f.append(Paragraph(f"<b>{md(k)}:</b> " + md(", ".join(v)), body))
    section("EDUCATION")
    for ed in r["education"]:
        row(md(ed["school"]), md(ed["location"]), bodyb, rb)
        row(md(ed["degree"]), md(ed["dates"]), bodyi, ri)
    section("AWARDS")
    aw = r["awards"] if isinstance(r["awards"], list) else ["**" + r["awards"] + "**"]
    bullets(aw)
    doc.build(f)
    return doc.page


def render_fit(r, path):
    """Fit one page at 10.5pt+ by cutting content, never shrinking type below 10pt.
    Cut order: internship bullets, then extra projects, then lowest-ranked full-time bullets.
    A job's lead (original first) bullet is never dropped."""
    for size in (9.5,):
        render(r, path, size)
        if pages(path) == 1:
            return r
    rr = copy.deepcopy(r)
    leads = {e["company"]: e["bullets"][0] for e in BASE["experience"]}
    def cut_job(company, floor):
        for e in rr["experience"]:
            if e["company"] == company and len(e["bullets"]) > floor:
                for b in reversed(e["bullets"]):
                    if b != leads.get(company):
                        e["bullets"].remove(b); return True
        return False
    jobs = [e["company"] for e in rr["experience"]]            # most recent first
    oldest = jobs[-1] if jobs else None
    steps = [lambda: cut_job(oldest, 3), lambda: len(rr["projects"]) > 4 and bool(rr["projects"].pop()),
             lambda: cut_job(oldest, 2), lambda: len(rr["projects"]) > 3 and bool(rr["projects"].pop())]
    for c in jobs[:-1][::-1]:
        steps += [lambda c=c: cut_job(c, 4), lambda c=c: cut_job(c, 3)]
    for step in steps:
        render(rr, path, 9.5)
        if pages(path) == 1:
            break
        step()
    render(rr, path, 9.5)
    return rr


def pages(path):
    from pypdf import PdfReader
    return len(PdfReader(path).pages)


def pdf_text(path):
    """Plain text of a PDF: pdftotext when installed (closest to what ATS parsers see), else pypdf."""
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True)
        if out.returncode == 0:
            return out.stdout
    from pypdf import PdfReader
    return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)


# ---------------- Shortlist ATS Scanner loop ----------------
HERE_JS = os.path.join(HERE, "ats_score.js")  # Shortlist ATS Scanner scoring (MIT, github.com/dibyanshi29/shortlist-ats-scanner)

# JD keyword (as the scanner names it) -> honest skill phrase backed by the candidate's experience.
# Anything not listed here is never added. "confirm" items need a yes first (see CONFIRMED).
EVIDENCE = {}  # filled from profile "evidence_map": JD keyword -> [skills category, honest phrase]
# Need the candidate's confirmation before use (set True once they confirm).
CONFIRM = {}   # filled from profile "needs_confirmation"; used only for keywords listed in confirmed_skills.json
_cf = os.path.join(PROFILE_DIR, "confirmed_skills.json")
CONFIRMED = set(json.load(open(_cf, encoding="utf-8"))) if os.path.exists(_cf) else set()

# Profile overrides: base_resume.json may define "evidence_map", "needs_confirmation", "never_claim", "target_titles".
EVIDENCE.update({k: tuple(v) for k, v in BASE.get("evidence_map", {}).items()})
CONFIRM.update({k: tuple(v) for k, v in BASE.get("needs_confirmation", {}).items()})
UNSUPPORTED |= set(BASE.get("never_claim", []))

CORE_TITLES = BASE.get("target_titles") or ["business analyst", "operations analyst", "mis analyst", "data analyst", "process analyst",
               "supply chain analyst", "business operations analyst", "operations specialist", "operations associate",
               "program manager", "project manager", "reporting and analytics", "planning analyst", "analyst"]


def core_title(title):
    t = re.sub(r"\s+[-–—|,(].*$", "", title.lower()).strip()
    return t


def ats(r, jd, title, tmp=None):
    """Render, extract text, and score with the Shortlist ATS Scanner (node)."""
    d = tempfile.mkdtemp(prefix="jobpilot_")
    pdf, rt, jt = (os.path.join(d, n) for n in ("ats.pdf", "resume.txt", "jd.txt"))
    try:
        render_fit(r, pdf)
        open(rt, "w", encoding="utf-8").write(pdf_text(pdf))
        open(jt, "w", encoding="utf-8").write(jd)
        out = subprocess.run(["node", HERE_JS, rt, jt, core_title(title)], capture_output=True, text=True, encoding="utf-8")
        if out.returncode != 0:
            raise RuntimeError("ATS scanner failed (is Node 18+ installed?): " + out.stderr[-400:])
        return json.loads(out.stdout)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def tailor_loop(jd, title, target=80, rounds=4):
    r = tailor(jd, title)
    ct = core_title(title)
    # put the exact (core) job title in the headline when it honestly describes their work
    if any(ct == c or ct.endswith(c) for c in CORE_TITLES) and ct.title() not in r["headline"]:
        r["headline"] = ct.title().replace("And", "and") + " | " + " | ".join(r["headline"].split(" | ")[1:])
    history, not_addable = [], set()
    for i in range(rounds):
        res = ats(r, jd, title)
        history.append(res["score"])
        if res["score"] >= target:
            break
        added = False
        for g in res["gaps"]:
            k = g["k"]
            src = EVIDENCE.get(k) or (CONFIRM.get(k) if k in CONFIRMED else None)
            if not src:
                if k in CONFIRM: not_addable.add(k + " (needs your confirmation)")
                continue
            cat, phrase = src
            need = 2 if g["jd"] >= 3 else 1
            have = g["resume"]
            if have < need:
                if phrase not in r["skills"].setdefault(cat, []):
                    r["skills"][cat].append(phrase); added = True; have += 1
                if have < need and phrase.lower() not in r["summary"].lower():
                    r["summary"] = r["summary"].rstrip(".") + f"; strong in {phrase}."
                    added = True
            elif g.get("spelling") and phrase not in r["skills"].setdefault(cat, []):
                r["skills"][cat].append(phrase); added = True
        if not added:
            break
    res = ats(r, jd, title)
    if not history or history[-1] != res["score"]:
        history.append(res["score"])
    return r, res, history, sorted(not_addable)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("jd")
    ap.add_argument("--title", default="Analyst")
    ap.add_argument("--resume")
    ap.add_argument("--out")
    a = ap.parse_args()
    jd = open(a.jd, encoding="utf-8").read()
    if a.cmd == "score":
        r = json.load(open(a.resume, encoding="utf-8")) if a.resume else base_variant("data")
        print(json.dumps(score(jd, a.title, r), indent=1))
    elif a.cmd == "loop":
        r, res, hist, na = tailor_loop(jd, a.title)
        r = render_fit(r, a.out + ".pdf")
        json.dump(r, open(a.out + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(json.dumps({"ats_score": res["score"], "history": hist, "parts": res["parts"],
                          "still_missing": [g["k"] for g in res["gaps"]], "needs_confirmation": na}, indent=1))
    elif a.cmd == "rescore":
        # re-render + re-score a hand-edited tailored resume JSON (used for the rewrite pass)
        r = json.load(open(a.resume, encoding="utf-8"))
        res = ats(r, jd, a.title)
        r = render_fit(r, a.out + ".pdf")
        json.dump(r, open(a.out + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(json.dumps({"ats_score": res["score"], "parts": res["parts"],
                          "still_missing": [g["k"] for g in res["gaps"]], "checks": res["checks"]}, indent=1))
    elif a.cmd == "tailor":
        base = base_variant("data")
        before = score(jd, a.title, base)
        r = tailor(jd, a.title)
        r = render_fit(r, a.out + ".pdf")
        json.dump(r, open(a.out + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        after = score(jd, a.title, r, a.out + ".pdf")
        print(json.dumps({"before": before["score"], "after": after}, indent=1))
