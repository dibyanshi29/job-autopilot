#!/usr/bin/env python3
"""jobpilot – honest, ATS-checked job applications from one command.

  python jobpilot.py init                       create ./profile from the templates
  python jobpilot.py doctor                     check Python, Node, fonts
  python jobpilot.py new <posting> --company "Acme" --title "Data Analyst" [--location ..] [--salary ..] [--url ..]
                                                safety check -> fit check -> tailor + ATS loop -> apps/<acme-data-analyst>/
  python jobpilot.py rescore <app>              re-render + re-score after you edit <app>/resume.json
  python jobpilot.py cover <app> [--render]     draft cover.md, then --render to fact-check and build cover.pdf
  python jobpilot.py prep <app>                 interview prep sheet mapping the posting to your real experience
  python jobpilot.py stage <app> <stage>        found | tailored | applied | interview | offer | rejected | skipped
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
    gi = os.path.join(os.path.dirname(os.path.abspath(a.profile)), ".gitignore")
    print(f"""
Next:
  1. Fill {a.profile}/base_resume.json from your resume (or ask Claude: "set up job autopilot from my resume").
  2. Set roles, cities, salary floor and deal-breakers in {a.profile}/preferences.json.
  3. python jobpilot.py doctor
  4. python jobpilot.py new posting.txt --company "Acme" --title "Data Analyst"
Your profile holds personal data – keep it out of any public repo (it is in .gitignore here).""")
    return 0


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
    n = sp.add_parser("new"); n.add_argument("posting"); n.add_argument("--company", required=True); n.add_argument("--title", required=True)
    n.add_argument("--location", default=""); n.add_argument("--salary", default=""); n.add_argument("--url", default=""); n.add_argument("--force", action="store_true")
    for c in ("rescore", "prep"):
        sp.add_parser(c).add_argument("app")
    c = sp.add_parser("cover"); c.add_argument("app"); c.add_argument("--render", action="store_true")
    s = sp.add_parser("stage"); s.add_argument("app"); s.add_argument("stage"); s.add_argument("--note", default="")
    l = sp.add_parser("list"); l.add_argument("--csv", action="store_true")
    a = ap.parse_args(argv)
    a.profile = os.path.abspath(a.profile); a.apps = os.path.abspath(a.apps)
    return {"init": cmd_init, "doctor": cmd_doctor, "new": cmd_new, "rescore": cmd_rescore, "cover": cmd_cover,
            "prep": cmd_prep, "stage": cmd_stage, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
