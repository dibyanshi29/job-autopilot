#!/usr/bin/env python3
"""End-to-end tests with the fictional example profile. Runs on Linux, macOS and Windows:
    python tests/test_jobpilot.py
"""
import csv, json, os, re, shutil, subprocess, sys, tempfile

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

        # 7. import: read the generated resume PDF back into a fresh profile
        w2 = os.path.join(w, "friend")
        os.makedirs(w2)
        code, out = run("import", os.path.join(app, "resume.pdf"), cwd=w2)
        assert code == 0, out
        imp = json.load(open(os.path.join(w2, "profile", "base_resume.json"), encoding="utf-8"))
        assert imp["name"] == base["name"], imp["name"]
        assert "ananya.rao@example.com" in imp["contact"], imp["contact"]
        assert len(imp["experience"]) == len(base["experience"]), imp["experience"]
        assert all(e["bullets"] and e["dates"] for e in imp["experience"]), imp["experience"]
        assert imp["education"] and imp["skills"] and imp["evidence_map"]
        imp["name"] = "Friend Example"  # a real (non-placeholder) profile ...
        json.dump(imp, open(os.path.join(w2, "profile", "base_resume.json"), "w", encoding="utf-8"))
        code, out = run("import", os.path.join(app, "resume.pdf"), cwd=w2)  # ... must not be overwritten
        assert code == 0 and os.path.exists(os.path.join(w2, "profile", "base_resume.imported.json")), out
        code, out = run("new", JD, "--company", "Acme", "--title", "Data Analyst", cwd=w2)
        assert code in (0, 5), out
        print("ok  import resume -> working profile")

        # 8. rank a folder of postings
        pf = os.path.join(w, "postings"); os.makedirs(pf)
        shutil.copy(JD, os.path.join(pf, "Acme Logistics__Data Analyst.txt"))
        shutil.copy(POISON, os.path.join(pf, "Shady__Data Analyst.html"))
        open(os.path.join(pf, "nope.txt"), "w", encoding="utf-8").write(
            "Company: Nope Corp\nTitle: Operations Manager\nNight shift rotation. 9+ years.")
        code, out = run("rank", pf, cwd=w)
        assert code == 0, out
        with open(os.path.join(pf, "ranked.csv"), encoding="utf-8") as fh:
            ranked = list(csv.DictReader(fh))
        assert [r["company"] for r in ranked] == ["Acme Logistics", "Shady", "Nope Corp"], ranked
        assert ranked[0]["fit"] == "GO" and ranked[0]["ats"] and ranked[1]["fit"] == "PAUSED" and ranked[2]["fit"] == "SKIP"
        assert "jobpilot.py new" in open(os.path.join(pf, "ranked.md"), encoding="utf-8").read()
        print("ok  rank a folder of postings")

        # 9. pack / unpack carries everything to a fresh place; hostile zip entries are ignored
        code, out = run("pack", "--out", os.path.join(w, "pack.zip"), cwd=w)
        assert code == 0 and os.path.exists(os.path.join(w, "pack.zip")), out
        import zipfile
        with zipfile.ZipFile(os.path.join(w, "pack.zip"), "a") as z:
            z.writestr("../evil.txt", "x"); z.writestr("profile/../../evil2.txt", "x")
        w3 = os.path.join(w, "newchat"); os.makedirs(w3)
        code, out = run("unpack", os.path.join(w, "pack.zip"), cwd=w3)
        assert code == 0 and "ignored 2" in out, out
        assert not os.path.exists(os.path.join(w, "evil.txt")) and not os.path.exists(os.path.join(w, "evil2.txt"))
        assert os.path.exists(os.path.join(w3, "profile", "base_resume.json"))
        assert os.path.exists(os.path.join(w3, "apps", "acme-logistics-data-analyst", "resume.pdf"))
        code, out = run("list", cwd=w3)
        assert "Acme Logistics" in out, out
        print("ok  pack / unpack")

        # 10. application kit
        code, out = run("kit", app, cwd=w)
        assert code == 0 and "Apply here" in out and "ananya.rao@example.com" in out and "Notice period" in out, out
        assert os.path.exists(os.path.join(app, "application_kit.md"))
        print("ok  application kit")
        print("ALL TESTS PASSED")
    finally:
        shutil.rmtree(w, ignore_errors=True)


if __name__ == "__main__":
    main()
