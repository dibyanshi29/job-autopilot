#!/usr/bin/env python3
"""Job boards: pull fresh postings straight from company hiring systems, and check whether a posting is still open.

  scan  Greenhouse, Lever and Ashby publish each company's open jobs as public JSON meant for job boards – no
        sign-in, no scraping, no captchas. scan() reads profile/boards.json, keeps jobs whose title and location
        match preferences.json, skips jobs already seen or already in apps/, and saves each one as HTML in
        postings/ (header lines Company:/Title:/Location:/URL: on top) ready for `jobpilot.py rank`. The raw HTML
        is kept so the posting guard still sees hidden text.

  live  check_live() says whether a posting link still takes applications: LIVE, CLOSED, LIKELY_CLOSED (the link
        now redirects away from the job) or UNKNOWN (could not tell). Greenhouse, Lever and Ashby links are checked
        against the hiring system's own feed; other links by loading the page.

Every network call goes through one `get(url) -> (status, final_url, text)` function, so tests pass a fake one.
Nothing about the user is sent anywhere – only public job pages are read.
"""
import datetime, html, json, os, re, urllib.error, urllib.parse, urllib.request

UA = "job-autopilot/1.0 (+https://github.com/dibyanshi29/job-autopilot)"


class BoardError(Exception):
    pass


def http_get(url, timeout=15):
    """(status, final_url, text). HTTP errors -> (code, url, ''); network errors -> (0, url, message)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/html;q=0.9, */*;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.geturl(), r.read(8_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, url, ""
    except Exception as e:  # DNS, timeout, TLS, blocked sandbox …
        return 0, url, str(e) or e.__class__.__name__


def _ts(v):
    """ISO-8601 string or epoch milliseconds -> timezone-aware datetime, else None."""
    if v in (None, ""):
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.datetime.fromtimestamp(v / 1000, datetime.timezone.utc)
        s = re.sub(r"(T\d\d:\d\d:\d\d)\.\d+", r"\1", str(v).strip()).replace("Z", "+00:00")
        d = datetime.datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def _json(get, url, what):
    st, _, body = get(url)
    if st == 404:
        raise BoardError(f"{what} not found – check the slug or careers link in boards.json")
    if st != 200:
        raise BoardError(f"{what}: could not load ({'HTTP ' + str(st) if st else body[:100]})")
    try:
        return json.loads(body)
    except ValueError:
        raise BoardError(f"{what}: unexpected reply (not JSON)")


# ---------------------------------------------------------------- the three public job-board feeds
def greenhouse(slug, company, get):
    data = _json(get, f"https://boards-api.greenhouse.io/v1/boards/{urllib.parse.quote(slug)}/jobs?content=true",
                 f"Greenhouse board '{slug}'")
    for j in data.get("jobs", []):
        yield {"company": company, "title": (j.get("title") or "").strip(),
               "location": ((j.get("location") or {}).get("name") or "").strip(),
               "url": j.get("absolute_url") or "", "salary": "",
               "html": html.unescape(j.get("content") or ""),  # Greenhouse sends the HTML entity-escaped
               "posted": _ts(j.get("first_published") or j.get("updated_at"))}


def lever(slug, company, get):
    data = _json(get, f"https://api.lever.co/v0/postings/{urllib.parse.quote(slug)}?mode=json", f"Lever board '{slug}'")
    for j in data if isinstance(data, list) else []:
        cat = j.get("categories") or {}
        loc = (cat.get("location") or "").strip()
        if (j.get("workplaceType") or "").lower() == "remote" and "remote" not in loc.lower():
            loc = f"{loc} (Remote)".strip()
        parts = [j.get("description") or ""]
        for l in j.get("lists") or []:
            parts.append(f"<h3>{html.escape(l.get('text') or '')}</h3><ul>{l.get('content') or ''}</ul>")
        parts.append(j.get("additional") or "")
        sr = j.get("salaryRange") or {}
        salary = (f"{sr.get('currency', '')} {sr.get('min')}-{sr.get('max')} {(sr.get('interval') or '').replace('-', ' ')}".strip()
                  if sr.get("min") and sr.get("max") else "")
        yield {"company": company, "title": (j.get("text") or "").strip(), "location": loc,
               "url": j.get("hostedUrl") or j.get("applyUrl") or "", "salary": salary,
               "html": "\n".join(p for p in parts if p), "posted": _ts(j.get("createdAt"))}


def ashby(slug, company, get):
    data = _json(get, f"https://api.ashbyhq.com/posting-api/job-board/{urllib.parse.quote(slug)}?includeCompensation=true",
                 f"Ashby board '{slug}'")
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        loc = (j.get("location") or "").strip()
        if j.get("isRemote") and "remote" not in loc.lower():
            loc = f"{loc} (Remote)".strip()
        comp = j.get("compensation") or {}
        yield {"company": company, "title": (j.get("title") or "").strip(), "location": loc,
               "url": j.get("jobUrl") or j.get("applyUrl") or "",
               "salary": comp.get("compensationTierSummary") or comp.get("scrapeableCompensationSalarySummary") or "",
               "html": j.get("descriptionHtml") or html.escape(j.get("descriptionPlain") or ""),
               "posted": _ts(j.get("publishedAt") or j.get("publishedDate"))}


FETCHERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}
BOARD_URL = [
    ("greenhouse", re.compile(r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board\?for=)?([\w-]+)", re.I)),
    ("lever", re.compile(r"jobs\.lever\.co/([\w.-]+)", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([\w.%-]+)", re.I)),
]


def parse_board_url(url):
    """'https://jobs.lever.co/acme' -> ('lever', 'acme'); None when it isn't one of the three."""
    for ats, rx in BOARD_URL:
        m = rx.search(url or "")
        if m and m.group(1).lower() not in ("embed", "v1"):
            return ats, m.group(1)
    return None


