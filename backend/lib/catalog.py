"""Static training catalog: exercises, difficulty tiers, scenario pool.

Scenarios carry `known` (shown in the pre-call brief) and `hidden` (only the AI
prospect sees it — the rep must discover it through questioning).
"""

EXERCISES = [
    {
        "id": "cold-call",
        "name": "Cold Call",
        "tagline": "Earn the right to a conversation from a standing start.",
        "description": "Open a completely cold prospect conversation, create curiosity, survive the brush-off and earn a next step.",
        "skills": ["Opening", "Confidence", "Objection Handling", "Question Quality", "Next Steps"],
        "duration_min": 5,
        "icon": "phone-outgoing",
    },
    {
        "id": "discovery",
        "name": "Discovery Meeting",
        "tagline": "Find the problem before you sell the solution.",
        "description": "Run a structured discovery conversation: set an agenda, ask layered questions, quantify business impact and qualify.",
        "skills": ["Rapport", "Discovery", "Pain Identification", "Qualification", "Active Listening"],
        "duration_min": 8,
        "icon": "search",
    },
    {
        "id": "objection-handling",
        "name": "Objection Handling",
        "tagline": "Stay in the conversation when the door starts closing.",
        "description": "Face live, escalating objections — price, incumbent, timing, authority — and keep the conversation moving forward.",
        "skills": ["Objection Handling", "Conversational Control", "Active Listening", "Confidence"],
        "duration_min": 6,
        "icon": "shield",
    },
    {
        "id": "closing",
        "name": "Closing",
        "tagline": "Read the buying signals and ask for the commitment.",
        "description": "You are late in the cycle. Surface remaining concerns, confirm the decision process and ask for a clear commitment.",
        "skills": ["Closing", "Next Steps", "Qualification", "Conversational Control"],
        "duration_min": 6,
        "icon": "handshake",
    },
    {
        "id": "value-statement",
        "name": "Value Statement",
        "tagline": "Say why it matters, in their language.",
        "description": "Articulate the value of your offering with clarity, relevance, differentiation and business outcome — not feature lists.",
        "skills": ["Value Communication", "Clarity", "Confidence"],
        "duration_min": 4,
        "icon": "target",
    },
    {
        "id": "commercial-30s",
        "name": "30-Second Commercial",
        "tagline": "Who you help, what you fix, why they should stay on the line.",
        "description": "Deliver a tight introduction: who you help, the problems you solve, why it matters and what makes you different.",
        "skills": ["Clarity", "Value Communication", "Opening"],
        "duration_min": 3,
        "icon": "timer",
    },
    {
        "id": "in-person",
        "name": "In-Person Interaction",
        "tagline": "Face-to-face, no script, no screen.",
        "description": "Networking, walk-ins and scheduled in-person meetings where body language and presence carry the conversation.",
        "skills": ["Rapport", "Opening", "Discovery", "Next Steps"],
        "duration_min": 6,
        "icon": "users",
    },
    {
        "id": "phone-sales",
        "name": "Phone Sales",
        "tagline": "Your voice is the only tool you have.",
        "description": "Inbound and outbound telephone selling where tonality, pacing and listening do all the work.",
        "skills": ["Confidence", "Clarity", "Active Listening", "Closing"],
        "duration_min": 6,
        "icon": "phone",
    },
]

DIFFICULTIES = [
    {
        "level": 1,
        "name": "Beginner",
        "subtitle": "Cooperative prospect",
        "behavior": "Friendly and patient. Shares information readily, raises at most one soft objection, gives the rep time to think and gently nudges the conversation forward.",
        "unlock_xp": 0,
    },
    {
        "level": 2,
        "name": "Developing",
        "subtitle": "Realistic prospect",
        "behavior": "Polite but not eager. Answers what is asked and little more, offers mild resistance and expects reasonably good questions before opening up.",
        "unlock_xp": 150,
    },
    {
        "level": 3,
        "name": "Experienced",
        "subtitle": "Busy and skeptical",
        "behavior": "Time-pressed and skeptical. Gives short answers, mentions competing priorities, raises real objections and only elaborates when the question earns it.",
        "unlock_xp": 400,
    },
    {
        "level": 4,
        "name": "Advanced",
        "subtitle": "Highly skeptical",
        "behavior": "Challenges assumptions, answers incompletely, occasionally interrupts or changes subject, pushes back on vague claims and demands specifics before engaging.",
        "unlock_xp": 900,
    },
    {
        "level": 5,
        "name": "Expert",
        "subtitle": "Difficult real-world buyer",
        "behavior": "Impatient, guarded, price sensitive and highly experienced with salespeople. Instantly detects generic technique, punishes pitching by disengaging, and only reveals the real problem after genuinely excellent discovery. Rewards outstanding reps by leaning in.",
        "unlock_xp": 1600,
    },
]

