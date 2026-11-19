// CLI: node ats_score.js <resume.txt> <jd.txt> "<job title>"  -> JSON (Shortlist ATS Scanner's analyze())
const fs=require("fs");
const {analyze}=require("./ats_core.js");
const [,,rf,jf,role]=process.argv;
const a=analyze(fs.readFileSync(rf,"utf8"),fs.readFileSync(jf,"utf8"),role||"");
const miss=a.all.filter(s=>s.credit<1).map(s=>({k:s.name,credit:+s.credit.toFixed(2),resume:s.r,jd:s.f,soft:s.soft,pref:s.pref,spelling:!!s.spelling}));
console.log(JSON.stringify({score:a.score,parts:a.parts.map(p=>({k:p.k,v:+p.v.toFixed(1),max:p.max})),gaps:miss,checks:a.checks.filter(c=>c.s!=="pass").map(c=>c.t)},null,1));