def board_entries(cfg):
    """Each boards.json entry -> (ats, slug, company). Entries may be {"ats", "slug", "company"}, {"url", "company"} or a URL."""
    for b in cfg.get("boards", []):
        if isinstance(b, str):
            b = {"url": b}
        if not isinstance(b, dict) or b.get("skip"):
            continue
        ats, slug = (b.get("ats") or "").lower().strip(), (b.get("slug") or "").strip()
        if not (ats and slug) and b.get("url"):
            ats, slug = parse_board_url(b["url"]) or ("", "")
        yield ats, slug, (b.get("company") or slug.replace("-", " ").title() or "?").strip()


# ---------------------------------------------------------------- filtering + saving
def matches(job, prefs):
    """Cheap title/location pre-filter before rank's full fit check. Returns '' to keep, else the reason to skip."""
    t = job["title"].lower()
    if not t:
        return "no title"
    if any(a.lower() in t for a in prefs.get("avoid_titles", [])):
        return "title on your avoid list"
    titles = [x.lower() for x in prefs.get("target_titles", [])]
    if titles and not any(x in t for x in titles):
        words = {w for x in titles for w in x.split() if len(w) > 3}
        if not words & set(re.findall(r"[a-z]+", t)):
            return "title outside your target roles"
    loc = job["location"].lower()
    locs = [c.lower() for c in prefs.get("locations", [])]
    cities = [c for c in locs if c != "remote"]
    remote = bool(re.search(r"\bremote\b|\banywhere\b|work from home|\bwfh\b", loc))
    if remote:
        return "" if prefs.get("remote_ok", True) else "remote, and you want on-site"
    if locs and not cities:
        return "not remote" if loc else ""
    if cities and loc and not any(c in loc for c in cities):
        return "location not in your list"
    return ""


def _safe(s):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', " ", s)
    return re.sub(r"\s+", " ", s).strip(" .")[:70] or "job"


def save_posting(job, folder):
    base = f"{_safe(job['company'])}__{_safe(job['title'])}"
    path, n = os.path.join(folder, base + ".html"), 2
    while os.path.exists(path):
        path, n = os.path.join(folder, f"{base} ({n}).html"), n + 1
    head = [("Company", job["company"]), ("Title", job["title"]), ("Location", job["location"]),
            ("Salary", job.get("salary", "")), ("URL", job["url"]),
            ("Posted", job["posted"].strftime("%Y-%m-%d") if job.get("posted") else "")]
    top = "".join(f"<p>{k}: {html.escape(str(v))}</p>\n" for k, v in head if v)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"<html><body>\n{top}<hr>\n{job['html']}\n</body></html>\n")
    return path


