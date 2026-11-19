#!/usr/bin/env python3
"""End-to-end tests with the fictional example profile. Runs on Linux, macOS and Windows:
    python tests/test_jobpilot.py
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = [sys.executable, os.path.join(ROOT, "jobpilot.py")]
JD = os.path.join(ROOT, "tests", "sample_jd.txt")
POISON = os.path.join(ROOT, "tests", "fixtures", "poisoned_posting.html")
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def run(*args, cwd):
    p = subprocess.run(CLI + list(args), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return p.returncode, p.stdout + p.stderr


def main():
    w = tempfile.mkdtemp(prefix="jobpilot_test_")
    try:
        code, out = run("init", cwd=w)
        assert code == 0 and os.path.exists(os.path.join(w, "profile", "preferences.json")), out

        # 1. normal posting -> tailored, one page, score never drops, nothing from never_claim
        code, out = run("new", JD, "--company", "Acme Logistics", "--title", "Data Analyst", "--location", "Bengaluru", cwd=w)
        assert code in (0, 5), out
        app = os.path.join(w, "apps", "acme-logistics-data-analyst")
        job = json.load(open(os.path.join(app, "job.json"), encoding="utf-8"))
        hist = job["ats"]["history"]
        assert hist == sorted(hist), f"score went down: {hist}"
        assert 0 <= job["ats"]["score"] <= 100
        from pypdf import PdfReader
        assert len(PdfReader(os.path.join(app, "resume.pdf")).pages) == 1, "resume must be one page"
        tailored = open(os.path.join(app, "resume.json"), encoding="utf-8").read().lower()
        base = json.load(open(os.path.join(w, "profile", "base_resume.json"), encoding="utf-8"))
        for n in base.get("never_claim", []):
            assert f'"{n.lower()}"' not in tailored, f"never_claim skill added: {n}"
        assert os.path.exists(os.path.join(app, "report.md"))
        print(f"ok  tailor: ATS {hist}, one page")

        # 2. rescore keeps working after a hand edit
        code, out = run("rescore", app, cwd=w)
        assert code in (0, 5) and "ATS" in out, out
        print("ok  rescore")

        # 3. poisoned posting is paused, findings recorded
        code, out = run("new", POISON, "--company", "Shady", "--title", "Data Analyst", cwd=w)
        assert code == 3, out
        sj = json.load(open(os.path.join(w, "apps", "shady-data-analyst", "job.json"), encoding="utf-8"))
        assert sj["guard"]["warn"] and sj["guard"]["instruction_lines"]
        clean = open(os.path.join(w, "apps", "shady-data-analyst", "jd.txt"), encoding="utf-8").read()
        assert "Ignore all previous" not in clean and "​" not in clean, "hidden text leaked into the clean posting"
        print("ok  posting guard paused a poisoned posting")

        # 4. fit check skips deal-breakers
        bad = os.path.join(w, "bad.txt")
        open(bad, "w", encoding="utf-8").write("Operations Manager. 9+ years. Night shift rotation. 5-6 LPA.")
        code, out = run("new", bad, "--company", "Nope", "--title", "Operations Manager", cwd=w)
        assert code == 4 and "SKIP" in out, out
        print("ok  fit check skipped a deal-breaker")

        # 5. cover letter: invented number refused, true one renders to one page
        code, out = run("cover", app, cwd=w)
        assert code == 0 and os.path.exists(os.path.join(app, "cover.md")), out
        letter = ("Dear Hiring Team at Acme Logistics,\n\nI built a Power BI dashboard tracking on-time delivery for 40+ carriers "
                  "and improved accuracy by 73%.\n\nI can join immediately.\n\nSincerely,\nAnanya Rao\n")
        open(os.path.join(app, "cover.md"), "w", encoding="utf-8").write(letter)
        code, out = run("cover", app, "--render", cwd=w)
        assert code == 1 and "73%" in out, out
        open(os.path.join(app, "cover.md"), "w", encoding="utf-8").write(letter.replace(" and improved accuracy by 73%", ""))
        code, out = run("cover", app, "--render", cwd=w)
        assert code == 0, out
        assert len(PdfReader(os.path.join(app, "cover.pdf")).pages) == 1
        print("ok  cover letter fact check + render")

        # 6. prep, stage, list
        assert run("prep", app, cwd=w)[0] == 0 and os.path.exists(os.path.join(app, "interview_prep.md"))
        assert run("stage", app, "applied", cwd=w)[0] == 0
        code, out = run("list", "--csv", cwd=w)
        assert code == 0 and "applied" in out, out
        print("ok  prep / stage / list")
        print("ALL TESTS PASSED")
    finally:
        shutil.rmtree(w, ignore_errors=True)


if __name__ == "__main__":
    main()