SCENARIOS = [
    {
        "id": "crm-vp-sales",
        "seller_role": "Account Executive at Apex Revenue Cloud",
        "product_sheet": {
            "name": "Apex Revenue Cloud",
            "one_liner": "A mid-market CRM and forecasting platform for B2B sales teams of 20-200 reps.",
            "features": [
                "Single pipeline view that consolidates CRM, email and spreadsheet data",
                "Forecast roll-up with the underlying maths exposed per deal",
                "Deal-slip alerts that fire while the quarter is still live",
                "Rep onboarding playbooks with guided call flows",
                "Two-way sync with email, calendar and common finance tools",
            ],
            "benefits": [
                "A forecast the VP can defend to a board without caveats",
                "New reps productive in weeks rather than months",
                "Slipping deals surfaced early enough to act on",
                "One source of truth instead of four disconnected tools",
            ],
            "pricing": "$95 per user / month on annual billing. Typical 75-person org with 8 reps lands around $9k/year. Implementation is $4k one-off and takes about three weeks.",
            "differentiators": [
                "Shows the maths behind every forecast number rather than a black-box score",
                "Deployed without a data-warehouse project — three weeks, not three quarters",
                "Onboarding playbooks included rather than sold as a separate module",
            ],
            "limitations": [
                "No native marketing automation — integrates rather than replaces",
                "Below about 10 reps the forecasting value is limited",
                "Custom finance-system integrations may add scope",
            ],
            "use_cases": [
                "Sales leaders who cannot produce a credible forecast",
                "Teams onboarding reps faster after headcount growth",
                "Orgs consolidating a stack of point tools",
            ],
        },
        "things_to_remember": [
            "You are selling the meeting, not the platform",
            "Do not quote a price before you know what the problem costs them",
            "Jordan is newly promoted — status and credibility matter to them",
        ],
        "exercise_ids": ["cold-call", "discovery", "closing", "phone-sales"],
        "product": "a mid-market CRM and revenue platform",
        "prospect_name": "Jordan Miller",
        "prospect_role": "VP of Sales",
        "company": "Harborline Logistics",
        "company_size": "75-person B2B organization",
        "industry": "Freight & logistics technology",
        "known": "Harborline runs its sales process across several disconnected tools — spreadsheets, a legacy contact database and email. Jordan was promoted into the VP seat nine months ago.",
        "hidden": "Jordan's real pressure: the CEO wants an accurate forecast for a board meeting in six weeks and Jordan cannot produce one. Two of eight reps quit last quarter because onboarding took four months. There is an unspent $60k software budget that expires at year end. Jordan's brother-in-law sold them the legacy system, which makes replacing it politically awkward. Jordan can approve up to $40k alone; anything above needs the CFO, Priya.",
        "objective": "Determine whether a legitimate opportunity exists and secure a scoped follow-up meeting with a specific date.",
        "personality": "Direct, numbers-driven, dislikes small talk, respects people who challenge them politely.",
        "mood": "Slightly rushed, mildly curious",
        "objections": ["We already have a system.", "Send me some information.", "I don't have budget for this."],
    },
    {
        "id": "hr-ops-director",
        "seller_role": "Senior Account Executive at Rota Health Systems",
        "product_sheet": {
            "name": "Rota Workforce",
            "one_liner": "Clinical staff scheduling and retention analytics for multi-site healthcare providers.",
            "features": [
                "Automated multi-site scheduling with skills and credential matching",
                "Real-time overtime and agency-spend tracking",
                "Shift-swap and self-service app for clinical staff",
                "Turnover risk analytics tied to scheduling patterns",
                "Compliance reporting for staffing ratios",
            ],
            "benefits": [
                "Overtime and agency spend visible before month end, not after",
                "Managers get hours back each week from manual rota building",
                "Staff churn linked to concrete scheduling causes",
                "Audit-ready staffing records without manual assembly",
            ],
            "pricing": "$9 per employee / month. A 400-staff group is about $43k/year. A paid 60-day pilot on two clinics is $4,500 and is credited against the first year.",
            "differentiators": [
                "Built for clinical credentialing rules, not generic shift work",
                "Pilot-first rollout on two sites before any group-wide commitment",
                "Retention analytics rather than scheduling alone",
            ],
            "limitations": [
                "Not a payroll system — exports to payroll providers",
                "Full value needs clean employee and credential data",
                "Below about five sites the analytics are thin",
            ],
            "use_cases": [
                "Multi-site providers with rising overtime spend",
                "Groups with high clinical-staff turnover",
                "Operations leaders under CFO pressure to explain labour cost",
            ],
        },
        "things_to_remember": [
            "Alicia defends her team's current process — do not criticise it",
            "A paid two-clinic pilot is available and is your strongest de-risking tool",
            "Quantify before you present anything",
        ],
        "exercise_ids": ["discovery", "objection-handling", "value-statement", "in-person"],
        "product": "a workforce scheduling and retention analytics platform",
        "prospect_name": "Alicia Reyes",
        "prospect_role": "Director of Operations",
        "company": "Northbay Care Group",
        "company_size": "12 clinics, 400 staff",
        "industry": "Healthcare services",
        "known": "Northbay schedules clinical staff manually across 12 clinics. Alicia has been in role four years and is known internally for defending her team's current process.",
        "hidden": "Overtime spend rose 22% last year and the CFO has asked Alicia to explain it. Turnover among medical assistants is 41%, and Alicia privately believes scheduling chaos is the cause but has never quantified it. She was burned by a failed software rollout in 2022 and will not sign anything without a pilot. Real decision requires the CFO plus the clinical director. Budget cycle opens in the next fiscal quarter.",
        "objective": "Uncover the quantified business impact of the current process and identify the full decision-making group.",
        "personality": "Warm but defensive about her team, analytical, needs evidence, distrusts vendors.",
        "mood": "Guarded, professionally polite",
        "objections": ["We're happy with our current process.", "We tried something like this and it failed.", "I need to speak with my boss."],
    },
    {
        "id": "cfo-price-pressure",
        "seller_role": "Enterprise Account Executive at Ledgerline",
        "product_sheet": {
            "name": "Ledgerline AP Automation",
            "one_liner": "Accounts-payable automation for mid-market manufacturers processing thousands of supplier invoices monthly.",
            "features": [
                "Invoice capture and coding with exception-only review",
                "Approval workflows with delegation and audit trail",
                "Duplicate and fraud detection on every invoice",
                "Early-payment discount capture and penalty avoidance",
                "Pre-built ERP connectors with a fixed-scope integration plan",
            ],
            "benefits": [
                "Approval cycle measured in days rather than weeks",
                "Late-payment penalties largely eliminated",
                "Duplicate payments caught before they leave the building",
                "Finance headcount redeployed off data entry",
            ],
            "pricing": "$180k/year for 4,000 invoices per month, plus a fixed $35k integration. A competing vendor is quoting roughly 30% less on licence but scopes integration hourly.",
            "differentiators": [
                "Fixed-price, fixed-scope ERP integration with a named engineer and a go-live date",
                "Named reference customers on the same ERP version",
                "Rollback plan and parallel-run period included",
            ],
            "limitations": [
                "Not a full procurement suite — AP only",
                "Requires a supplier master data clean-up before go-live",
                "Highly customised ERP builds add integration scope",
            ],
            "use_cases": [
                "Manufacturers with high invoice volume and penalty exposure",
                "Finance teams recovering from a failed systems project",
                "CFOs who need auditable controls on payments",
            ],
        },
        "things_to_remember": [
            "Daniel is late to the process; the controller already supports you",
            "Discounting to win this will lose it — sell the integration plan",
            "$210k of late-payment penalties last year is the number that matters",
        ],
        "exercise_ids": ["objection-handling", "closing", "phone-sales", "value-statement"],
        "product": "an accounts-payable automation suite",
        "prospect_name": "Daniel Okafor",
        "prospect_role": "Chief Financial Officer",
        "company": "Verratek Manufacturing",
        "company_size": "$180M revenue, 600 employees",
        "industry": "Industrial manufacturing",
        "known": "Verratek's finance team processes roughly 4,000 supplier invoices per month. You have already had two conversations with the controller, who is supportive. Daniel is joining the process late.",
        "hidden": "Daniel has a competing bid that is 30% cheaper and he intends to use it as leverage. His actual concern is not price — it is a failed ERP integration two years ago that cost him credibility with the CEO. Late-payment penalties cost Verratek about $210k last year. Daniel has signing authority up to $250k. He will commit if the rep resolves the integration risk with a concrete plan; he will stall indefinitely if the rep discounts instead.",
        "objective": "Identify the true concern behind the price objection and secure a specific commitment or next step.",
        "personality": "Blunt, impatient, tests people, hates being handled.",
        "mood": "Skeptical, pressed for time",
        "objections": ["It's too expensive.", "Your competitor is 30% cheaper.", "I need to think about it.", "Call me in six months."],
    },
    {
        "id": "owner-walkin",
        "seller_role": "Territory Representative at Counterpoint Retail",
        "product_sheet": {
            "name": "Counterpoint POS & Loyalty",
            "one_liner": "Point-of-sale, inventory and customer loyalty for independent multi-location retailers.",
            "features": [
                "Cloud POS across multiple locations with offline mode",
                "Automatic repeat-customer identification and loyalty tracking",
                "Inventory counts with shrink and variance reporting",
                "Simple daily owner dashboard on phone",
                "Staff permissions and till accountability",
            ],
            "benefits": [
                "Know who your repeat customers are and what they buy",
                "Shrink becomes visible instead of invisible",
                "One stock view across all three stores",
                "Handover to the next generation on modern systems",
            ],
            "pricing": "$129 per location / month, hardware from $600 per till, no long-term contract. Three locations is about $4,650 in year one including hardware.",
            "differentiators": [
                "Built for independents, not scaled-down enterprise retail",
                "On-site setup and staff training included",
                "Month-to-month — no multi-year lock-in",
            ],
            "limitations": [
                "No e-commerce storefront included; integrates with common platforms",
                "Loyalty value depends on staff prompting at the till",
                "Older hardware may need replacement",
            ],
            "use_cases": [
                "Independent retailers running 2-5 locations on paper or legacy tills",
                "Owners preparing to hand the business to family",
                "Retailers with unexplained inventory loss",
            ],
        },
        "things_to_remember": [
            "Marcus has run this business 19 years — respect that first",
            "The goal is a scheduled follow-up with the daughter present",
            "He will not discuss numbers until he believes you are genuinely curious",
        ],
        "exercise_ids": ["in-person", "cold-call", "commercial-30s", "value-statement"],
        "product": "a point-of-sale and customer loyalty system",
        "prospect_name": "Marcus Webb",
        "prospect_role": "Owner",
        "company": "Webb & Daughters Outfitters",
        "company_size": "3 retail locations, 28 staff",
        "industry": "Specialty retail",
        "known": "You are meeting Marcus in person at his flagship store during a moderately busy afternoon. He owns three locations and has run the business for 19 years.",
        "hidden": "Marcus's daughter is taking over the business next year and has been pushing him to modernise; he resists advice from vendors but listens to his daughter. Repeat customers make up 65% of revenue but he has no way to identify them. He lost roughly $18k to inventory shrink last year. He will not talk numbers until he decides the rep is genuinely curious about his business rather than reading a script.",
        "objective": "Build enough credibility to earn a real business conversation and a scheduled follow-up with the daughter present.",
        "personality": "Friendly, talkative, proud of his store, deeply allergic to sales scripts.",
        "mood": "Distracted but approachable",
        "objections": ["I'm not interested.", "We've done fine without it for 19 years.", "Leave me a card."],
    },
    {
        "id": "startup-founder-pitch",
        "seller_role": "Account Executive at Perimeter Compliance",
        "product_sheet": {
            "name": "Perimeter",
            "one_liner": "Security and compliance automation that gets B2B SaaS companies through SOC 2 without an internal project team.",
            "features": [
                "Automated evidence collection from cloud, HR and code systems",
                "SOC 2, ISO 27001 and GDPR control frameworks out of the box",
                "Continuous monitoring with drift alerts",
                "Auditor workspace with a partner audit firm included",
                "Security questionnaire and trust-page automation",
            ],
            "benefits": [
                "Audit-ready in weeks with days, not months, of engineering time",
                "Enterprise deals unblocked sooner",
                "Evidence gathered continuously rather than in a panic",
                "Security questionnaires answered without engineering involvement",
            ],
            "pricing": "$18k/year for a 55-person company, including the partner audit-firm fee. Typical time to audit-ready is 6-8 weeks.",
            "differentiators": [
                "Audit firm bundled — one contract, one timeline, one accountable party",
                "Engineering time measured in days because evidence collection is automated",
                "Fixed go-live date rather than an open-ended programme",
            ],
            "limitations": [
                "Does not replace a security engineer for remediation work",
                "Penetration testing is a separate paid add-on",
                "Highly bespoke infrastructure may need manual evidence",
            ],
            "use_cases": [
                "Series A/B SaaS companies blocked on SOC 2 for enterprise deals",
                "Teams attempting compliance manually in spreadsheets",
                "Companies with a board-level compliance deadline",
            ],
        },
        "things_to_remember": [
            "Priya has minutes, not an hour — lead with the point",
            "Anything that adds engineering work is an instant no",
            "She screens vendors aggressively; technical honesty beats polish",
        ],
        "exercise_ids": ["commercial-30s", "value-statement", "cold-call", "discovery"],
        "product": "a security and compliance automation platform",
        "prospect_name": "Priya Raghavan",
        "prospect_role": "Co-founder & CTO",
        "company": "Lumenscale",
        "company_size": "Series A, 55 employees",
        "industry": "B2B SaaS",
        "known": "Lumenscale just closed a Series A and is moving upmarket into enterprise deals. Priya is technical, extremely busy, and screens vendors aggressively.",
        "hidden": "Two enterprise deals worth $1.4M are blocked pending SOC 2 Type II, which Priya's team is attempting manually with a spreadsheet and one overloaded engineer. The board asked about it last week. Priya has 90 days. She has budget but will not spend it on anything that adds engineering work. Her co-founder handles procurement sign-off.",
        "objective": "Deliver a sharp value introduction that earns a real conversation, then uncover the deadline pressure.",
        "personality": "Fast, precise, low tolerance for fluff, respects technical honesty.",
        "mood": "Impatient, interruption-prone",
        "objections": ["I've got two minutes.", "We're building that internally.", "Send me some information."],
    },
]