def scan(cfg, prefs, folder, applied=(), slugger=None, get=http_get, max_age_days=None, now=None):
    """Fetch every board in cfg, filter, save new postings into folder. Returns (report rows, saved paths)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    max_age = cfg.get("max_age_days", 30) if max_age_days is None else max_age_days
    os.makedirs(folder, exist_ok=True)
    seen_path = os.path.join(folder, ".seen.json")
    seen = json.load(open(seen_path, encoding="utf-8")) if os.path.exists(seen_path) else {}
    applied = set(applied)
    report, saved = [], []
    for ats, slug, company in board_entries(cfg):
        row = {"company": company, "board": f"{ats or '?'}:{slug or '?'}", "found": 0, "kept": 0, "skipped": {}, "error": ""}
        report.append(row)
        if ats not in FETCHERS or not slug:
            row["error"] = "not a Greenhouse / Lever / Ashby board – give ats + slug, or the careers link"
            continue
        try:
            jobs = list(FETCHERS[ats](slug, company, get))
        except BoardError as e:
            row["error"] = str(e)
            continue
        row["found"] = len(jobs)
        for j in jobs:
            if not j["url"]:
                why = "no link"
            elif j["url"] in seen:
                why = "seen in an earlier scan"
            elif slugger and slugger(j["company"], j["title"]) in applied:
                why = "already in apps/"
            else:
                why = matches(j, prefs)
                if not why and max_age and j["posted"] and (now - j["posted"]).days > max_age:
                    why = f"posted over {max_age} days ago"
            if why:
                row["skipped"][why] = row["skipped"].get(why, 0) + 1
                continue
            saved.append(save_posting(j, folder))
            seen[j["url"]] = {"first_seen": now.strftime("%Y-%m-%d"), "company": j["company"], "title": j["title"]}
            row["kept"] += 1
    with open(seen_path, "w", encoding="utf-8") as fh:
        json.dump(seen, fh, indent=1, ensure_ascii=False)
    return report, saved


# ---------------------------------------------------------------- is it still open?
CLOSED_RX = re.compile(
    r"no longer (?:accepting|available|open|active|taking)"
    r"|(?:job|position|posting|role|vacancy|opening|requisition) (?:has been|is|was) (?:closed|filled|removed|expired|taken down)"
    r"|this (?:job|position|posting|opening) (?:has )?expired"
    r"|(?:job|posting|position) not found"
    r"|applications? (?:are|is) (?:now )?closed"
    r"|not (?:currently )?accepting applications", re.I)
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def _ats_job(url):
    """API URL for a Greenhouse / Lever / Ashby job link, plus the Ashby job id (Ashby has no single-job endpoint)."""
    m = re.search(r"(?:boards|job-boards)\.greenhouse\.io/([\w-]+)/jobs/(\d+)", url, re.I)
    if m:
        return f"https://boards-api.greenhouse.io/v1/boards/{m.group(1)}/jobs/{m.group(2)}", None
    m = re.search(r"jobs\.lever\.co/([\w.-]+)/(" + UUID + ")", url, re.I)
    if m:
        return f"https://api.lever.co/v0/postings/{m.group(1)}/{m.group(2)}", None
    m = re.search(r"jobs\.ashbyhq\.com/([\w.%-]+)/(" + UUID + ")", url, re.I)
    if m:
        return f"https://api.ashbyhq.com/posting-api/job-board/{m.group(1)}", m.group(2).lower()
    return None, None


def _job_token(url):
    """The job's id in its link (a UUID or a long number), used to spot redirects to a generic careers page."""
    toks = re.findall(UUID + r"|\d{5,}", url, re.I)
    return max(toks, key=len).lower() if toks else ""


def check_live(url, get=http_get):
    if not url:
        return {"status": "UNKNOWN", "why": "no posting link saved (pass --url to new)"}
    api, ashby_id = _ats_job(url)
    if api:
        st, _, body = get(api)
        if st == 404:
            return {"status": "CLOSED", "why": "the hiring system no longer lists this job"}
        if st == 200 and ashby_id is None:
            return {"status": "LIVE", "why": "listed by the hiring system"}
        if st == 200:
            try:
                ids = {str(j.get("id", "")).lower() for j in json.loads(body).get("jobs", []) if j.get("isListed", True)}
                return ({"status": "LIVE", "why": "listed by the hiring system"} if ashby_id in ids
                        else {"status": "CLOSED", "why": "no longer on the company's Ashby board"})
            except (ValueError, AttributeError):
                pass  # fall back to loading the page
    st, final, body = get(url)
    if st in (404, 410):
        return {"status": "CLOSED", "why": f"page returns HTTP {st}"}
    if st != 200:
        return {"status": "UNKNOWN", "why": f"could not check (HTTP {st})" if st else f"could not reach the page ({body[:80]})"}
    text = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", body)
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text)))
    m = CLOSED_RX.search(text)
    if m:
        return {"status": "CLOSED", "why": f'page says "{m.group(0)}"'}
    tok = _job_token(url)
    if tok and tok not in (final or "").lower():
        return {"status": "LIKELY_CLOSED", "why": f"link now redirects away from the job, to {final}"}
    return {"status": "LIVE", "why": "page loads with no closed notice (open it to be sure – some sites build pages with JavaScript)"}
