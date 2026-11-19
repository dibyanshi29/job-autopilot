#!/usr/bin/env python3
"""jobpilot – honest, ATS-checked job applications from one command.

  python jobpilot.py init                       create ./profile from the templates
  python jobpilot.py import resume.pdf          pre-fill profile/base_resume.json from your resume (PDF, DOCX or TXT)
  python jobpilot.py doctor                     check Python, Node, fonts
  python jobpilot.py new <posting> --company "Acme" --title "Data Analyst" [--location ..] [--salary ..] [--url ..]
                                                safety check -> fit check -> tailor + ATS loop -> apps/<acme-data-analyst>/
  python jobpilot.py rank <folder> [--top 10]   safety + fit + quick ATS for every posting in a folder -> ranked shortlist
  python jobpilot.py rescore <app>              re-render + re-score after you edit <app>/resume.json
  python jobpilot.py cover <app> [--render]     draft cover.md, then --render to fact-check and build cover.pdf
  python jobpilot.py kit <app>                  application kit: files to attach, apply link, ready-to-paste answers
  python jobpilot.py prep <app>                 interview prep sheet mapping the posting to your real experience
  python jobpilot.py stage <app> <stage>        found | tailored | applied | interview | offer | rejected | skipped
  python jobpilot.py pack [--out FILE]          save profile + applications into one zip to keep between chats
  python jobpilot.py unpack <pack.zip>          restore them from that zip
  python jobpilot.py list [--csv]               every application with score and stage

Options: --profile DIR (default ./profile or $JOBPILOT_PROFILE), --apps DIR (default ./apps), --target 80
"""
import argparse, csv, datetime, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)
STAGES = ["found", "skipped", "tailored", "applied", "interview", "offer", "rejected"]


