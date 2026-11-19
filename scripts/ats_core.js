const SKILL_SRC = `python|py;sql;mysql;postgresql|postgres;sql server|mssql;oracle;mongodb;nosql;excel|ms excel|microsoft excel;advanced excel;vlookup;pivot tables|pivot table;google sheets;power bi|powerbi;tableau;looker;qlik;data studio|looker studio;pandas;numpy;scikit-learn|sklearn;tensorflow;pytorch;keras;spark|pyspark|apache spark;hadoop;airflow|apache airflow;dbt;snowflake;bigquery;redshift;databricks;etl;elt;data pipelines|data pipeline;data warehouse|data warehousing|data warehouses;data modeling|data modelling;data visualization|data visualisation;dashboards|dashboard;statistics|statistical analysis;a/b testing|a/b tests|ab testing|experimentation;forecasting;regression;machine learning|ml;deep learning;nlp|natural language processing;computer vision;generative ai|genai|llm|llms;data cleaning|data cleansing;data analysis|data analytics;business intelligence|bi;kpis|kpi;r programming;sas;spss;matlab;javascript|js;typescript;java;c++;c#;golang;rust;ruby;php;kotlin;swift;scala;html;css;react|react.js|reactjs;angular;vue|vue.js;node.js|nodejs|node;next.js|nextjs;express;django;flask;fastapi;spring boot|spring;rest api|rest apis|restful;graphql;microservices;aws|amazon web services;azure;gcp|google cloud;docker;kubernetes|k8s;terraform;ci/cd;jenkins;git|github|gitlab;linux;jira;confluence;agile;scrum;kanban;devops;unit testing;system design;salesforce;hubspot;sap;erp;crm;seo;sem;google analytics;google ads;content marketing;email marketing;social media;copywriting;figma;sketch;adobe xd;photoshop;illustrator;ux research|user research;wireframing;prototyping;product management;product roadmap|roadmap;user stories;market research;competitive analysis;go-to-market|gtm;b2b;saas;lead generation;cold calling;account management;negotiation;pipeline management;quota;financial modeling|financial modelling;budgeting;accounting;gaap;ifrs;valuation;supply chain;logistics;procurement;inventory management;warehouse management|wms;transportation management|tms;freight;demand planning;lean;six sigma;project management;pmp;stakeholder management|stakeholders;communication|communication skills;leadership;problem solving|problem-solving;teamwork|collaboration;presentation skills|presentations;time management;cross-functional|cross functional;mentoring;customer service|customer support;operations;recruiting|talent acquisition;onboarding;payroll`;
const SKILL_SRC2 = `ai|artificial intelligence;power query;dax;vba|excel macros;alteryx;stata;jupyter|jupyter notebook;hypothesis testing;anova;time series|time-series;clustering;classification;predictive modeling|predictive modelling;data governance;data quality;data mining;informatica;talend;ssis;ssrs;kafka|apache kafka;redis;rabbitmq;elasticsearch;nginx;aws lambda;ec2;s3;ansible;prometheus;grafana;selenium;cypress;jest;playwright;junit;pytest;android;ios;flutter;react native;tailwind|tailwind css;redux;webpack;.net|dotnet;asp.net;oop|object-oriented programming|object oriented programming;data structures;algorithms;distributed systems;okrs|okr;sprint planning;backlog;prd|product requirements document;user acceptance testing|uat;sop|sops|standard operating procedures;process improvement;kaizen;root cause analysis|rca;incoterms;freight forwarding;customs clearance;demurrage;detention;last mile|last-mile;fleet management;route optimization|route optimisation;3pl|third-party logistics;ocean freight;air freight;shipment tracking;carrier management;rate negotiation;sap s/4hana|s/4hana;netsuite|oracle netsuite;tally;dynamics 365|microsoft dynamics;ifrs 16;gst;tds;reconciliation|reconciliations;accounts payable;accounts receivable;fp&a;variance analysis;cash flow;audit|auditing;hris;employee engagement;marketing automation;mailchimp;semrush;ahrefs;ppc;b2c;inside sales;enterprise sales;customer success;churn;retention;okta;sso|single sign-on;cybersecurity|information security;iso 27001;soc 2;gdpr;power automate;sharepoint;ms office|microsoft office;powerpoint;adaptability;attention to detail;critical thinking;analytical skills|analytical thinking;interpersonal skills;ownership;decision making|decision-making;written communication;verbal communication;multitasking;conflict resolution;creativity;self-motivated|self motivated`;
/* Hard skills by field. Format: name|alias|alias; */
const SKILL_SRC3 = [
 /* languages & frameworks */ `perl;bash|shell scripting;powershell;objective-c;dart;elixir;haskell;clojure;lua;groovy;cobol;fortran;vb.net;solidity;webassembly|wasm;jquery;bootstrap;sass|scss;svelte;nuxt|nuxt.js;gatsby;ember|ember.js;three.js;d3|d3.js;chart.js;material ui|mui;storybook;vite;babel;npm;yarn;pnpm;laravel;symfony;codeigniter;ruby on rails|rails;nestjs|nest.js;quarkus;micronaut;hibernate;jpa;struts;maven;gradle;entity framework;blazor;xamarin;wpf;winforms;unity;unreal engine;godot;opengl;vulkan;directx;cuda;opencv;openmp;mpi`,
 /* mobile */ `swiftui;jetpack compose;kotlin multiplatform;xcode;android studio;firebase;ionic;cordova;mobile development|mobile app development`,
 /* data, ML & AI */ `matplotlib;seaborn;plotly;scipy;statsmodels;xgboost;lightgbm;catboost;hugging face|huggingface;transformers;langchain;llamaindex;openai api;prompt engineering;rag|retrieval-augmented generation;vector database|vector databases|vector db;pinecone;faiss;mlflow;kubeflow;sagemaker|amazon sagemaker;vertex ai;azure machine learning|azure ml;feature engineering;model deployment;mlops;reinforcement learning;recommender systems|recommendation systems;sentiment analysis;object detection;image classification;bert;gpt;neural networks;cnn|convolutional neural networks;rnn;lstm;bayesian statistics;causal inference;survival analysis;monte carlo;linear programming;operations research;econometrics;data engineering;data lake|data lakes;delta lake;lakehouse;hive|apache hive;presto|trino;flink|apache flink;apache beam;nifi|apache nifi;fivetran;matillion;dagster;prefect;great expectations;dimensional modeling|dimensional modelling|star schema;olap;oltp;change data capture|cdc;metabase;apache superset|superset;domo;sisense;microstrategy;cognos;spotfire;ssms|sql server management studio;t-sql|tsql;pl/sql|plsql;stored procedures;query optimization|query optimisation;cassandra;dynamodb;couchbase;neo4j;firestore;cosmos db|cosmosdb;mariadb;sqlite;teradata;db2;clickhouse;data entry;data management;trend analysis;cohort analysis;funnel analysis;customer analytics;web analytics;statistical modeling|statistical modelling;descriptive statistics;data storytelling;reporting automation|report automation`,
 /* cloud, devops & infra */ `azure devops;github actions;gitlab ci;circleci;travis ci;argo cd|argocd;helm;istio;openshift;rancher;docker compose;vagrant;packer;pulumi;cloudformation|aws cloudformation;bicep;arm templates;serverless;cloud functions;app engine;cloud run;gke;eks;aks;ecs;fargate;rds;aurora;cloudwatch;iam|identity and access management;vpc;load balancing|load balancer|load balancers;cdn;cloudflare;datadog;new relic;splunk;elk stack|elk;logstash;kibana;opentelemetry;jaeger;pagerduty;site reliability engineering|sre;observability;incident management;itil;servicenow;linux administration;windows server;active directory;vmware;hyper-v;computer networking|networking;tcp/ip;dns;dhcp;bgp;ospf;vpn;firewalls|firewall;cisco;juniper;sd-wan;wireshark`,
 /* security */ `penetration testing|pen testing;vulnerability assessment|vulnerability management;siem;security operations|soc;threat modeling|threat modelling;owasp;zero trust;encryption;pki;nist;pci dss|pci-dss;hipaa;sox|sarbanes-oxley;risk assessment;incident response;burp suite;metasploit;nmap;kali linux;cissp;ceh;comptia security+|security+;oscp;cism;cisa`,
 /* QA & testing */ `manual testing;test automation|automation testing;regression testing;integration testing;performance testing;load testing;jmeter;loadrunner;postman;soapui;testng;mocha;chai;cucumber;bdd|behavior-driven development;tdd|test-driven development;appium;test cases;test plans|test planning;quality assurance`,
 /* engineering practices */ `design patterns;solid principles;clean code;domain-driven design|ddd;event-driven architecture;cqrs;soa|service-oriented architecture;api design;api gateway;websockets;grpc;soap;json;xml;yaml;oauth|oauth2|oauth 2.0;jwt;message queues|message queue;multithreading;concurrency;memory management;performance tuning|performance optimization;code review|code reviews;pair programming;version control;frontend|front-end;backend|back-end;full stack|full-stack;responsive design;web accessibility|wcag;cross-browser compatibility;pwa|progressive web apps`,
 /* product & project */ `product strategy;product discovery;product lifecycle|product life cycle;product analytics;mixpanel;amplitude;pendo;hotjar;customer journey|user journey|user journeys;personas;jobs to be done|jtbd;mvp|minimum viable product;feature prioritization|prioritization;release management;requirements gathering;business requirements|brd;functional specifications|functional requirements;gap analysis;swot analysis;business analysis;process mapping;bpmn;visio|microsoft visio;lucidchart;miro;asana;trello;monday.com;clickup;smartsheet;ms project|microsoft project;waterfall;scaled agile|safe agile;prince2;capm;change management;risk management;resource planning;budget management;vendor management;contract management;program management|programme management;portfolio management;pmo`,
 /* design & media */ `ui design|user interface design;ux design|user experience;interaction design;visual design;design systems|design system;usability testing;information architecture;indesign;after effects;premiere pro;final cut pro;davinci resolve;blender;cinema 4d;maya;3ds max;autocad;solidworks;revit;sketchup;catia;fusion 360;ansys;canva;invision;framer;zeplin;protopie;motion graphics;typography;branding|brand identity;photography;video editing`,
 /* marketing */ `digital marketing;performance marketing;growth marketing;product marketing;brand marketing;affiliate marketing;influencer marketing;content strategy;keyword research;link building;on-page seo;technical seo;google tag manager;ga4|google analytics 4;meta ads|facebook ads;linkedin ads;programmatic advertising;display advertising;media planning;media buying;conversion rate optimization|cro;marketing analytics;attribution modeling|attribution;customer acquisition|cac;lifetime value|ltv|clv;roas;cpc|cost per click;ctr|click-through rate;campaign management;klaviyo;marketo;pardot;salesforce marketing cloud;braze;customer segmentation|market segmentation;public relations;event marketing;community management;social media marketing;copy editing;proofreading;content writing;technical writing;blogging`,
 /* sales & customer success */ `prospecting|sales prospecting;outbound sales;inbound sales;b2b sales;solution selling;consultative selling;meddic|meddpicc;account-based marketing|abm;sales forecasting;sales operations;revenue operations|revops;zoho crm|zoho;pipedrive;salesloft;gong;sales navigator|linkedin sales navigator;upselling|upsell;cross-selling|cross-sell;renewals;contract negotiation;territory management;key account management|kam;channel sales;partner management|partnerships;business development;relationship management|client relationship management;customer onboarding;customer retention;nps|net promoter score;csat;zendesk;freshdesk;intercom;ticketing|ticketing systems;sla|slas|service level agreements;escalation management`,
 /* finance & accounting */ `financial analysis;financial reporting;financial planning;cost accounting;management accounting;general ledger|gl;journal entries;month-end close|month end close|month-end closing;bank reconciliation;fixed assets;taxation;income tax;transfer pricing;statutory audit;internal audit;internal controls;ind as;cpa;cfa;acca;chartered accountant;treasury;working capital;credit analysis;quickbooks;xero;sap fico|sap fi/co;oracle financials;hyperion;anaplan;adaptive insights;bloomberg|bloomberg terminal;capital markets;equity research;investment banking;mergers and acquisitions|m&a;dcf|discounted cash flow;lbo;asset management;wealth management;derivatives;fixed income;kyc|know your customer;aml|anti-money laundering;compliance;regulatory reporting;basel`,
 /* HR */ `sourcing;candidate screening|screening;interviewing;employer branding;performance management;compensation and benefits|c&b;hr operations;hr policies;labour law|labor law;employee relations;succession planning;learning and development|l&d;training and development;workforce planning;people analytics|hr analytics;diversity and inclusion|dei|diversity, equity and inclusion;successfactors|sap successfactors;bamboohr;greenhouse;darwinbox`,
 /* operations, supply chain & manufacturing */ `s&op|sales and operations planning;mrp|material requirements planning;warehouse operations;order fulfillment|order fulfilment;reverse logistics;cold chain;import/export|exim|export-import;letters of credit|letter of credit;vendor development;strategic sourcing;category management;supplier management|supplier relationship management;purchase orders|purchase order;rfq|rfp|rfi;spend analysis;cost reduction;quality control|qc;quality management|qms;iso 9001;gmp|good manufacturing practice;haccp;capa;fmea;spc|statistical process control;tpm|total productive maintenance;5s;value stream mapping|vsm;lean manufacturing;lean six sigma|green belt|black belt;production planning;capacity planning;cnc;plc;scada;cad|computer-aided design;industrial engineering;health and safety|hse|ehs;osha`,
 /* healthcare, legal, education */ `ehr|emr|electronic health records;epic systems|epic emr;cerner;clinical research;clinical trials;pharmacovigilance;medical coding;icd-10;cpt coding;patient care;regulatory affairs;contract drafting;legal research;litigation;due diligence;intellectual property;corporate law;curriculum development;lesson planning;instructional design;lms|learning management system;e-learning|elearning;articulate storyline`,
 /* office tools & spoken languages */ `google workspace|g suite;microsoft teams|ms teams;slack;ms word|microsoft word;ms access|microsoft access;english;hindi;spanish;french;german;mandarin;japanese;arabic;portuguese`
].join(";");
/* Soft skills: everything here is scored as a soft skill. */
const SOFT_SRC = `active listening;empathy;emotional intelligence;resilience;work ethic;accountability;integrity;takes initiative|take initiative|show initiative|self-initiative;proactive|proactivity;curiosity;growth mindset;flexibility;organizational skills|organisational skills|organization skills;detail-oriented|detail oriented;results-oriented|result-oriented|results-driven|results driven;customer focus|customer-centric|customer centric|customer obsession;relationship building;influencing|influence;persuasion;public speaking;storytelling;coaching;delegation;people management|team management;team building;strategic thinking;business acumen;commercial awareness;innovation;judgment|judgement;quantitative skills|numerical skills|numeracy;research skills;fast learner|quick learner|learning agility;ability to work under pressure|work under pressure|working under pressure;stress management;patience;cultural awareness|cultural sensitivity;diplomacy;facilitation;consensus building;dependability|dependable;professionalism;positive attitude;self-starter;work independently|independently;open-minded|open-mindedness;prioritisation skills|organising priorities;verbal and written communication|written and verbal communication;listening skills;feedback skills|giving feedback`;
const SOFT = new Set(["stakeholder management","communication","leadership","problem solving","teamwork","presentation skills","time management","cross-functional","mentoring","customer service","negotiation","adaptability","attention to detail","critical thinking","analytical skills","interpersonal skills","ownership","decision making","written communication","verbal communication","multitasking","conflict resolution","creativity","self-motivated"]);
/* Build the skills list. Each spelling belongs to one skill only, so nothing is counted twice. */
const SKILLS = (()=>{
  const seenTerm=new Set(), out=[];
  const addSrc=(src,soft)=>src.split(";").forEach(s=>{
    const t=s.split("|").map(x=>x.trim().toLowerCase()).filter(x=>x&&!seenTerm.has(x));
    if(!t.length) return;
    t.forEach(x=>seenTerm.add(x));
    out.push({name:t[0],terms:t,soft:soft||SOFT.has(t[0])});
  });
  addSrc(SKILL_SRC); addSrc(SKILL_SRC2); addSrc(SKILL_SRC3); addSrc(SOFT_SRC,true);
  return out;
})();