SKILL_CATEGORIES = [
    "Opening",
    "Rapport",
    "Discovery",
    "Question Quality",
    "Active Listening",
    "Pain Identification",
    "Qualification",
    "Value Communication",
    "Objection Handling",
    "Conversational Control",
    "Confidence",
    "Clarity",
    "Closing",
    "Next Steps",
]

BADGES = [
    {"id": "first-flight", "name": "First Flight", "description": "Complete your first simulation."},
    {"id": "high-scorer", "name": "High Scorer", "description": "Score 80 or above in any simulation."},
    {"id": "discovery-pro", "name": "Discovery Pro", "description": "Score 85+ on Discovery."},
    {"id": "objection-slayer", "name": "Objection Slayer", "description": "Score 80+ on Objection Handling."},
    {"id": "expert-tier", "name": "Expert Tier", "description": "Complete a Level 5 simulation."},
    {"id": "committed", "name": "Committed", "description": "Complete 5 simulations."},
    {"id": "relentless", "name": "Relentless", "description": "Complete 15 simulations."},
    {"id": "streak-3", "name": "On a Streak", "description": "Practice 3 days in a row."},
]


def exercise_by_id(eid: str):
    return next((e for e in EXERCISES if e["id"] == eid), None)


def difficulty_by_level(level: int):
    return next((d for d in DIFFICULTIES if d["level"] == level), None)


def scenario_by_id(sid: str):
    return next((s for s in SCENARIOS if s["id"] == sid), None)


def scenarios_for_exercise(eid: str):
    matches = [s for s in SCENARIOS if eid in s["exercise_ids"]]
    return matches or SCENARIOS


def level_for_xp(xp: int) -> int:
    return max(1, int((xp / 250) ** 0.5) + 1)


def xp_for_level(level: int) -> int:
    return int(((level - 1) ** 2) * 250)