def slug(*parts):
    s = "-".join(re.sub(r"[^a-z0-9]+", "-", p.lower()).strip("-") for p in parts if p)
    return s[:60] or "job"


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def save_job(app, job):
    json.dump(job, open(os.path.join(app, "job.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def load_job(app):
    p = os.path.join(app, "job.json")
    if not os.path.exists(p):
        sys.exit(f"{app} is not an application folder (no job.json)")
    return json.load(open(p, encoding="utf-8"))


# ---------------------------------------------------------------- commands
def cmd_init(a):
    os.makedirs(a.profile, exist_ok=True)
    pairs = [("base_resume.example.json", "base_resume.json"), ("confirmed_skills.example.json", "confirmed_skills.json"),
             ("preferences.example.json", "preferences.json"), ("RUNBOOK.template.md", "RUNBOOK.md")]
    for src, dst in pairs:
        d = os.path.join(a.profile, dst)
        if os.path.exists(d):
            print(f"  kept     {d}")
        else:
            shutil.copy(os.path.join(ROOT, "templates", src), d)
            print(f"  created  {d}")
    if getattr(a, "quiet", False):
        return 0
    print(f"""
Next:
  1. python jobpilot.py import your_resume.pdf   (fills base_resume.json; then read it and fix anything misread)
  2. Set roles, cities, salary floor and deal-breakers in {a.profile}/preferences.json.
  3. python jobpilot.py doctor
  4. python jobpilot.py new posting.txt --company "Acme" --title "Data Analyst"
Your profile holds personal data – keep it out of any public repo (it is in .gitignore here).""")
    return 0


def cmd_import(a):
    import resume_import
    if not os.path.exists(os.path.join(a.profile, "preferences.json")):
        cmd_init(argparse.Namespace(profile=a.profile, quiet=True))
    return resume_import.run(a.resume, os.path.join(a.profile, "base_resume.json"), a.force)


def cmd_doctor(a):
    ok = True
    def line(good, msg, fix=""):
        nonlocal ok
        ok &= good or fix.startswith("optional")
        print(("  ok   " if good else "  --   ") + msg + ("" if good else f"   -> {fix}"))
    print(f"Python {sys.version.split()[0]}")
    line(sys.version_info >= (3, 9), "Python 3.9+", "install Python 3.9 or newer")
    for mod in ("reportlab", "pypdf"):
        try:
            __import__(mod); line(True, mod)
        except ImportError:
            line(False, mod, "pip install -r requirements.txt")
    node = shutil.which("node")
    v = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else ""
    line(bool(v) and int(v.lstrip("v").split(".")[0]) >= 18, f"Node {v or 'missing'} (runs the ATS scanner)", "install Node 18+ from nodejs.org")
    line(bool(shutil.which("pdftotext")), "pdftotext (closest to real ATS text extraction)", "optional: poppler-utils; pypdf is used instead")
    try:
        os.environ["JOBPILOT_PROFILE"] = a.profile
        if os.path.exists(os.path.join(a.profile, "base_resume.json")):
            import engine
            line(engine.FONT == "Body", "resume font (Carlito/Calibri)", "optional: install fonts-crosextra-carlito; Helvetica is used instead")
            line(True, f"profile {a.profile}")
        else:
            line(False, f"profile {a.profile}", "python jobpilot.py init")
    except SystemExit as e:
        line(False, "profile", str(e))
    print("ready" if ok else "fix the items marked --")
    return 0 if ok else 1


def cmd_new(a):
    os.environ["JOBPILOT_PROFILE"] = a.profile
    import posting_guard, fit, engine
    raw = open(a.posting, encoding="utf-8", errors="replace").read()
    jd, guard = posting_guard.guard(raw)
    app = os.path.join(a.apps, slug(a.company, a.title))
    os.makedirs(app, exist_ok=True)
    open(os.path.join(app, "jd.txt"), "w", encoding="utf-8").write(jd + "\n")
    job = {"company": a.company, "title": a.title, "location": a.location, "url": a.url, "salary": a.salary,
           "created": now(), "stage": "found", "guard": {k: guard[k] for k in ("verdict", "warn", "instruction_lines", "invisible_text", "mixed_script_words")},
           "top_terms": sorted(engine.jd_terms(jd).items(), key=lambda kv: -kv[1])}
    job["top_terms"] = [k for k, _ in job["top_terms"]][:20]
    print(f"[1/3] safety: {guard['verdict']}")
    for i in guard["instruction_lines"]:
        print(f"      ! [{i['where']}] {i['line']}")

    if guard["warn"] and not a.force:
        job["stage"] = "found"; job["notes"] = "paused: posting contains text aimed at an AI agent"
        save_job(app, job); write_report(app, job)
        print(f"      paused – read {app}/report.md. If the job looks genuine, rerun with --force.")
        return 3

    f = fit.check(jd, a.title, a.location, a.salary, fit.load_prefs())
    job["fit"] = f
    print(f"[2/3] fit: {f['verdict']} ({f['score']}/100)" + "".join(f"\n      x {r}" for r in f["reasons"]) + "".join(f"\n      ~ {r}" for r in f["flags"]))
    if f["verdict"] == "SKIP" and not a.force:
        job["stage"] = "skipped"; job["notes"] = "fit: " + "; ".join(f["reasons"])
        save_job(app, job); write_report(app, job)
        print(f"      skipped (use --force to tailor anyway). Report: {app}/report.md")
        return 4

    r, res, hist, na = engine.tailor_loop(jd, a.title, target=a.target)
    r = engine.render_fit(r, os.path.join(app, "resume.pdf"))
    json.dump(r, open(os.path.join(app, "resume.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    job.update(stage="tailored", ats={"score": res["score"], "history": hist, "parts": res["parts"],
               "still_missing": [g["k"] for g in res["gaps"]], "checks": res["checks"], "needs_confirmation": na})
    save_job(app, job); write_report(app, job)
    verdict = "ready to apply" if res["score"] >= a.target else f"below {a.target} – do a rewrite pass (edit resume.json, then rescore)"
    print(f"[3/3] ATS: {' -> '.join(str(h) for h in hist)}  ({verdict})")
    print(f"      {app}/resume.pdf\n      {app}/report.md")
    return 0 if res["score"] >= a.target else 5


def posting_meta(path, text):
    """Company / title / location / salary from 'Company:'-style lines at the top, else from the file name
    ('Acme__Data Analyst.txt' or 'Acme - Data Analyst.txt'), else the first line."""
    meta = {}
    for line in text.splitlines()[:15]:
        m = re.match(r"\s*(company|employer|title|role|position|location|salary|ctc|url|link)\s*:\s*(.+)", line, re.I)
        if m:
            k = {"employer": "company", "role": "title", "position": "title", "ctc": "salary", "link": "url"}.get(m.group(1).lower(), m.group(1).lower())
            meta.setdefault(k, m.group(2).strip())
    stem = os.path.splitext(os.path.basename(path))[0]
    parts = re.split(r"__| - ", stem, maxsplit=1)
    if len(parts) == 2:
        meta.setdefault("company", parts[0].strip()); meta.setdefault("title", parts[1].strip())
    first = next((l.strip() for l in text.splitlines() if l.strip()), stem)
    meta.setdefault("company", stem if len(parts) < 2 else parts[0])
    meta.setdefault("title", first[:80])
    return meta


def cmd_rank(a):
    os.environ["JOBPILOT_PROFILE"] = a.profile
    import posting_guard, fit, engine
    prefs = fit.load_prefs()
    files = sorted(f for f in os.listdir(a.folder) if f.lower().endswith((".txt", ".html", ".htm", ".md")) and not f.startswith("ranked"))
    if not files:
        print(f"no .txt / .html / .md postings in {a.folder}"); return 1
    rows = []
    for i, f in enumerate(files, 1):
        path = os.path.join(a.folder, f)
        raw = open(path, encoding="utf-8", errors="replace").read()
        jd, g = posting_guard.guard(raw)
        m = posting_meta(path, jd)
        row = {"file": f, "company": m["company"], "title": m["title"], "location": m.get("location", ""),
               "salary": m.get("salary", ""), "url": m.get("url", ""), "ats": "", "fit": "", "fit_score": 0, "why": ""}
        print(f"[{i}/{len(files)}] {m['company']} – {m['title']}", flush=True)
        if g["warn"]:
            row.update(fit="PAUSED", why="safety: text aimed at an AI agent – read it before applying")
        else:
            fr = fit.check(jd, m["title"], m.get("location", ""), m.get("salary", ""), prefs)
            row.update(fit=fr["verdict"], fit_score=fr["score"], why="; ".join(fr["reasons"] + fr["flags"]))
            if fr["verdict"] != "SKIP":
                try:
                    res = engine.ats(engine.tailor(jd, m["title"]), jd, m["title"])
                    row["ats"] = res["score"]
                    miss = [x["k"] for x in res["gaps"]][:5]
                    if miss:
                        row["why"] = (row["why"] + "; " if row["why"] else "") + "missing: " + ", ".join(miss)
                except Exception as e:  # keep ranking the rest
                    row["why"] += f"; ATS failed: {e}"
        rows.append(row)
    order = {"GO": 0, "STRETCH": 1, "PAUSED": 2, "SKIP": 3}
    rows.sort(key=lambda r: (order.get(r["fit"], 4), -(r["ats"] or 0), -r["fit_score"]))
    print(f"\n{'#':>2}  {'fit':<8}{'ATS':>5}  {'company':<22}{'title':<34}why")
    for n, r in enumerate(rows, 1):
        print(f"{n:>2}  {r['fit']:<8}{str(r['ats']):>5}  {r['company'][:21]:<22}{r['title'][:33]:<34}{r['why'][:70]}")
    md = ["# Ranked postings", "", f"{len(rows)} postings, ranked by fit then quick ATS score (before the rewrite pass).", "",
          "| # | Fit | ATS | Company | Title | Notes | File |", "|---|---|---|---|---|---|---|"]
    md += [f"| {n} | {r['fit']} | {r['ats']} | {r['company']} | {r['title']} | {r['why']} | {r['file']} |" for n, r in enumerate(rows, 1)]
    top = [r for r in rows if r["fit"] in ("GO", "STRETCH")][:a.top]
    if top:
        md += ["", "## Next", ""] + [f'- `python jobpilot.py new "{os.path.join(a.folder, r["file"])}" --company "{r["company"]}" --title "{r["title"]}"'
                                     + (f' --location "{r["location"]}"' if r["location"] else "") + "`" for r in top]
    open(os.path.join(a.folder, "ranked.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    with open(os.path.join(a.folder, "ranked.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "company", "title", "location", "salary", "url", "fit", "fit_score", "ats", "why"])
        w.writeheader(); w.writerows(rows)
    print(f"\nShortlist: {len(top)} worth tailoring. Saved {os.path.join(a.folder, 'ranked.md')} (+ ranked.csv) with the next commands.")
    return 0


def cmd_rescore(a):
    os.environ["JOBPILOT_PROFILE"] = a.profile
    import engine
    job = load_job(a.app)
    jd = open(os.path.join(a.app, "jd.txt"), encoding="utf-8").read()
    r = json.load(open(os.path.join(a.app, "resume.json"), encoding="utf-8"))
    res = engine.ats(r, jd, job["title"])
    r = engine.render_fit(r, os.path.join(a.app, "resume.pdf"))
    json.dump(r, open(os.path.join(a.app, "resume.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    ats = job.setdefault("ats", {"history": []})
    ats.update(score=res["score"], parts=res["parts"], still_missing=[g["k"] for g in res["gaps"]], checks=res["checks"])
    ats.setdefault("history", []).append(res["score"])
    job["rewrite_rounds"] = job.get("rewrite_rounds", 0) + 1
    save_job(a.app, job); write_report(a.app, job)
    print(f"ATS {res['score']} (history {ats['history']}); still missing: {', '.join(ats['still_missing'][:10]) or 'nothing'}")
    return 0 if res["score"] >= a.target else 5


def cmd_cover(a):
    os.environ["JOBPILOT_PROFILE"] = a.profile
    import cover_letter
    if a.render:
        p = cover_letter.render(a.app)
        if p:
            print("wrote", p)
        return 0 if p else 1
    if os.path.exists(os.path.join(a.app, "cover.md")):
        _, probs = cover_letter.check(a.app)
        print("cover.md exists. " + ("Fact check OK – run with --render" if not probs else "Fix:\n" + "\n".join("  x " + p for p in probs)))
        return 0 if not probs else 1
    print("wrote", cover_letter.draft(a.app), "– fill in the [brackets], then: jobpilot.py cover", a.app, "--render")
    return 0


def cmd_kit(a):
    job = load_job(a.app)
    pp = os.path.join(a.profile, "preferences.json")
    prefs = json.load(open(pp, encoding="utf-8")) if os.path.exists(pp) else {}
    bp = os.path.join(a.profile, "base_resume.json")
    base = json.load(open(bp, encoding="utf-8")) if os.path.exists(bp) else {}
    plain = lambda x: re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\2", str(x)).replace("mailto:", "").replace("**", "")
    contact = [plain(c).strip() for c in base.get("contact", "").split("|")]
    files = [f for f in ("resume.pdf", "cover.pdf") if os.path.exists(os.path.join(a.app, f))]
    ats = job.get("ats", {})
    L = [f"# Application kit – {job['title']}, {job['company']}", "",
         f"**Apply here:** {job.get('url') or '(link not saved – search the company careers page)'}",
         f"**Attach:** " + ", ".join(f"`{os.path.join(a.app, f)}`" for f in files),
         f"**ATS score:** {ats.get('score', '?')}" + (f" (missing: {', '.join(ats.get('still_missing', [])[:6])})" if ats.get("still_missing") else ""),
         "", "## Copy-paste answers", "", f"- **Name:** {base.get('name', '')}"]
    for c in contact:
        key = "Email" if "@" in c else "LinkedIn" if "linkedin" in c.lower() else "Phone" if re.search(r"\d{6,}", c.replace(" ", "")) else \
              "Website" if re.search(r"https?://|\.\w{2,}/|github|\.io", c) else "Location"
        if c: L.append(f"- **{key}:** {c}")
    labels = {"notice_period": "Notice period", "current_ctc": "Current / last salary", "expected_ctc": "Expected salary",
              "work_authorization": "Work authorisation", "relocation": "Relocation"}
    for k, lab in labels.items():
        if prefs.get(k): L.append(f"- **{lab}:** {prefs[k]}")
    L.append(f"- **Years of experience:** {base.get('years_experience', '')}")
    exp = base.get("experience", [])
    if exp:
        L.append(f"- **Current / last role:** {exp[0].get('title', '')}, {exp[0].get('company', '')} ({exp[0].get('dates', '')})")
    if base.get("education"):
        e = base["education"][0]; L.append(f"- **Highest education:** {e.get('degree', '')}, {e.get('school', '')} ({e.get('dates', '')})")
    L += ["", "## Short answers you may be asked", "",
          f"- **Why this role?** Write 2 sentences from the posting + your matching work (ask Claude: \"why-this-role answer for {job['company']}\").",
          "- **Anything not listed above:** answer truthfully; if unsure, ask Claude before you submit.", "",
          f"_After you submit: `python jobpilot.py stage {a.app} applied`_"]
    out = os.path.join(a.app, "application_kit.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L)); print(f"\nsaved {out}")
    return 0


def cmd_prep(a):
    job = load_job(a.app)
    r = json.load(open(os.path.join(a.app, "resume.json"), encoding="utf-8"))
    jd = open(os.path.join(a.app, "jd.txt"), encoding="utf-8").read()
    plain = lambda s: re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s).replace("**", "")
    bullets = [(e["company"], plain(b)) for e in r.get("experience", []) for b in e.get("bullets", [])]
    reqs = [l.strip(" -•*\t") for l in jd.splitlines() if 25 < len(l.strip()) < 220 and
            re.search(r"\b(experience|ability|proficien|knowledge|skill|manage|build|analy|own|work with|responsib)", l, re.I)][:10]
    def best(req):
        words = {w for w in re.findall(r"[a-z]{4,}", req.lower())}
        scored = sorted(bullets, key=lambda cb: -len(words & set(re.findall(r"[a-z]{4,}", cb[1].lower()))))
        return scored[0] if scored and words & set(re.findall(r"[a-z]{4,}", scored[0][1].lower())) else None
    out = [f"# Interview prep – {job['title']}, {job['company']}", "",
           "Everything below comes from your resume. Practise saying each story out loud in under 2 minutes.", "",
           "## What they asked for → your proof", ""]
    for q in reqs:
        b = best(q)
        out += [f"**{q}**", f"- Your story: {b[1]} ({b[0]})" if b else "- No direct proof in your resume – be honest, show how you'd learn it fast.",
                "- STAR: Situation … Task … Action … Result (use the real numbers)", ""]
    missing = job.get("ats", {}).get("still_missing", [])
    if missing:
        out += ["## Gaps to prepare an honest answer for", ""] + [f"- {m}" for m in missing[:8]] + [""]
    out += ["## Likely questions", "", f"- Walk me through your resume and why {job['company']}.",
            f"- Why are you leaving / why now?", "- Tell me about a time you used data to change a decision.",
            "- Tell me about a disagreement with a stakeholder.", "- What would you do in your first 90 days?", "",
            "## Ask them", "", "- What does success look like in the first 6 months?",
            "- What are the team's biggest data/process pain points today?", "- How is the team structured, and who would I work with most?", "",
            "_After the interview: run `jobpilot.py stage <app> interview` and note what they asked in job.json → notes._"]
    p = os.path.join(a.app, "interview_prep.md")
    open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("wrote", p)
    return 0


def cmd_stage(a):
    if a.stage not in STAGES:
        sys.exit("stage must be one of: " + ", ".join(STAGES))
    job = load_job(a.app)
    job.setdefault("history", []).append({"at": now(), "from": job.get("stage"), "to": a.stage})
    job["stage"] = a.stage
    if a.note:
        job["notes"] = (job.get("notes", "") + " | " + a.note).strip(" |")
    save_job(a.app, job)
    print(f"{job['company']} – {job['title']}: {a.stage}")
    return 0


PACK_ROOTS = ("profile", "apps")


def cmd_pack(a):
    import zipfile
    out = os.path.abspath(a.out or "jobautopilot-pack.zip")
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root_name, root in (("profile", a.profile), ("apps", a.apps)):
            if not os.path.isdir(root):
                continue
            for dirpath, _, files in os.walk(root):
                for f in files:
                    full = os.path.join(dirpath, f)
                    rel = os.path.relpath(full, root).replace(os.sep, "/")
                    z.write(full, f"{root_name}/{rel}"); n += 1
        z.writestr("PACK_README.txt", "Job Autopilot pack. Attach this file in a new chat and say 'continue job autopilot',\n"
                   "or run: python jobpilot.py unpack <this file>. It holds personal data - keep it private.\n")
    if not n:
        print("nothing to pack yet (no profile/ or apps/)"); os.remove(out); return 1
    print(f"packed {n} files -> {out}")
    return 0


def cmd_unpack(a):
    import zipfile
    dest = {"profile": a.profile, "apps": a.apps}
    n, skipped = 0, []
    with zipfile.ZipFile(a.pack) as z:
        for info in z.infolist():
            name = info.filename.replace("\\", "/")
            parts = [p for p in name.split("/") if p not in ("", ".")]
            if info.is_dir() or name == "PACK_README.txt":
                continue
            if not parts or parts[0] not in PACK_ROOTS or ".." in parts or ":" in name or name.startswith("/") or len(parts) < 2:
                skipped.append(name); continue  # only profile/ and apps/ files, never paths that climb out
            target = os.path.join(dest[parts[0]], *parts[1:])
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(info) as src, open(target, "wb") as fh:
                fh.write(src.read(50_000_000))
            n += 1
    print(f"restored {n} files into {a.profile} and {a.apps}" + (f"; ignored {len(skipped)} unexpected entries" if skipped else ""))
    return 0 if n else 1


def cmd_list(a):
    rows = []
    if os.path.isdir(a.apps):
        for d in sorted(os.listdir(a.apps)):
            p = os.path.join(a.apps, d, "job.json")
            if os.path.exists(p):
                j = json.load(open(p, encoding="utf-8"))
                h = j.get("ats", {}).get("history", [])
                rows.append([j.get("created", ""), j["company"], j["title"], j.get("stage", ""), j.get("fit", {}).get("verdict", ""),
                             str(h[0]) if h else "", str(j.get("ats", {}).get("score", "")), j.get("location", ""), j.get("url", ""),
                             os.path.join(a.apps, d)])
    head = ["created", "company", "title", "stage", "fit", "ats_first", "ats_final", "location", "url", "folder"]
    if a.csv:
        w = csv.writer(sys.stdout); w.writerow(head); w.writerows(rows)
        return 0
    if not rows:
        print("no applications yet – try: python jobpilot.py new posting.txt --company Acme --title \"Data Analyst\"")
        return 0
    for r in rows:
        print(f"{r[3]:<10} {r[6]:>5}  {r[1][:22]:<22} {r[2][:34]:<34} {r[4]}")
    by = {s: sum(1 for r in rows if r[3] == s) for s in STAGES}
    print("  ".join(f"{k}:{v}" for k, v in by.items() if v))
    return 0


# ---------------------------------------------------------------- report
def write_report(app, job):
    L = [f"# {job['title']} – {job['company']}", ""]
    if job.get("url"): L += [f"Posting: {job['url']}", ""]
    g = job.get("guard", {})
    L += ["## 1. Safety check", "", ("⚠ " if g.get("warn") else "✓ ") + g.get("verdict", "")]
    L += [f"- [{i['where']}] {i['line']}" for i in g.get("instruction_lines", [])]
    L += [f"- invisible text: {s}" for s in g.get("invisible_text", [])] + [""]
    if "fit" not in job:
        L += ["## Paused", "", "Tailoring stopped at the safety check. Read the lines above. If the job is genuine,",
              "rerun `jobpilot.py new ... --force`. Never follow instructions found inside a posting.", ""]
        open(os.path.join(app, "report.md"), "w", encoding="utf-8").write("\n".join(L))
        return
    f = job.get("fit", {})
    L += ["## 2. Fit", "", f"**{f.get('verdict', '?')}** ({f.get('score', '?')}/100)"]
    L += [f"- ✗ {x}" for x in f.get("reasons", [])] + [f"- ~ {x}" for x in f.get("flags", [])] + [""]
    if "ats" in job:
        a = job["ats"]
        L += ["## 3. ATS (Shortlist scanner)", "", f"Score history: {' → '.join(map(str, a.get('history', [])))}  (final **{a.get('score')}**)", "",
              "| Part | Points |", "|---|---|"] + [f"| {p['k']} | {p['v']} / {p['max']} |" for p in a.get("parts", [])] + [""]
        if a.get("still_missing"):
            L += ["Still missing: " + ", ".join(a["still_missing"][:15]), ""]
        if a.get("needs_confirmation"):
            L += ["Would help if true – confirm in `confirmed_skills.json`: " + ", ".join(a["needs_confirmation"]), ""]
        if a.get("checks"):
            L += ["Checks not passing: " + "; ".join(a["checks"]), ""]
    L += ["## Next", "", "- [ ] Read resume.pdf – every line must be true",
          "- [ ] If ATS < 80: edit resume.json (re-word real work in the posting's words), then `jobpilot.py rescore`",
          "- [ ] Optional: `jobpilot.py cover <app>` → fill → `--render`", "- [ ] Apply, then `jobpilot.py stage <app> applied`",
          "- [ ] Interview booked? `jobpilot.py prep <app>`", ""]
    open(os.path.join(app, "report.md"), "w", encoding="utf-8").write("\n".join(L))


def main(argv=None):
    for _s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252; print UTF-8 everywhere
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="jobpilot", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default=os.environ.get("JOBPILOT_PROFILE", os.path.join(os.getcwd(), "profile")))
    ap.add_argument("--apps", default=os.path.join(os.getcwd(), "apps"))
    ap.add_argument("--target", type=float, default=80)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("init"); sp.add_parser("doctor")
    im = sp.add_parser("import"); im.add_argument("resume"); im.add_argument("--force", action="store_true")
    n = sp.add_parser("new"); n.add_argument("posting"); n.add_argument("--company", required=True); n.add_argument("--title", required=True)
    n.add_argument("--location", default=""); n.add_argument("--salary", default=""); n.add_argument("--url", default=""); n.add_argument("--force", action="store_true")
    rk = sp.add_parser("rank"); rk.add_argument("folder"); rk.add_argument("--top", type=int, default=10)
    for c in ("rescore", "prep", "kit"):
        sp.add_parser(c).add_argument("app")
    c = sp.add_parser("cover"); c.add_argument("app"); c.add_argument("--render", action="store_true")
    s = sp.add_parser("stage"); s.add_argument("app"); s.add_argument("stage"); s.add_argument("--note", default="")
    l = sp.add_parser("list"); l.add_argument("--csv", action="store_true")
    pk = sp.add_parser("pack"); pk.add_argument("--out", default="")
    up = sp.add_parser("unpack"); up.add_argument("pack")
    a = ap.parse_args(argv)
    a.profile = os.path.abspath(a.profile); a.apps = os.path.abspath(a.apps)
    return {"init": cmd_init, "import": cmd_import, "doctor": cmd_doctor, "new": cmd_new, "rank": cmd_rank, "rescore": cmd_rescore, "cover": cmd_cover,
            "prep": cmd_prep, "kit": cmd_kit, "stage": cmd_stage, "list": cmd_list,
            "pack": cmd_pack, "unpack": cmd_unpack}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