const STOP = new Set(`a about above after again against all also am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its itself just me more most my no nor not of off on once only or other our ours out over own same she should so some such than that the their theirs them then there these they this those through to too under until up very was we were what when where which while who whom why will with would you your yours etc e.g ie using use used within across including include includes ideally such like well per via based able join looking role team teams work working candidate candidates ability strong excellent good great years year experience experiences responsibilities responsibility requirements requirement preferred plus nice have must will skills skill knowledge understanding familiarity proven track record new opportunity company about we're you'll you're our help make high best highly part day days time environment related relevant equivalent degree bachelor's master's other more one two three across key level senior junior lead hybrid remote office full partner insights`.split(/\s+/));
const VERBS = new Set(`accelerated achieved analyzed analysed architected automated boosted built championed collaborated consolidated created cut decreased defined delivered deployed designed developed directed drove eliminated enabled engineered established executed expanded forecasted generated grew identified implemented improved increased initiated integrated introduced launched led managed migrated modeled modelled negotiated optimized optimised orchestrated organized oversaw owned partnered pioneered planned produced quantified rebuilt redesigned reduced refactored resolved restructured revamped saved scaled shipped simplified spearheaded standardized streamlined strengthened tracked trained transformed unified upgraded wrote coordinated mentored presented secured won closed sourced audited evaluated measured researched segmented cleaned merged flagged authored`.split(/\s+/));
const WEAK = /^(responsible for|worked on|worked with|helped|assisted|involved in|did|handled|participated in|duties included|tasked with)\b/i;

