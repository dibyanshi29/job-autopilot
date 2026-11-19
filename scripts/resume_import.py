#!/usr/bin/env python3
"""Pre-fill profile/base_resume.json from an existing resume (PDF, DOCX or TXT).

  python resume_import.py resume.pdf [--out profile/base_resume.json] [--force]

Reads the usual one- or two-column resume layout:
  Name / contact line / optional headline / SUMMARY / EXPERIENCE (company + location, title + dates, bullets)
  / PROJECTS / SKILLS ("Category: a, b, c") / EDUCATION / AWARDS or CERTIFICATIONS.
It never invents anything – it only moves text from your resume into the right fields, and every skill it finds
becomes an evidence_map entry (because your resume already claims it). Always read the result and fix what it
misread; the report at the end tells you what to check.
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys, zipfile

MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
DATE = re.compile(rf"((?:{MONTHS})[a-z]*\.?\s*'?\d{{2,4}}|\d{{1,2}}/\d{{4}}|\b(?:19|20)\d{{2}}\b)\s*(?:–|—|-|to)\s*"
                  rf"((?:{MONTHS})[a-z]*\.?\s*'?\d{{2,4}}|\d{{1,2}}/\d{{4}}|\b(?:19|20)\d{{2}}\b|present|current|now|till date|date)", re.I)
BULLET = re.compile("^\\s*(?:[\u2022\u25cf\u25aa\u25e6\u2023\u2219\u00b7\u25a0\u25ba\u27a2\u2713\uf0b7\uf0a7\uf076\uf0d8\x7f\x95]\\s*|[-*\u2013]\\s+)(?=\\S)")  # symbol bullets (incl. Word symbol-font / PDF-extraction codes) or "- " / "* "
HEADINGS = {
    "summary": r"(professional |career )?(summary|profile|objective|about me)",
    "experience": r"(professional |work |relevant )?(experience|employment( history)?|work history)",
    "projects": r"(key |academic |personal )?projects?",
    "skills": r"(technical |core |key )?(skills|competencies|tools|technical skills)( & tools| and tools)?",
    "education": r"education( & certifications?)?|academics?|qualifications?",
    "awards": r"(awards?|achievements?|certifications?|honou?rs?|accomplishments?)( & (awards?|achievements?|certifications?))?",
}
FAMILIES = ["analyst", "data", "operations", "supply_chain", "program"]


# ---------------------------------------------------------------- text extraction
def text_of(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        if shutil.which("pdftotext"):
            out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, encoding="utf-8")
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout
        from pypdf import PdfReader
        pages = []
        for p in PdfReader(path).pages:
            try:
                pages.append(p.extract_text(extraction_mode="layout") or "")
            except TypeError:  # old pypdf
                pages.append(p.extract_text() or "")
        return "\n".join(pages)
    if ext == ".docx":
        z = zipfile.ZipFile(path)
        xml = z.read("word/document.xml").decode("utf-8")
        try:  # keep Word hyperlinks as [text](url)
            rels = dict(re.findall(r'Id="([^"]+)"[^>]*?Target="([^"]+)"[^>]*?TargetMode="External"',
                                   z.read("word/_rels/document.xml.rels").decode("utf-8")))
        except KeyError:
            rels = {}
        def _link(m):
            url = rels.get(m.group(1))
            txt = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", m.group(2)))
            return f"<w:r><w:t>[{txt}]({url})</w:t></w:r>" if url and txt.strip() else m.group(2)
        xml = re.sub(r'<w:hyperlink[^>]*?r:id="([^"]+)"[^>]*>(.*?)</w:hyperlink>', _link, xml, flags=re.S)
        paras = []
        for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
            p = re.sub(r"<w:tab/>", "\t", p)
            p = re.sub(r"<w:br/>", "\n", p)
            t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>|(\t)", p) and
                        [a or b for a, b in re.findall(r"<w:t[^>]*>([^<]*)</w:t>|(\t)", p)])
            if "<w:numPr>" in p and t.strip():
                t = "• " + t
            paras.append(t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'"))
        return "\n".join(paras)
    return open(path, encoding="utf-8", errors="replace").read()


# ---------------------------------------------------------------- helpers
def split_lr(line):
    """'GoComet        Bangalore' -> ('GoComet', 'Bangalore'); tabs or 3+ spaces separate columns."""
    parts = [p.strip() for p in re.split(r"\t+|\s{3,}", line.strip()) if p.strip()]
    if len(parts) >= 2:
        return " ".join(parts[:-1]), parts[-1]
    m = DATE.search(line)
    if m:  # 'Analyst, Acme  Jan 2020 – Present' with only one space before the date
        return line[:m.start()].strip(" ,|–-"), line[m.start():].strip()
    return line.strip(), ""


def heading_of(line):
    s = re.sub(r"[^a-z& ]", "", line.strip().lower()).strip()
    if not s or len(s) > 40:
        return None
    for key, rx in HEADINGS.items():
        if re.fullmatch(rx, s):
            return key
    return None


def linkify(contact):
    def one(tok):
        t = tok.strip()
        if re.fullmatch(r"\[[^\]]+\]\([^)]+\)", t):
            return t
        if re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.]+", t):
            return f"[{t}](mailto:{t})"
        if re.fullmatch(r"(https?://)?(www\.)?[\w-]+(\.[\w-]+)+(/[\w./%#?=&-]*)?", t) and not re.fullmatch(r"[\d.]+", t):
            url = t if t.startswith("http") else "https://" + t
            return f"[{re.sub(r'^https?://(www\.)?', '', t)}]({url})"
        return t
    return " | ".join(one(t) for t in re.split(r"\s*[|•·]\s*|\s{3,}", contact) if t.strip())


def month_index(s, today):
    s = s.lower().strip()
    if s in ("present", "current", "now", "till date", "date"):
        return today.year * 12 + today.month
    m = re.match(rf"({MONTHS})[a-z]*\.?\s*'?(\d{{2,4}})", s)
    if m:
        y = int(m.group(2)); y = y + 2000 if y < 100 else y
        return y * 12 + ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].index(m.group(1)[:3]) + 1
    m = re.match(r"(\d{1,2})/(\d{4})", s)
    if m:
        return int(m.group(2)) * 12 + int(m.group(1))
    m = re.match(r"(\d{4})", s)
    return int(m.group(1)) * 12 + 1 if m else None


# ---------------------------------------------------------------- parse
def parse(text):
    lines = [l.rstrip() for l in text.replace("\r", "").split("\n")]
    lines = [l for l in lines if l.strip() and not re.fullmatch(r"\s*(page \d+( of \d+)?|\d+)\s*", l, re.I)]
    i, head = 0, []
    while i < len(lines) and not heading_of(lines[i]):
        head.append(lines[i].strip()); i += 1
    sections, cur = {}, None
    for l in lines[i:]:
        h = heading_of(l)
        if h:
            cur = h; sections.setdefault(cur, []); continue
        if cur:
            sections[cur].append(l)

    name = head[0] if head else ""
    contact_lines = [h for h in head[1:] if re.search(r"@|\+?\d[\d\s-]{7,}|linkedin|github|https?://|\.\w{2,3}/", h, re.I)]
    other = [h for h in head[1:] if h not in contact_lines]
    contact = linkify(" | ".join(contact_lines))
    headline = other[0] if other else ""

    summary = " ".join(l.strip() for l in sections.get("summary", []))

    def entries(sec, kind):
        out, e = [], None
        for l in sections.get(sec, []):
            if BULLET.match(l):
                if e is not None:
                    e["bullets"].append(BULLET.sub("", l).strip())
                continue
            left, right = split_lr(l)
            is_date = bool(DATE.search(right)) or bool(DATE.search(l) and not right)
            indented_cont = l.startswith("   ") and e and e["bullets"] and not right
            if indented_cont or (e and e["bullets"] and not right and l[:1] == " "):
                e["bullets"][-1] += " " + l.strip(); continue
            if is_date and e is not None and not e.get("_dated"):
                e["second"], e["dates"], e["_dated"] = left, right or DATE.search(l).group(0), True
            elif e is not None and not e["bullets"] and not e.get("_dated") and not e.get("second"):
                e["second"] = left  # title line without dates
                if right: e["dates"] = right
            else:
                e = {"first": left, "right": right if not is_date else "", "second": "", "dates": right if is_date else "", "bullets": [], "_dated": is_date}
                out.append(e)
        res = []
        for e in out:
            if kind == "job":
                res.append({"company": e["first"], "location": e["right"], "title": e["second"], "dates": e["dates"], "bullets": e["bullets"]})
            else:
                res.append({"school": e["first"], "location": e["right"], "degree": e["second"], "dates": e["dates"]})
        return res

    experience = entries("experience", "job")
    education = entries("education", "edu")

    projects, awards = [], []
    for key, bucket in (("projects", projects), ("awards", awards)):
        for l in sections.get(key, []):
            if BULLET.match(l) or not bucket:
                bucket.append(BULLET.sub("", l).strip())
            else:
                bucket[-1] += " " + l.strip()

    skills, last_cat = {}, None
    for l in sections.get("skills", []):
        s = BULLET.sub("", l).strip()
        m = re.match(r"([^:,()]{2,40}):\s*(.+)", s)
        if m:
            cat, items = m.group(1).strip(), m.group(2)
        else:  # wrapped line: continues the previous category
            cat, items = (last_cat or "Skills"), s
        last_cat = cat
        depth, buf, parts = 0, "", []
        for ch in items:  # split on , ; | • but not inside brackets: "SQL (Joins, CTEs)" stays one skill
            depth += (ch in "([") - (ch in ")]")
            if ch in ",;|•" and depth <= 0:
                parts.append(buf); buf = ""
            else:
                buf += ch
        parts.append(buf)
        for it in parts:
            it = it.strip(" .")
            if not it:
                continue
            lst = skills.setdefault(cat, [])
            if lst and lst[-1].count("(") > lst[-1].count(")"):  # bracket opened on the previous line
                lst[-1] += ", " + it
            elif len(it) < 60 and it not in lst:
                lst.append(it)

    today = datetime.date.today()
    months = 0
    for e in experience:
        if re.search(r"intern|trainee|apprentice", e["title"] + " " + e["company"], re.I):
            continue
        m = DATE.search(e["dates"])
        if m:
            a, b = month_index(m.group(1), today), month_index(m.group(2), today)
            if a and b and b >= a:
                months += b - a + 1
    years = round(months / 12 * 2) / 2

    titles = []
    for e in experience:
        t = re.sub(r"\s*[,(].*$", "", e["title"]).strip().lower()
        if t and not re.search(r"intern|trainee", t) and t not in titles:
            titles.append(t)

    evidence = {}
    for cat, items in skills.items():
        for it in items:
            key = re.sub(r"\s*\(.*?\)", "", it).strip().lower()
            if key and key not in evidence:
                evidence[key] = [cat, it]

    return {
        "name": name, "years_experience": years, "contact": contact,
        "headlines": {f: headline for f in FAMILIES}, "summaries": {f: summary for f in FAMILIES},
        "target_titles": titles, "experience": experience, "projects": projects, "skills": skills,
        "supported_extra_skills": {}, "education": education, "awards": awards,
        "evidence_map": evidence, "needs_confirmation": {}, "never_claim": [],
    }


def report(r):
    warn = []
    if not r["name"]: warn.append("name not found – first line of the resume")
    if "@" not in r["contact"]: warn.append("no email found in the contact line")
    if not r["headlines"]["data"]: warn.append("no headline (the line under your contact details) – add one per role family")
    if not r["summaries"]["data"]: warn.append("no summary section found")
    if not r["experience"]: warn.append("no experience entries found – check the EXPERIENCE heading")
    for e in r["experience"]:
        miss = [k for k in ("company", "title", "dates") if not e[k]]
        if miss: warn.append(f"job '{e['company'] or e['title']}': missing {', '.join(miss)}")
        if not e["bullets"]: warn.append(f"job '{e['company']}': no bullet points found")
    if not r["skills"]: warn.append("no skills found")
    if not r["education"]: warn.append("no education found")
    lines = [f"Imported: {r['name'] or '?'} · {len(r['experience'])} jobs · {sum(len(e['bullets']) for e in r['experience'])} bullets · "
             f"{len(r['projects'])} projects · {sum(len(v) for v in r['skills'].values())} skills · {len(r['education'])} education · "
             f"{r['years_experience']:g} yrs (excl. internships)"]
    for e in r["experience"]:
        lines.append(f"  - {e['title'] or '?'} @ {e['company'] or '?'} ({e['dates'] or 'no dates'}), {len(e['bullets'])} bullets")
    lines += ["Check:"] + [f"  ! {w}" for w in warn] if warn else []
    lines += ["Next: open base_resume.json and check every field. Then tailor headlines/summaries per role family, put a job's",
              "strongest bullet first, wrap key numbers in **bold**, and move skills you're unsure of from evidence_map to",
              "needs_confirmation. Then run: python jobpilot.py doctor"]
    return "\n".join(lines)


def main(argv=None):
    for _s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252; print UTF-8 everywhere
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Pre-fill base_resume.json from your resume")
    ap.add_argument("resume")
    ap.add_argument("--out", default=os.path.join(os.environ.get("JOBPILOT_PROFILE", "profile"), "base_resume.json"))
    ap.add_argument("--force", action="store_true", help="overwrite an existing base_resume.json")
    a = ap.parse_args(argv)
    return run(a.resume, a.out, a.force)


def run(resume, out, force=False):
    if not os.path.exists(resume):
        print(f"not found: {resume}"); return 2
    r = parse(text_of(resume))
    if os.path.exists(out) and not force:
        try:
            cur = json.load(open(out, encoding="utf-8"))
        except Exception:
            cur = {}
        if cur.get("name") not in (None, "", "Ananya Rao"):  # a real profile – don't clobber it
            alt = out.replace(".json", ".imported.json")
            json.dump(r, open(alt, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            print(report(r)); print(f"\n{out} already has your profile, so this was saved to {alt} (use --force to overwrite).")
            return 0
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(r, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(report(r)); print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
