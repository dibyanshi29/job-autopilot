#!/usr/bin/env python3
"""One-page cover letter: scaffold a draft from your real resume, fact-check it, render a matching PDF.

  python cover_letter.py draft  <app_dir>   -> writes <app_dir>/cover.md (an outline the agent/user fills in)
  python cover_letter.py check  <app_dir>   -> fact check only
  python cover_letter.py render <app_dir>   -> fact check, then <app_dir>/cover.pdf

<app_dir> is the folder `jobpilot.py tailor` made (it has resume.json, job.json, jd.txt).

Fact check (the letter is refused if it fails):
  * every number in the letter (40+, 2 days, 12 stores, 30%) must appear in your profile or tailored resume
  * no word from never_claim may appear
  * no leftover [placeholders]
  * at most ~350 words, so it fits one page
Fact-grounding idea from ai-job-search (MIT, Mads Lorentzen).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PROFILE_DIR = os.environ.get("JOBPILOT_PROFILE", os.path.join(os.getcwd(), "profile"))


def _load(app):
    r = json.load(open(os.path.join(app, "resume.json"), encoding="utf-8"))
    job = json.load(open(os.path.join(app, "job.json"), encoding="utf-8")) if os.path.exists(os.path.join(app, "job.json")) else {}
    base = json.load(open(os.path.join(PROFILE_DIR, "base_resume.json"), encoding="utf-8"))
    return r, job, base


def _plain(s):
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s).replace("**", "")


def draft(app):
    r, job, base = _load(app)
    jd = open(os.path.join(app, "jd.txt"), encoding="utf-8").read() if os.path.exists(os.path.join(app, "jd.txt")) else ""
    company, role = job.get("company", "[Company]"), job.get("title", "[Role]")
    pp = os.path.join(PROFILE_DIR, "preferences.json")
    notice = json.load(open(pp, encoding="utf-8")).get("notice_period", "notice period") if os.path.exists(pp) else "notice period"
    lead = [_plain(e["bullets"][0]) for e in r.get("experience", []) if e.get("bullets")]
    out = f"""Dear Hiring Team at {company},

[Opening, 2 sentences: the {role} role, and one concrete reason this company/team interests you – from the posting, not generic.]

[Proof paragraph, 3-4 sentences: pick the 2 achievements below that best match the posting's top requirements and say what they mean for this role. Keep every number exactly as written.]

[Fit paragraph, 2-3 sentences: tools/ways of working the posting asks for that your resume shows; nothing new.]

[Close, 1-2 sentences: availability ({notice}) and a simple ask for a conversation.]

Sincerely,
{base.get('name', '')}

<!-- Facts you may use (from your resume):
""" + "\n".join("- " + b for b in lead) + "\n" + "\n".join("- " + _plain(b) for e in r.get("experience", []) for b in e.get("bullets", [])[1:3]) + f"""
Top posting words: {', '.join(job.get('top_terms', [])[:12])}
Delete this comment block before rendering. -->
"""
    p = os.path.join(app, "cover.md")
    if os.path.exists(p):
        sys.exit(f"{p} already exists; edit it or delete it first")
    open(p, "w", encoding="utf-8").write(out)
    return p


def check(app):
    r, job, base = _load(app)
    text = open(os.path.join(app, "cover.md"), encoding="utf-8").read()
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()
    facts = (json.dumps(base, ensure_ascii=False) + json.dumps(r, ensure_ascii=False)).lower()
    problems = []
    for ph in re.findall(r"\[[^\]]{3,}\](?!\()", text):
        problems.append(f"placeholder left: {ph[:60]}")
    for num in set(re.findall(r"\d+(?:[.,]\d+)?\s*(?:%|\+|x)?", text)):
        n = num.strip()
        core = re.sub(r"[%+x]$", "", n).strip()
        if core and core not in facts:
            problems.append(f"number not in your profile: {n}")
    for w in base.get("never_claim", []):
        if re.search(r"\b" + re.escape(w.lower()) + r"\b", text.lower()):
            problems.append(f"never_claim word used: {w}")
    words = len(text.split())
    if words > 350:
        problems.append(f"{words} words – trim to 350 or fewer for one page")
    return text, problems


def render(app):
    import engine  # registers fonts, reads profile
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    text, problems = check(app)
    if problems:
        print("cover letter NOT rendered – fix these first:")
        for p in problems:
            print("  x " + p)
        return None
    r, job, base = _load(app)
    path = os.path.join(app, "cover.pdf")
    F = engine.FONT
    st = lambda **k: ParagraphStyle("c", **{"fontName": F, "fontSize": 10.5, "leading": 14, **k})
    doc = SimpleDocTemplate(path, pagesize=(595.27, 841.89), leftMargin=56, rightMargin=56, topMargin=48, bottomMargin=48)
    flow = [Paragraph(f"<b>{engine.md(base['name'])}</b>", st(fontSize=16, leading=20, alignment=TA_CENTER, textColor=engine.NAVY)),
            Paragraph(engine.md(base.get("contact", "")), st(fontSize=9, alignment=TA_CENTER)), Spacer(1, 18)]
    import datetime
    flow += [Paragraph(datetime.date.today().strftime("%d %B %Y"), st()), Spacer(1, 10)]
    for para in re.split(r"\n\s*\n", text):
        flow += [Paragraph(engine.md(para.strip()).replace("\n", "<br/>"), st()), Spacer(1, 8)]
    doc.build(flow)
    if engine.pages(path) > 1:
        print("warning: cover letter runs past one page – shorten it")
    return path


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("draft", "check", "render"):
        sys.exit(__doc__)
    cmd, app = sys.argv[1], sys.argv[2]
    if cmd == "draft":
        print("wrote", draft(app))
    elif cmd == "check":
        _, probs = check(app)
        print("cover letter OK" if not probs else "\n".join("x " + p for p in probs))
        sys.exit(1 if probs else 0)
    else:
        p = render(app)
        print("wrote", p) if p else sys.exit(1)
