# Data Analyst – Acme Logistics

Posting: https://example.com/jobs/123

## 1. Safety check

✓ clean: nothing aimed at an agent found

## 2. Fit

**GO** (100/100)
- ~ salary not stated – confirm in screening

## 3. ATS (Shortlist scanner)

Score history: 80  (final **80**)

| Part | Points |
|---|---|
| Hard skills & keywords | 40.6 / 55 |
| Soft skills | 5 / 10 |
| Job title | 8 / 8 |
| Quantified impact | 6.7 / 7 |
| Education | 5 / 5 |
| Years of experience | 5 / 5 |
| Sections & contact | 7 / 7 |
| Action verbs & length | 2.5 / 3 |

Still missing: tableau, data pipelines, logistics, procurement, communication, leadership

Checks not passing: Hard-skill coverage 74%. 3 job keywords are missing from your resume.; 1 keyword is only a partial match: mentioned fewer times than the job asks for, or spelled differently.; 223 words. Thin for most roles; add detail to your experience.

## Next

- [ ] Read resume.pdf – every line must be true
- [ ] If ATS < 80: edit resume.json (re-word real work in the posting's words), then `jobpilot.py rescore`
- [ ] Optional: `jobpilot.py cover <app>` → fill → `--render`
- [ ] Apply, then `jobpilot.py stage <app> applied`
- [ ] Interview booked? `jobpilot.py prep <app>`