/* ---------- Helpers ---------- */
const $ = id=>document.getElementById(id);
const esc = s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const reEsc = s=>s.replace(/[.*+?^${}()|[\]\\\/]/g,"\\$&");
const norm = s=>" "+String(s||"").toLowerCase().replace(/[’']/g,"'").replace(/\s+/g," ")+" ";
const termRe = (t,flags="g")=>new RegExp("(^|[^a-z0-9+#])("+reEsc(t)+")(?:s|es)?(?=$|[^a-z0-9+#])",flags);
/* count mentions of any of several spellings at once (no double counting; plurals included) */
const countAny = (txt,terms)=>(txt.match(new RegExp("(^|[^a-z0-9+#])("+[...terms].sort((a,b)=>b.length-a.length).map(reEsc).join("|")+")(?:s|es)?(?=$|[^a-z0-9+#])","g"))||[]).length;
const count = (txt,t)=>(txt.match(termRe(t))||[]).length;
const has = (txt,t)=>termRe(t,"").test(txt);
const words = s=>(String(s).match(/[A-Za-z0-9][A-Za-z0-9+#.'-]*/g)||[]).length;
function extractBullets(text){
  const lines=text.split(/\r?\n/).map(l=>l.trim()).filter(Boolean);
  let b=lines.filter(l=>/^([-•*▪◦–·●■➢✓>]|\d+[.)])\s*/.test(l)).map(l=>l.replace(/^([-•*▪◦–·●■➢✓>]|\d+[.)])\s*/,""));
  if(b.length<3) b=lines.filter(l=>l.length>45 && !/[|@]/.test(l));
  return b.filter(l=>l.length>15);
}
/* JD terms outside the skills list: repeated 2-word phrases, repeated words, and acronyms/product names. */
const NOISE=new Set("us usa uk eu uae ceo cto cfo coo cmo vp svp evp eoe hr id na am pm it ok faq ctc lpa inr usd we our you".split(" "));
function jdExtras(jd,knownFound,knownAll){
  const isKnown=t=>knownAll.has(t)||knownFound.some(k=>k===t||k.includes(t)||t.includes(k));
  const toks=jd.toLowerCase().replace(/[^a-z0-9+#/&.\s-]/g," ").split(/\s+/).map(t=>t.replace(/^[.-]+|[.-]+$/g,"")).filter(Boolean);
  const bi={},uni={};
  for(let i=0;i<toks.length;i++){
    const a=toks[i],b=toks[i+1];
    if(a.length>3&&!STOP.has(a)&&!/\d/.test(a)) uni[a]=(uni[a]||0)+1;
    if(b&&a.length>2&&b.length>2&&!STOP.has(a)&&!STOP.has(b)&&!/\d/.test(a+b)){const k=a+" "+b;bi[k]=(bi[k]||0)+1}
  }
  const bis=Object.entries(bi).filter(([k,n])=>n>=2&&!isKnown(k)).sort((x,y)=>y[1]-x[1]).slice(0,6);
  const usedW=new Set(bis.flatMap(([k])=>k.split(" ")));
  const unis=Object.entries(uni).filter(([k,n])=>n>=2&&!usedW.has(k)&&!isKnown(k)).sort((x,y)=>y[1]-x[1]).slice(0,8);
  const acr=[...new Set(jd.match(/\b[A-Z][A-Za-z0-9]*[A-Z0-9][A-Za-z0-9]*\b/g)||[])].map(t=>t.toLowerCase()).filter(t=>t.length>=2&&t.length<=14&&!NOISE.has(t)&&!STOP.has(t)&&!isKnown(t)&&!usedW.has(t)&&!unis.some(([u])=>u===t)).slice(0,10);
  return [...bis.map(([k,n])=>({name:k,f:n,w:1})),...unis.map(([k,n])=>({name:k,f:n,w:.5})),...acr.map(k=>({name:k,f:1,w:1}))];
}
const MON={jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,sept:8,oct:9,nov:10,dec:11};
function resumeYears(text){
  const lines=text.split(/\r?\n/); let s=-1,e=lines.length;
  lines.forEach((l,i)=>{const t=l.trim(); if(t.length>=40) return;
    if(s<0&&/^(work\s+|professional\s+)?(experience|employment|work history|career history)\b/i.test(t)) s=i;
    else if(s>=0&&e===lines.length&&/^(education|skills|technical skills|projects|certifications?|awards|achievements|languages|interests)\b/i.test(t)) e=i;});
  const body=(s>=0?lines.slice(s,e):lines).join("\n");
  const now=new Date(), nowM=now.getFullYear()*12+now.getMonth();
  const mon="(jan|feb|mar|apr|may|jun|jul|aug|sept|sep|oct|nov|dec)[a-z]*\\.?\\s*,?\\s*";
  const re=new RegExp("(?:"+mon+")?((?:19|20)\\d{2})\\s*(?:-|–|—|to)\\s*(?:(?:"+mon+")?((?:19|20)\\d{2})|(present|current|now|till date|to date|date))","gi");
  const ranges=[]; let m;
  while((m=re.exec(body))){const a=(+m[2])*12+(m[1]?MON[m[1].toLowerCase()]:0); const b=m[5]?nowM:(+m[4])*12+(m[3]?MON[m[3].toLowerCase()]:11); if(b>=a&&b-a<600) ranges.push([a,b])}
  ranges.sort((x,y)=>x[0]-y[0]); let tot=0,cs=-1,ce=-1;
  ranges.forEach(([a,b])=>{if(a>ce){if(ce>=0)tot+=ce-cs;cs=a;ce=b}else ce=Math.max(ce,b)}); if(ce>=0) tot+=ce-cs;
  const claim=[...text.matchAll(/(\d{1,2})\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:[a-z-]+\s+){0,3}?experience/gi)].map(x=>+x[1]).filter(n=>n<=40);
  return Math.max(tot/12, claim.length?Math.max(...claim):0);
}
const EDU=[[4,/\b(ph\.?\s?d|doctorate)\b/i],[3,/\b(master'?s|m\.sc|msc|m\.tech|mtech|m\.s\.|mba|m\.com|mca|post[- ]?graduate|pgdm)\b/i],[2,/\b(bachelor'?s?|b\.sc|bsc|b\.tech|btech|b\.e\.|b\.a\.|b\.s\.|b\.com|bcom|bca|bba|undergraduate degree)\b/i],[1,/\bdiploma\b/i]];
const EDU_NAME={1:"a diploma",2:"a bachelor's degree",3:"a master's degree",4:"a PhD"};
function eduLevels(t){return EDU.filter(([,re])=>re.test(t)).map(([l])=>l)}

function analyze(resume,jd,role){
  const R=norm(resume), J=norm(jd);
  /* split required vs nice-to-have parts of the JD */
  const prefIdx=jd.search(/\n\s*(nice to have|good to have|preferred( qualifications| skills)?|bonus( points)?|pluses|desirable|additional skills)\b/i);
  const Jreq=norm(prefIdx>0?jd.slice(0,prefIdx):jd);
  /* skills from the dictionary */
  let items=[];
  SKILLS.forEach(s=>{
    const f=countAny(J,s.terms); if(!f) return;
    const fr=s.terms.map(t=>count(J,t));
    const jdTerm=s.terms[fr.indexOf(Math.max(...fr))];
    const sing=t=>t.replace(/s$/,"");               // "dashboard" = "dashboards"
    const exactTerms=s.terms.filter(t=>sing(t)===sing(jdTerm));
    items.push({name:jdTerm,terms:s.terms,f,r:countAny(R,s.terms),rExact:countAny(R,exactTerms),soft:s.soft,pref:s.terms.every(t=>!has(Jreq,t))});
  });
  // drop a skill that is only mentioned inside a longer one ("communication" inside "written communication")
  items=items.filter(a=>!items.some(b=>b!==a&&b.name!==a.name&&termRe(a.name,"").test(" "+b.name+" ")&&a.f<=b.f));
  /* extra JD terms not in the dictionary */
  const extras=jdExtras(jd,items.flatMap(i=>i.terms),new Set(SKILLS.flatMap(s=>s.terms))).map(x=>({...x,terms:[x.name],r:countAny(R,[x.name]),rExact:countAny(R,[x.name]),soft:false,pref:!has(Jreq,x.name),extra:true}));
  const all=[...items,...extras];
  all.forEach(it=>{
    const target=it.f>=3?2:1;                       // a skill the JD stresses should appear at least twice
    it.target=target;
    it.credit=Math.min(it.r,target)/target;
    it.spelling = it.r>0 && it.rExact===0;          // only found under a different spelling
    if(it.spelling) it.credit=Math.min(it.credit,.7);
    it.w=(it.w||1+Math.min(it.f-1,2))*(it.pref?.5:1);
  });
  const ratio=l=>{const W=l.reduce((a,s)=>a+s.w,0);return W?l.reduce((a,s)=>a+s.w*s.credit,0)/W:null};
  const hard=all.filter(s=>!s.soft), soft=all.filter(s=>s.soft);
  const hardRatio=ratio(hard)??0, softRatio=ratio(soft)??1;

  const lines=resume.split(/\r?\n/).map(l=>l.trim());
  const head=(re)=>lines.some(l=>l.length<40 && re.test(l));
  const sec={summary:head(/^(professional\s+)?(summary|profile|objective|about me)\b/i),experience:head(/^(work\s+|professional\s+)?(experience|employment|work history|career history)\b/i),education:head(/^education\b|academic/i),skills:head(/^(technical\s+|core\s+|key\s+)?(skills|competencies|technologies|tech stack)\b/i)};
  const secN=Object.values(sec).filter(Boolean).length;
  const email=/[\w.+-]+@[\w-]+\.[\w.]+/.test(resume), phone=/(\+?\d[\d\s().-]{8,}\d)/.test(resume), li=/linkedin\.com\//i.test(resume);
  const bullets=extractBullets(resume);
  const quant=bullets.filter(b=>/\d|%|\$|₹|€|£/.test(b));
  const strong=bullets.filter(b=>VERBS.has((b.split(/\s+/)[0]||"").toLowerCase().replace(/[^a-z]/g,"")));
  const weak=bullets.filter(b=>WEAK.test(b));
  const wc=words(resume);
  const roleTxt=(role||jd.split(/\n/).find(l=>l.trim())||"").toLowerCase().replace(/\s+[–—-]\s+.*$/,"").replace(/[()|,]/g," ").replace(/\s+/g," ").trim();
  const roleWords=(roleTxt.match(/[a-z+#]{2,}/g)||[]).filter(w=>!STOP.has(w));
  const titleExact=roleTxt.length>1&&has(R,roleTxt);
  const roleHit=roleWords.length? roleWords.filter(w=>has(R,w)).length/roleWords.length : 0;
  const pron=(resume.match(/\b(I|me|my)\b/g)||[]).length;
  /* education + years */
  const jdEduL=eduLevels(jd), resEduL=eduLevels(resume);
  const jdEdu=jdEduL.length?Math.min(...jdEduL):0, resEdu=resEduL.length?Math.max(...resEduL):0;
  const yrM=[...jd.matchAll(/(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|to)\s*\d{1,2}\s*)?\+?\s*(?:years?|yrs?)/gi)].map(m=>+m[1]).filter(n=>n>0&&n<=20);
  const jdYears=yrM.length?yrM[0]:0, ry=resumeYears(resume);

  const parts=[
    {k:"Hard skills & keywords",max:55,v:55*hardRatio},
    {k:"Soft skills",max:10,v:10*softRatio},
    {k:"Job title",max:8,v:titleExact?8:4*roleHit},
    {k:"Quantified impact",max:7,v:bullets.length?7*Math.min(1,(quant.length/bullets.length)/0.6):0},
    {k:"Education",max:5,v:!jdEdu?5:resEdu>=jdEdu?5:0},
    {k:"Years of experience",max:5,v:!jdYears?5:ry>=jdYears?5:ry>=jdYears-1?2.5:0},
    {k:"Sections & contact",max:7,v:4*secN/4+(email?1.5:0)+(phone?1:0)+(li?.5:0)},
    {k:"Action verbs & length",max:3,v:(bullets.length?2*Math.min(1,(strong.length/bullets.length)/0.7):0)+((wc>=350&&wc<=1000)?1:.5)}
  ];
  const score=Math.round(parts.reduce((a,p)=>a+p.v,0));
  const C=[];
  const add=(s,t)=>C.push({s,t});
  const missHard=hard.filter(s=>s.credit===0), partial=all.filter(s=>s.credit>0&&s.credit<1), spell=all.filter(s=>s.spelling);
  add(hardRatio>=.8?"pass":hardRatio>=.55?"warn":"fail",`Hard-skill coverage ${Math.round(hardRatio*100)}%. ${missHard.length?missHard.length+" job keywords are missing from your resume.":"Every job keyword appears in your resume."}`);
  if(partial.length) add("warn",`${partial.length} keyword${partial.length>1?"s are":" is"} only a partial match: mentioned fewer times than the job asks for, or spelled differently.`);
  if(spell.length) add("warn",`Use the job's exact wording: ${spell.slice(0,4).map(s=>"“"+s.name+"”").join(", ")}. Some ATS systems don't match other spellings.`);
  add(titleExact?"pass":roleHit>0?"warn":"fail",roleWords.length?(titleExact?`The exact job title “${roleTxt}” appears in your resume.`:`The exact job title “${roleTxt}” isn't in your resume. Put it in your headline or summary, if it fits your experience.`):"Add a job title to compare against your resume.");
  if(jdEdu) add(resEdu>=jdEdu?"pass":"fail",resEdu>=jdEdu?`Meets the education requirement (${EDU_NAME[jdEdu]}).`:resEdu?`The job asks for ${EDU_NAME[jdEdu]}; your resume shows ${EDU_NAME[resEdu]}.`:`The job asks for ${EDU_NAME[jdEdu]}. Write your degree out clearly, e.g. “Bachelor of Science (B.Sc.)”.`);
  if(jdYears) add(ry>=jdYears?"pass":ry>=jdYears-1?"warn":"fail",ry?`The job asks for ${jdYears}+ years; your resume shows about ${Math.floor(ry*2)/2} years.`:`The job asks for ${jdYears}+ years, but no work dates were found. Use dates like “Jun 2023 – Present”.`);
  Object.entries(sec).forEach(([k,v])=>add(v?"pass":"fail",v?`“${k[0].toUpperCase()+k.slice(1)}” section found.`:`No “${k[0].toUpperCase()+k.slice(1)}” heading found. ATS parsers look for standard headings.`));
  add(email&&phone?"pass":"fail",email&&phone?"Email and phone are present.":"Add "+[!email&&"an email address",!phone&&"a phone number"].filter(Boolean).join(" and ")+" in the resume body.");
  add(li?"pass":"warn",li?"LinkedIn URL included.":"Add your LinkedIn URL. Most recruiters check it.");
  add(quant.length/Math.max(1,bullets.length)>=.5?"pass":"warn",`${quant.length} of ${bullets.length} bullets include a number. Aim for at least half.`);
  if(weak.length) add("warn",`${weak.length} bullet${weak.length>1?"s start":" starts"} with weak phrasing (“${weak[0].split(/\s+/).slice(0,2).join(" ")}…”). Lead with a strong action verb.`);
  add(wc>=350&&wc<=1000?"pass":"warn",`${wc} words. ${wc<350?"Thin for most roles; add detail to your experience.":wc>1000?"Long; trim to 1–2 pages.":"Good length for 1–2 pages."}`);
  if(pron>2) add("warn",`Uses first person (I/me/my) ${pron} times. Resumes read better without pronouns.`);
  if(/[│┃║■▪◆★]|\t{2,}/.test(resume)) add("warn","Special symbols or tab layouts detected. These often mean columns or tables that ATS mis-reads.");
  return {score,parts,all,hard,soft,checks:C,bullets,quant,strong,weak,wc};
}

/* ---------- Render report ---------- */
let last=null, aiResult=null;
module.exports={analyze};
