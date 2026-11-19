#!/usr/bin/env python3
"""Fit check: should this job be tailored for at all?

Reads <profile>/preferences.json and the job description, returns GO / STRETCH / SKIP with reasons.
Run it before tailoring so time is only spent on jobs worth applying to.

Checks: deal-breakers (hard skip), role title vs target roles, years required vs your experience,
location vs your cities / remote preference, salary (when the posting states one) vs your floor,
and must-have phrases. Deal-breaker idea from ai-job-search (MIT, Mads Lorentzen).

Usage:
  python fit.py <jd.txt> --title "Job title" [--location "Bengaluru"] [--salary "12-18 LPA"] [--json]
"""
import argparse, json, os, re, sys

PROFILE_DIR = os.environ.get("JOBPILOT_PROFILE", os.path.join(os.getcwd(), "profile"))


def load_prefs():
    p = os.path.join(PROFILE_DIR, "preferences.json")
    if not os.path.exists(p):
        sys.exit(f"No preferences at {p}. Run: python jobpilot.py init")
    prefs = json.load(open(p, encoding="utf-8"))
    base = os.path.join(PROFILE_DIR, "base_resume.json")
    if os.path.exists(base):
        b = json.load(open(base, encoding="utf-8"))
        prefs.setdefault("years_experience", b.get("years_experience"))
        prefs.setdefault("target_titles", b.get("target_titles", []))
    return prefs


def years_required(jd):
    t = jd.lower()
    m = re.search(r"(\d{1,2})\s*(?:\+|plus)?\s*(?:-|–|to)\s*(\d{1,2})\s*\+?\s*(?:years|yrs)", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(?:minimum|min\.?|at least|over)?\s*(\d{1,2})\s*\+?\s*(?:years|yrs)", t)
    if m:
        return int(m.group(1)), None
    return None, None


def salary_range(text, currency):
    """Return (low, high) in the profile's unit: LPA for INR, thousands/year for others. None if not stated."""
    t = text.lower().replace(",", "")
    if currency.upper() == "INR":
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|l\b)", t)
        if m:
            return float(m.group(1)), float(m.group(2))
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?)", t)
        if m:
            return float(m.group(1)), float(m.group(1))
        m = re.search(r"(?:₹|inr|rs\.?)\s*(\d{5,8})\s*(?:-|–|to)\s*(?:₹|inr|rs\.?)?\s*(\d{5,8})", t)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            per_month = re.search(r"per month|/month|monthly|p\.m\.", t)
            mult = 12 if per_month else 1
            return lo * mult / 1e5, hi * mult / 1e5
        return None
    m = re.search(r"[$€£]\s*(\d{2,3})k?\s*(?:-|–|to)\s*[$€£]?\s*(\d{2,3})k", t) or \
        re.search(r"[$€£]\s*(\d{2,3})\s?\d{3}\s*(?:-|–|to)\s*[$€£]?\s*(\d{2,3})\s?\d{3}", t)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


def check(jd, title, location="", salary="", prefs=None):
    prefs = prefs or load_prefs()
    t, jl = title.lower(), jd.lower()
    reasons, flags, score = [], [], 100

    for d in prefs.get("deal_breakers", []):
        if re.search(r"\b" + re.escape(d.lower()) + r"\b", jl + " " + t):
            return {"verdict": "SKIP", "score": 0, "reasons": [f"deal-breaker: '{d}'"], "flags": []}

    titles = [x.lower() for x in prefs.get("target_titles", [])]
    avoid = [x.lower() for x in prefs.get("avoid_titles", [])]
    if any(a in t for a in avoid):
        return {"verdict": "SKIP", "score": 0, "reasons": [f"title is on your avoid list ({title})"], "flags": []}
    if titles and not any(x in t or t in x for x in titles):
        words = {w for x in titles for w in x.split() if len(w) > 3}
        if words & set(t.split()):
            score -= 15; flags.append("title only partly matches your target roles")
        else:
            score -= 40; reasons.append(f"title '{title}' is outside your target roles")

    yrs = float(prefs.get("years_experience") or 0)
    lo, hi = years_required(jd)
    if lo is not None:
        if lo > yrs + prefs.get("stretch_years", 1):
            score -= 45; reasons.append(f"asks for {lo}+ years; you have {yrs:g}")
        elif lo > yrs:
            score -= 15; flags.append(f"asks for {lo}+ years; you have {yrs:g} (stretch)")
        elif hi is not None and hi < yrs - 3:
            score -= 15; flags.append(f"pitched at {lo}-{hi} years; may be junior for you")

    loc = (location + " " + jl).lower()
    cities = [c.lower() for c in prefs.get("locations", [])]
    remote_ok = prefs.get("remote_ok", True)
    is_remote = bool(re.search(r"\bremote\b|work from home|\bwfh\b", loc))
    if location:
        if is_remote and remote_ok:
            pass
        elif cities and not any(c in location.lower() for c in cities):
            score -= 40; reasons.append(f"location '{location}' is not in your list")
    if prefs.get("onsite_only_skip") and re.search(r"\b(on-?site only|5 days (in|from) office)\b", jl):
        score -= 10; flags.append("fully on-site")

    sal = salary_range(salary or jd, prefs.get("currency", "INR"))
    floor = prefs.get("salary_floor")
    if sal and floor:
        if sal[1] < floor:
            score -= 50; reasons.append(f"pays up to {sal[1]:g}, below your floor {floor:g}")
        elif sal[0] < floor:
            flags.append(f"range {sal[0]:g}-{sal[1]:g} starts below your floor {floor:g}")
    elif floor:
        flags.append("salary not stated – confirm in screening")

    missing_must = [m for m in prefs.get("must_have", []) if m.lower() not in jl]
    if missing_must:
        score -= 10 * len(missing_must); flags.append("missing your must-haves: " + ", ".join(missing_must))

    score = max(0, score)
    verdict = "GO" if score >= 75 and not reasons else ("STRETCH" if score >= 50 else "SKIP")
    return {"verdict": verdict, "score": score, "reasons": reasons, "flags": flags,
            "years_required": lo, "salary_found": sal}


def main(argv=None):
    for _s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252; print UTF-8 everywhere
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Fit check before tailoring")
    ap.add_argument("jd")
    ap.add_argument("--title", required=True)
    ap.add_argument("--location", default="")
    ap.add_argument("--salary", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = check(open(a.jd, encoding="utf-8").read(), a.title, a.location, a.salary)
    if a.json:
        print(json.dumps(r, indent=1))
    else:
        print(f"fit: {r['verdict']} ({r['score']}/100)")
        for x in r["reasons"]:
            print("  x " + x)
        for x in r["flags"]:
            print("  ~ " + x)
    return {"GO": 0, "STRETCH": 0, "SKIP": 4}[r["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
