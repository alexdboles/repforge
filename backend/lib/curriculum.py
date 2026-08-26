"""Training curriculum: what we teach before each simulation, and what the
evaluator therefore grades. Content is skill-specific by design — the closed loop
is "we taught X → you practised X → here is how you did on X".

Each module: learning objectives, key terms, a framework, weak vs strong examples,
beginner mistakes, what strong performance looks like, a knowledge check, and the
`focus_categories` the scorecard weights most heavily for that exercise.
"""
from typing import Any

MODULES: dict[str, dict[str, Any]] = {
    "cold-call": {
        "exercise_id": "cold-call",
        "title": "Cold Calling",
        "promise": "Earn 30 more seconds, then earn the meeting.",
        "duration_min": 6,
        "objectives": [
            "Open a cold call so the prospect chooses to keep listening",
            "Use a permission-based opener instead of a pitch",
            "Create curiosity with a problem, not a product",
            "Treat the first 'no' as a reflex, not a decision",
            "Close for one specific, small next step",
        ],
        "why_it_matters": "A cold call is an interruption. The prospect did not plan for you, is mid-task, and their default answer is no. Your job on a cold call is not to sell the product — it is to earn permission for a real conversation. That is the whole win condition.",
        "when_used": "Outbound prospecting, breaking into new accounts, reviving dormant leads, and any first-touch phone conversation where the prospect has no context for who you are.",
        "terms": [
            {
                "term": "Permission-based opener",
                "definition": "Acknowledging you've interrupted and explicitly asking for a small slice of time. It lowers resistance because it gives the prospect control.",
            },
            {
                "term": "Pattern interrupt",
                "definition": "Anything that breaks the prospect's 'this is a salesperson' script — honesty about the cold call, an unexpected question, a lack of enthusiasm-selling.",
            },
            {
                "term": "Reflex objection",
                "definition": "The automatic brush-off ('not interested', 'send me an email') that arrives before the prospect has processed anything. It is a reflex, not a decision.",
            },
            {
                "term": "Problem hypothesis",
                "definition": "A specific, credible guess about a problem this kind of company has. It earns attention far better than describing your product.",
            },
            {
                "term": "Micro-commitment",
                "definition": "The smallest realistic next step: 20 minutes on Thursday, not 'a partnership'. Small asks get said yes to.",
            },
        ],
        "framework": {
            "name": "The 30-second cold open",
            "steps": [
                {
                    "label": "Name & honesty",
                    "detail": "Use their name, say who you are, and admit the call is cold. Honesty disarms.",
                },
                {
                    "label": "Permission",
                    "detail": "Ask for a defined, tiny amount of time and hand them the veto.",
                },
                {
                    "label": "Problem hypothesis",
                    "detail": "One sentence on a problem companies like theirs have — not a feature list.",
                },
                {
                    "label": "One question",
                    "detail": "Ask an open question about their world and then stop talking.",
                },
                {
                    "label": "Micro-commitment",
                    "detail": "Ask for a specific, small next step with a day and a duration.",
                },
            ],
        },
        "examples": [
            {
                "weak": "Hi, is this Jordan? Great! I'm calling from Apex — we're a leading revenue platform that helps sales teams increase productivity by up to 40% with AI-powered pipeline intelligence. Do you have a few minutes to hear about it?",
                "strong": "Jordan, it's Alex from Apex — I'll be honest, this is a cold call. Can I take 30 seconds to say why I picked up the phone, and you tell me if it's worth continuing?",
                "why": "The weak version leads with the vendor, a claim nobody believes and an open-ended time request. The strong version admits the interruption, asks for a defined 30 seconds and hands the prospect the decision — which is exactly why they usually grant it.",
            },
            {
                "weak": "We help companies streamline their sales process and drive efficiency across the revenue org.",
                "strong": "Most VPs I talk to at 60-to-100-person shops can't get a forecast they'd actually stake their quarter on, because the data lives in four places. I don't know if that's you — is it?",
                "why": "Generic value language means nothing to a stranger. The strong version names a specific, recognisable pain, admits it might not apply, and ends in a question that invites a real answer.",
            },
            {
                "weak": "Prospect: 'Not interested.' — Rep: 'Okay, no problem, I'll send you an email with some information and follow up next quarter.'",
                "strong": "Prospect: 'Not interested.' — Rep: 'Totally fair, you don't know me yet. Quick one before I let you go — is that because forecasting isn't a problem, or because you've already fixed it?'",
                "why": "The weak version accepts a reflex as a decision and trades the call for an email nobody reads. The strong version stays warm, takes the pressure off, and asks one question that separates 'no problem' from 'no interest'.",
            },
        ],
        "mistakes": [
            "Pitching features in the first 20 seconds instead of earning permission",
            "Asking 'how are you today?' — it signals salesperson instantly",
            "Talking for 60 seconds without asking a single question",
            "Accepting the first brush-off as a real answer",
            "Ending with 'I'll send some information' instead of a specific next step",
            "Sounding over-enthusiastic; calm confidence outperforms energy",
        ],
        "strong_performance": [
            "You spoke less than the prospect did",
            "You asked at least three open questions",
            "You named a specific problem before mentioning any product",
            "You handled the first objection with a question, not a counter-pitch",
            "You asked for a dated, time-boxed next step — even if you got a no",
        ],
        "knowledge_check": [
            {
                "question": "The prospect opens with 'I'm not interested.' What's the best next move?",
                "options": [
                    "Offer to send an email instead",
                    "Ask one calm question to find out what the 'no' actually refers to",
                    "Explain the three biggest benefits of your product",
                    "Apologise and end the call",
                ],
                "answer": 1,
                "explanation": "A reflex objection arrives before the prospect has processed anything. One low-pressure question turns a reflex into information.",
            },
            {
                "question": "What is the win condition of a cold call?",
                "options": [
                    "Closing the sale",
                    "Delivering your full value proposition",
                    "Earning a specific next step",
                    "Getting the prospect to like you",
                ],
                "answer": 2,
                "explanation": "Cold calls sell the meeting, never the product. A dated, time-boxed next step is the win.",
            },
        ],
        "focus_categories": [
            "Opening",
            "Confidence",
            "Question Quality",
            "Objection Handling",
            "Conversational Control",
            "Next Steps",
        ],
        "graded_principles": [
            "Permission-based opener that acknowledged the cold interruption",
            "Curiosity created through a specific problem rather than a product pitch",
            "First reflex objection met with a question rather than a counter-pitch",
            "Prospect talked more than the rep did",
            "A specific, small next step was requested",
        ],
    },
    "discovery": {
        "exercise_id": "discovery",
        "title": "Discovery & Needs Analysis",
        "promise": "Find the problem, quantify it, and qualify it — before you solve anything.",
        "duration_min": 7,
        "objectives": [
            "Open with an agenda so the meeting has a shape",
            "Layer questions to move from symptom to consequence",
            "Quantify business impact in money, time or risk",
            "Qualify decision process, authority and timeline without interrogating",
            "Resist the urge to pitch the moment you hear a problem",
        ],
        "why_it_matters": "People do not buy a product; they buy the removal of a consequence. A prospect who has said out loud what a problem costs them is a prospect with a reason to act. Discovery is where deals are actually won — and the most common failure mode is pitching too early.",
        "when_used": "First real meetings, needs analysis calls, requalification of stalled deals, and any conversation where you do not yet know what the problem costs.",
        "terms": [
            {
                "term": "Up-front agreement",
                "definition": "A short agenda agreed at the start: how long, what you'll cover, and what a good outcome looks like for both sides.",
            },
            {
                "term": "Layered questioning",
                "definition": "Following an answer with a deeper question rather than a new topic. Symptom → cause → consequence → cost.",
            },
            {
                "term": "Business impact",
                "definition": "The problem expressed in money, hours, risk or lost revenue. 'It's annoying' is not impact; '$18k of shrink last year' is.",
            },
            {
                "term": "Premature pitch",
                "definition": "Explaining your solution before the prospect has articulated the cost of the problem. It reliably kills discovery.",
            },
            {
                "term": "Decision process",
                "definition": "Who signs, who influences, what steps exist, and what the timeline is driven by.",
            },
        ],
        "framework": {
            "name": "Symptom → Consequence → Cost → Motivation",
            "steps": [
                {"label": "Agenda", "detail": "Agree what you'll cover and how long you have."},
                {"label": "Symptom", "detail": "What is happening today? Get the surface facts."},
                {"label": "Consequence", "detail": "What does that cause downstream — for the team, customers, the number?"},
                {"label": "Cost", "detail": "Quantify it. Money, hours, deals, attrition, risk."},
                {"label": "Motivation", "detail": "Why fix it now, what's changed, and what happens if nothing changes?"},
                {"label": "Qualification", "detail": "Who else is involved, what's the process, what's the timeline?"},
            ],
        },
        "examples": [
            {
                "weak": "Prospect: 'Onboarding new reps takes us about four months.' — Rep: 'That's exactly what we solve — our platform cuts ramp time by half with guided playbooks.'",
                "strong": "Prospect: 'Onboarding new reps takes us about four months.' — Rep: 'Four months is a long runway. What does that cost you — in quota coverage, or in reps who leave before they ramp?'",
                "why": "The weak version trades a discovery goldmine for a feature claim. The strong version makes the prospect say the cost out loud, which is what creates urgency later.",
            },
            {
                "weak": "So what's your budget for something like this?",
                "strong": "If we did fix the forecast problem, is that something you'd fund out of your own budget this year, or does it go through someone else?",
                "why": "The weak version feels like an interrogation and invites a defensive number. The strong version qualifies budget and authority in a single, natural question tied to the problem.",
            },
            {
                "weak": "Any other pain points I should know about?",
                "strong": "You said the CEO wants a forecast for the board. What happens to you if that forecast still isn't credible in six weeks?",
                "why": "Vague sweeper questions get vague answers. The strong version uses something the prospect already said and pushes to personal consequence.",
            },
        ],
        "mistakes": [
            "Pitching the second you hear a problem",
            "Asking a list of questions instead of following the answers",
            "Never converting a problem into a number",
            "Skipping the decision process because it feels rude to ask",
            "Filling silence instead of letting the prospect think",
            "Accepting 'it's fine' without one more question",
        ],
        "strong_performance": [
            "You set an agenda in the first minute",
            "You asked at least two follow-up questions on the same thread",
            "The prospect stated a cost or consequence in their own words",
            "You uncovered who else is involved in the decision",
            "You did not describe your product until the problem was quantified",
        ],
        "knowledge_check": [
            {
                "question": "A prospect mentions employee turnover. What is the highest-value next question?",
                "options": [
                    "Would our retention module help with that?",
                    "How is that turnover affecting productivity, recruiting cost and your managers' time?",
                    "How many people left last year?",
                    "Do you have budget for a solution?",
                ],
                "answer": 1,
                "explanation": "Move from symptom to consequence. Impact questions create the urgency that makes a solution worth funding.",
            },
            {
                "question": "Why is a premature pitch so damaging in discovery?",
                "options": [
                    "It wastes the prospect's time",
                    "It stops the prospect from articulating the cost of their problem",
                    "It makes you sound unprepared",
                    "It shortens the meeting",
                ],
                "answer": 1,
                "explanation": "Once you start solving, the prospect stops explaining. You lose the impact you needed to justify the change.",
            },
        ],
        "focus_categories": [
            "Rapport",
            "Discovery",
            "Question Quality",
            "Active Listening",
            "Pain Identification",
            "Qualification",
            "Next Steps",
        ],
        "graded_principles": [
            "An agenda or up-front agreement was set early",
            "Questions were layered from symptom to consequence to cost",
            "Business impact was quantified in the prospect's own words",
            "Decision process, authority or timeline was uncovered",
            "The rep avoided pitching before the problem was understood",
        ],
    },
    "value-statement": {
        "exercise_id": "value-statement",
        "title": "Value Proposition",
        "promise": "Say why it matters, in their language, in three sentences.",
        "duration_min": 5,
        "objectives": [
            "Build a value statement from the customer's problem, not your feature list",
            "Translate features into business outcomes",
            "Differentiate without naming or trashing competitors",
            "Keep it short enough to be repeated back to you",
            "Anchor value with evidence, not adjectives",
        ],
        "why_it_matters": "Value is not what your product does; it is what changes for the customer because of it. A rep who can only describe features forces the buyer to do the translation — and most buyers won't bother. A clear value statement is also how a champion sells you internally when you're not in the room.",
        "when_used": "After discovery, in executive summaries, when a prospect asks 'so what do you actually do?', and in any moment where you have 30 seconds to justify continuing.",
        "terms": [
            {
                "term": "Feature",
                "definition": "What the product has. 'Real-time dashboards.'",
            },
            {
                "term": "Benefit",
                "definition": "What the feature enables. 'You see pipeline movement as it happens.'",
            },
            {
                "term": "Business outcome",
                "definition": "What changes on the business's scoreboard. 'Your forecast is credible enough to commit to the board.'",
            },
            {
                "term": "Differentiator",
                "definition": "Something true of you and not comfortably true of the alternatives — including doing nothing.",
            },
            {
                "term": "Proof",
                "definition": "A number, a named outcome or a reference that makes the claim credible.",
            },
        ],
        "framework": {
            "name": "Problem → Impact → Solution → Differentiator → Outcome",
            "steps": [
                {"label": "Problem", "detail": "The specific problem this buyer has, in their words."},
                {"label": "Impact", "detail": "What that problem costs them today."},
                {"label": "Solution", "detail": "The one part of what you do that removes it."},
                {"label": "Differentiator", "detail": "Why this approach and not the obvious alternative."},
                {"label": "Outcome", "detail": "The measurable after-state they'd recognise."},
            ],
        },
        "examples": [
            {
                "weak": "We're an all-in-one revenue platform with AI-powered forecasting, pipeline intelligence, conversation analytics and best-in-class integrations, trusted by thousands of companies.",
                "strong": "You said your forecast lives across four tools and you can't defend it to the board. We pull those four sources into one number and show the maths behind it, so when the CEO asks why the quarter moved, you have the answer in the meeting rather than after it.",
                "why": "The weak version is a feature list with no owner. The strong version starts from the buyer's stated problem, names one capability and lands on a moment the buyer personally cares about.",
            },
            {
                "weak": "We're much better than Competitor X — their product is old and their support is terrible.",
                "strong": "Most tools in this space report what already happened. We flag the deals that are slipping while you can still do something about it — that's the difference our customers notice in the first month.",
                "why": "Trashing a competitor makes the buyer defend their previous decision. The strong version differentiates on a capability the buyer can verify, without naming anyone.",
            },
            {
                "weak": "Our platform is very powerful, easy to use, and highly scalable.",
                "strong": "Two of your peers cut invoice-approval time from nine days to two. For a team processing 4,000 invoices a month, that was roughly $200k in late-payment penalties that stopped happening.",
                "why": "Adjectives are unverifiable. Numbers and named before/after states are what a buyer repeats to their CFO.",
            },
        ],
        "mistakes": [
            "Listing features and hoping the buyer translates them",
            "Using the same value statement for every persona",
            "Talking for two minutes when 20 seconds would land",
            "Naming and attacking competitors",
            "Claiming outcomes with no proof or number",
            "Describing value before doing any discovery",
        ],
        "strong_performance": [
            "You opened from the prospect's problem, not your company",
            "Every feature you mentioned was tied to an outcome",
            "You differentiated without disparaging anyone",
            "You included at least one number or concrete proof point",
            "You stopped talking and checked whether it landed",
        ],
        "knowledge_check": [
            {
                "question": "Which of these is a business outcome?",
                "options": [
                    "Real-time dashboards",
                    "You can see your pipeline instantly",
                    "Your forecast is credible enough to commit to the board",
                    "AI-powered insights",
                ],
                "answer": 2,
                "explanation": "Outcomes live on the business's scoreboard. Dashboards are a feature; seeing pipeline is a benefit; a defensible forecast is the outcome.",
            },
            {
                "question": "A prospect says a competitor is cheaper. What's the strongest differentiation move?",
                "options": [
                    "Explain why the competitor's product is worse",
                    "Match the price",
                    "Tie your difference to the cost of the problem they told you about",
                    "Repeat your feature list more forcefully",
                ],
                "answer": 2,
                "explanation": "Differentiation only matters in the context of a problem the buyer has already admitted costs them something.",
            },
        ],
        "focus_categories": [
            "Value Communication",
            "Clarity",
            "Confidence",
            "Active Listening",
            "Conversational Control",
        ],
        "graded_principles": [
            "The statement started from the prospect's problem, not the vendor",
            "Features were translated into business outcomes",
            "Differentiation was made without disparaging competitors",
            "A number, proof point or concrete outcome was used",
            "It was concise and the rep checked whether it landed",
        ],
    },
    "commercial-30s": {
        "exercise_id": "commercial-30s",
        "title": "30-Second Commercial",
        "promise": "Who you help, what you fix, why they should stay on the line.",
        "duration_min": 4,
        "objectives": [
            "Structure a 30-second introduction that ends in a question",
            "Lead with who you help rather than what you are",
            "Name a problem the listener recognises within the first 10 seconds",
            "Cut jargon, credentials and company history",
            "Hit the time budget — length is part of the skill",
        ],
        "why_it_matters": "You get one unrehearsed chance to explain yourself: a networking event, an elevator, a prospect asking 'so what do you do?'. Rambling loses the room; a tight commercial buys you the next five minutes. It also forces the clarity that every other sales conversation depends on.",
        "when_used": "Networking, referrals, event conversations, the first 30 seconds of a cold call, and any introduction where nobody has context for you.",
        "terms": [
            {
                "term": "Who-you-help opener",
                "definition": "Starting with the audience and their situation rather than your job title or company.",
            },
            {
                "term": "Problem statement",
                "definition": "The recognisable pain your audience already feels, said in their language.",
            },
            {
                "term": "Differentiator",
                "definition": "The one thing that makes your approach distinct — one, not five.",
            },
            {
                "term": "Hook question",
                "definition": "The question you end on so the other person talks and the conversation continues.",
            },
            {
                "term": "Time budget",
                "definition": "Roughly 70-90 spoken words. Beyond that you are monologuing.",
            },
        ],
        "framework": {
            "name": "Who → Problem → Why it matters → Difference → Hook",
            "steps": [
                {"label": "Who you help", "detail": "One line naming the audience precisely."},
                {"label": "The problem", "detail": "The pain they'd recognise instantly."},
                {"label": "Why it matters", "detail": "What it costs them if it stays broken."},
                {"label": "What's different", "detail": "One distinguishing thing about your approach."},
                {"label": "Hook question", "detail": "Hand the conversation back with a question."},
            ],
        },
        "examples": [
            {
                "weak": "I'm a senior account executive at Apex Systems. We were founded in 2016 and we're a leading provider of AI-driven revenue intelligence solutions for the modern enterprise, with a full suite of integrations and a really strong customer success organisation.",
                "strong": "I work with sales leaders at 50-to-150-person B2B companies who can't get a forecast they'd bet their quarter on, because the data is spread across four tools. We pull it into one number and show the maths, so the forecast survives the board meeting. How does your team put its forecast together today?",
                "why": "The weak version is about the vendor and ends nowhere. The strong version names the audience, the pain, the stake and one difference, then hands over with a question — in about 60 words.",
            },
            {
                "weak": "We help businesses do more with less by leveraging best-in-class technology.",
                "strong": "You know when a clinic is short-staffed at 6am and someone spends two hours on the phone rebuilding the rota? That's the thing we remove.",
                "why": "Abstract corporate language is invisible. A specific, recognisable moment makes the listener nod before you've explained anything.",
            },
        ],
        "mistakes": [
            "Opening with your title and company history",
            "Running 90 seconds instead of 30",
            "Using internal jargon or product names nobody knows",
            "Listing three differentiators so none of them stick",
            "Finishing on a statement so the other person has nothing to say",
        ],
        "strong_performance": [
            "You named a specific audience in the first sentence",
            "A recognisable problem appeared within 10 seconds",
            "You stayed near 30 seconds",
            "You ended with a question",
            "No jargon and no company history",
        ],
        "knowledge_check": [
            {
                "question": "How should a 30-second commercial end?",
                "options": [
                    "With your company's mission statement",
                    "With a question that hands the conversation back",
                    "With a list of your differentiators",
                    "With a request for a meeting",
                ],
                "answer": 1,
                "explanation": "The point of the commercial is to start a conversation, so it ends in a question, not a full stop.",
            }
        ],
        "focus_categories": ["Opening", "Clarity", "Value Communication", "Confidence"],
        "graded_principles": [
            "Opened with who they help rather than their title or company",
            "Named a recognisable problem early",
            "Kept close to the 30-second time budget",
            "Included one clear differentiator, not a list",
            "Ended on a question that continued the conversation",
        ],
    },
    "objection-handling": {
        "exercise_id": "objection-handling",
        "title": "Objection Handling",
        "promise": "Understand the objection before you answer it.",
        "duration_min": 7,
        "objectives": [
            "Separate a reflex brush-off from a real concern",
            "Acknowledge before you respond — never argue",
            "Ask a question that isolates what the objection actually means",
            "Answer the real concern, then check whether it's resolved",
            "Accept a genuine no without collapsing the relationship",
        ],
        "why_it_matters": "Objections are not rejection; they're the buyer telling you what stands between them and a decision. Most reps lose here by rebutting instantly — which turns a conversation into a debate the buyer must win. Handled well, an objection is the most useful information you'll get all call.",
        "when_used": "Everywhere: cold calls, discovery, pricing conversations, the end of a proposal cycle, and any moment the buyer pushes back.",
        "terms": [
            {
                "term": "Reflex objection",
                "definition": "An automatic brush-off ('not interested', 'send info') that arrives before thought. Needs a question, not an answer.",
            },
            {
                "term": "Real concern",
                "definition": "A specific risk, cost or constraint the buyer has actually considered. Needs a direct, honest answer.",
            },
            {
                "term": "Acknowledge",
                "definition": "Showing you heard it and it's reasonable, before you say anything else. Removes the need for the buyer to repeat it louder.",
            },
            {
                "term": "Isolate",
                "definition": "Establishing whether this is the only thing in the way: 'If we solved that, is there anything else?'",
            },
            {
                "term": "Smokescreen",
                "definition": "A stated objection standing in for the real one — 'too expensive' often means 'I don't believe the value' or 'I've been burned before'.",
            },
        ],
        "framework": {
            "name": "Acknowledge → Question → Isolate → Respond → Confirm",
            "steps": [
                {"label": "Acknowledge", "detail": "Make it safe. 'That's fair' costs nothing."},
                {"label": "Question", "detail": "Find out what the objection actually refers to."},
                {"label": "Isolate", "detail": "Check whether it's the only obstacle."},
                {"label": "Respond", "detail": "Answer the real concern, briefly and honestly."},
                {"label": "Confirm", "detail": "Ask whether that resolved it before moving on."},
            ],
        },
        "examples": [
            {
                "weak": "Prospect: 'It's too expensive.' — Rep: 'Actually, when you look at the ROI, we're the cheapest option in the long run. Most customers see payback in four months.'",
                "strong": "Prospect: 'It's too expensive.' — Rep: 'That's fair — can I ask what you're comparing it against? Is it another quote, or the budget you've been given?'",
                "why": "The weak version argues and assumes price is the issue. The strong version discovers whether 'expensive' means a competing bid, a budget ceiling or a value gap — three completely different problems.",
            },
            {
                "weak": "Prospect: 'We're happy with our current provider.' — Rep: 'I understand, but our platform has features they don't have, like...'",
                "strong": "Prospect: 'We're happy with our current provider.' — Rep: 'Good — that's usually a sign it's working. What made you choose them, and if you could change one thing about how it works today, what would it be?'",
                "why": "'But' erases everything before it. The strong version respects the incumbent decision and opens a door: nobody is 100% happy, and the one-thing question is where the gap shows up.",
            },
            {
                "weak": "Prospect: 'Send me some information.' — Rep: 'Sure, what's your email?'",
                "strong": "Prospect: 'Send me some information.' — Rep: 'Happy to — so I don't send you a generic deck, what specifically would you want it to answer?'",
                "why": "Sending a deck ends the conversation with nothing learned. The strong version converts the brush-off into either a real requirement or a graceful no.",
            },
        ],
        "mistakes": [
            "Rebutting before understanding what the objection means",
            "Using 'but' — it deletes the acknowledgement",
            "Discounting the moment price is mentioned",
            "Answering an objection the buyer didn't actually make",
            "Never checking whether the concern is resolved",
            "Treating every 'no' as something to overcome",
        ],
        "strong_performance": [
            "You acknowledged before responding, every time",
            "You asked at least one question before answering",
            "You isolated whether it was the only obstacle",
            "You answered the real concern, not the stated one",
            "You confirmed resolution before moving on",
        ],
        "knowledge_check": [
            {
                "question": "'It's too expensive' most often means:",
                "options": [
                    "The buyer cannot afford it",
                    "Something specific that needs a question to uncover",
                    "You should offer a discount",
                    "The deal is dead",
                ],
                "answer": 1,
                "explanation": "Price objections stand in for competing quotes, budget ceilings, value gaps or past bad experiences. One question tells you which.",
            },
            {
                "question": "What does isolating an objection mean?",
                "options": [
                    "Ignoring it and moving on",
                    "Checking whether it is the only thing in the way",
                    "Repeating it back word for word",
                    "Escalating it to your manager",
                ],
                "answer": 1,
                "explanation": "If you solve the stated objection and three more appear, you never had the real one.",
            },
        ],
        "focus_categories": [
            "Objection Handling",
            "Active Listening",
            "Conversational Control",
            "Question Quality",
            "Confidence",
        ],
        "graded_principles": [
            "Objections were acknowledged before being answered",
            "A question was asked to isolate what the objection actually meant",
            "The rep answered the real concern rather than the surface one",
            "The rep checked whether the concern was resolved",
            "Control of the conversation was kept without arguing",
        ],
    },
    "closing": {
        "exercise_id": "closing",
        "title": "Closing",
        "promise": "Recognise readiness, clear the last concern, ask plainly.",
        "duration_min": 6,
        "objectives": [
            "Recognise buying signals and stop selling when you hear them",
            "Surface the remaining concern instead of hoping it disappears",
            "Reinforce value in the buyer's own words before asking",
            "Ask for the commitment directly, once, without hedging",
            "Convert any answer into a dated next step",
        ],
        "why_it_matters": "Most deals aren't lost at the close; they're lost because nobody ever actually asked, or because the rep kept selling past the moment the buyer was ready. Closing is a service: it forces a decision so both sides stop spending time on something that isn't going to happen.",
        "when_used": "Late-stage conversations, proposal reviews, renewal and expansion talks, and any point where the next step requires the buyer to commit.",
        "terms": [
            {
                "term": "Buying signal",
                "definition": "Language that assumes ownership — 'how would onboarding work for us', 'when could we start', questions about implementation or contracts.",
            },
            {
                "term": "Trial close",
                "definition": "A low-stakes temperature check: 'How are you feeling about this so far?'",
            },
            {
                "term": "Remaining concern",
                "definition": "The last unresolved risk. If you don't ask for it, it becomes 'let me think about it'.",
            },
            {
                "term": "Direct ask",
                "definition": "A clear, specific request for commitment with a date attached.",
            },
            {
                "term": "Next step",
                "definition": "What happens, who does it, and when — agreed out loud, even when the answer is no.",
            },
        ],
        "framework": {
            "name": "Signal → Summarise → Surface → Ask → Confirm",
            "steps": [
                {"label": "Signal", "detail": "Notice readiness and stop presenting."},
                {"label": "Summarise", "detail": "Play back the problem and impact in their words."},
                {"label": "Surface", "detail": "Ask what's left standing in the way."},
                {"label": "Ask", "detail": "Make one clear, specific request for commitment."},
                {"label": "Confirm", "detail": "Lock a dated next step, whatever the answer."},
            ],
        },
        "examples": [
            {
                "weak": "Prospect: 'How would implementation work for a team our size?' — Rep: 'Great question — let me also show you our reporting module and talk about our roadmap...'",
                "strong": "Prospect: 'How would implementation work for a team our size?' — Rep: 'Two weeks, one workshop, and we'd start with your AP team. That's a rollout question, so let me ask directly — is there anything left that would stop you moving forward this month?'",
                "why": "The weak version talks past a buying signal. The strong version answers the question and converts the signal into a decision conversation.",
            },
            {
                "weak": "So, what do you think? Should we maybe look at getting something going, or do you want to think about it?",
                "strong": "Based on the $210k in penalties you described, I'd recommend we start with the AP team on the 1st. Can I send the agreement over today for you and Priya to review?",
                "why": "Hedged asks invite hedged answers. The strong version reinforces their number, recommends a specific action and requests one concrete thing.",
            },
            {
                "weak": "Prospect: 'I need to think about it.' — Rep: 'No problem, I'll follow up in a couple of weeks.'",
                "strong": "Prospect: 'I need to think about it.' — Rep: 'Of course. Just so I'm useful rather than annoying — what's the part you want to think through? Is it the integration risk or the timing?'",
                "why": "'I'll follow up' is where deals go to die. Naming the likely concerns gives the buyer permission to say what's actually true.",
            },
        ],
        "mistakes": [
            "Talking past a buying signal",
            "Never asking, and calling it 'not being pushy'",
            "Asking with hedging language that invites delay",
            "Discounting to close instead of resolving the real concern",
            "Ending with no date and no owner",
            "Treating 'I need to think about it' as a yes-in-progress",
        ],
        "strong_performance": [
            "You noticed a buying signal and changed gear",
            "You summarised value using their words and numbers",
            "You asked what was still standing in the way",
            "You made one clear, specific ask",
            "You left with a dated next step, even after a no",
        ],
        "knowledge_check": [
            {
                "question": "The prospect asks 'how quickly could we get started?'. What is this?",
                "options": [
                    "A stalling tactic",
                    "A buying signal — move toward a decision",
                    "A request for more product detail",
                    "An objection",
                ],
                "answer": 1,
                "explanation": "Ownership language is a buying signal. Answer briefly, then ask for the commitment.",
            },
            {
                "question": "'I need to think about it' usually means:",
                "options": [
                    "They will decide next week",
                    "There is a specific unresolved concern you haven't surfaced",
                    "The price is too high",
                    "The deal is closed",
                ],
                "answer": 1,
                "explanation": "It's a polite placeholder for an unnamed risk. Ask what part they want to think through.",
            },
        ],
        "focus_categories": [
            "Closing",
            "Next Steps",
            "Objection Handling",
            "Value Communication",
            "Confidence",
            "Conversational Control",
        ],
        "graded_principles": [
            "Buying signals were recognised and acted on",
            "Value was reinforced in the prospect's own words and numbers",
            "The remaining concern was surfaced rather than ignored",
            "A clear, specific commitment was requested",
            "A dated next step was agreed regardless of the answer",
        ],
    },
    "in-person": {
        "exercise_id": "in-person",
        "title": "In-Person Prospecting",
        "promise": "Earn credibility in the room before you ask for anything.",
        "duration_min": 6,
        "objectives": [
            "Read the room before you start talking",
            "Open with genuine curiosity about their business",
            "Respect the interruption — they're mid-work, not mid-meeting",
            "Trade observation for insight rather than pitching",
            "Leave with a scheduled follow-up, not a business card",
        ],
        "why_it_matters": "In person you have advantages no call gives you — you can see the business, the queue, the shelves, the team. You also have a shorter fuse: you're physically interrupting someone's day. Owners and managers decide within a minute whether you're a salesperson reading a script or someone genuinely interested in their business.",
        "when_used": "Walk-ins, retail and trade calls, networking events, site visits, scheduled in-person meetings and conference floor conversations.",
        "terms": [
            {
                "term": "Environmental observation",
                "definition": "Something specific you can only know by being there — a queue, a layout, a handwritten sign. It proves you're paying attention.",
            },
            {
                "term": "Permission in person",
                "definition": "Asking whether now is a good moment, and meaning it. Being told 'not now' with a better time is a win.",
            },
            {
                "term": "Credibility trade",
                "definition": "Offering a relevant insight or observation before asking for anything.",
            },
            {
                "term": "Non-verbal read",
                "definition": "Body language, busyness and attention telling you to slow down, speed up or come back later.",
            },
            {
                "term": "Scheduled follow-up",
                "definition": "A named time with a named person — the only real outcome of a good in-person call.",
            },
        ],
        "framework": {
            "name": "Observe → Ask permission → Be curious → Trade insight → Schedule",
            "steps": [
                {"label": "Observe", "detail": "Notice something specific and real about the business."},
                {"label": "Permission", "detail": "Check whether now works, and offer to come back."},
                {"label": "Curiosity", "detail": "Ask about their business before mentioning yours."},
                {"label": "Trade insight", "detail": "Offer something useful you've seen elsewhere."},
                {"label": "Schedule", "detail": "Agree a specific time with the right people present."},
            ],
        },
        "examples": [
            {
                "weak": "Hi there! Are you the owner? Great — I'd love to tell you about our point-of-sale system, it's really popular with retailers like you and I think it could save you a lot of money.",
                "strong": "Afternoon — I noticed you've got the loyalty cards by the register but they're all handwritten. Are you tracking repeat customers, or is it more by memory? I don't want to interrupt your afternoon; is now bad?",
                "why": "The weak version is a pitch to a stranger who is working. The strong version proves he's actually looking at the business, asks about their process and hands over control of the timing.",
            },
            {
                "weak": "Well, here's my card — give me a call if you ever want to talk about it.",
                "strong": "You mentioned your daughter's taking over next year and she's the one pushing to modernise. Would it be worth the three of us sitting down for 20 minutes next Tuesday, so she can ask the technical questions?",
                "why": "A card is a polite no. The strong version uses something learned in conversation and proposes a specific meeting with the actual decision-makers.",
            },
        ],
        "mistakes": [
            "Pitching before asking a single question",
            "Ignoring how busy they obviously are",
            "Asking 'are you the owner?' as your opener",
            "Talking over customers or staff in the room",
            "Leaving a card instead of booking a time",
            "Missing what's visibly in front of you",
        ],
        "strong_performance": [
            "You referenced something specific about their business",
            "You checked whether the timing worked",
            "You asked about their business before describing yours",
            "You adjusted when they showed they were busy",
            "You left with a named time and the right people",
        ],
        "knowledge_check": [
            {
                "question": "An owner is clearly busy with customers. What's the best move?",
                "options": [
                    "Deliver a faster version of your pitch",
                    "Acknowledge it and propose a specific better time",
                    "Wait silently until they're free",
                    "Leave a brochure and go",
                ],
                "answer": 1,
                "explanation": "Respecting their time earns the return visit. A named time beats a rushed pitch every time.",
            }
        ],
        "focus_categories": [
            "Rapport",
            "Opening",
            "Discovery",
            "Active Listening",
            "Next Steps",
        ],
        "graded_principles": [
            "Something specific and real about the business was referenced",
            "Permission and timing were respected",
            "Curiosity about their business preceded any pitch",
            "The rep adapted to the prospect's mood and availability",
            "A specific follow-up time with the right people was proposed",
        ],
    },
    "phone-sales": {
        "exercise_id": "phone-sales",
        "title": "Phone Sales",
        "promise": "Your voice is the only tool you have — use pace, pause and clarity.",
        "duration_min": 5,
        "objectives": [
            "Control pace and use silence deliberately",
            "Confirm understanding out loud since you have no visual cues",
            "Keep sentences short enough to be followed by ear",
            "Handle interruptions and dead air without panicking",
            "Close the call with an explicit, repeated-back next step",
        ],
        "why_it_matters": "On the phone you lose every visual signal: no nodding, no confusion on their face, no glance at the clock. Tonality, pacing and structure carry the entire conversation, and the most common failure is filling silence with words instead of letting the prospect think.",
        "when_used": "Inbound enquiries, outbound follow-ups, scheduled phone meetings, renewal calls and any conversation happening entirely by voice.",
        "terms": [
            {
                "term": "Deliberate pause",
                "definition": "Silence you choose, after a question. It's the cheapest way to make the other person talk.",
            },
            {
                "term": "Verbal nod",
                "definition": "Short acknowledgements that replace body language: 'got it', 'makes sense', 'say more'.",
            },
            {
                "term": "Playback",
                "definition": "Repeating what you heard in your own words to confirm you understood — and to prove you were listening.",
            },
            {
                "term": "Downward inflection",
                "definition": "Ending statements down rather than up. Up-talk turns statements into requests for approval.",
            },
            {
                "term": "Monologue drift",
                "definition": "Speaking for more than about 30 seconds without a question. On the phone, attention is already gone.",
            },
        ],
        "framework": {
            "name": "Frame → Ask → Pause → Play back → Confirm",
            "steps": [
                {"label": "Frame", "detail": "Say why you're calling and how long it'll take."},
                {"label": "Ask", "detail": "One question at a time, short and clear."},
                {"label": "Pause", "detail": "Stop talking. Let the silence do the work."},
                {"label": "Play back", "detail": "Summarise what you heard before responding."},
                {"label": "Confirm", "detail": "State the next step and have them repeat it back."},
            ],
        },
        "examples": [
            {
                "weak": "So, yeah, I mean, we kind of do a lot of different things — like, we've got the platform side, and then there's also the reporting piece, and, um, some people use it for compliance too, so it kind of depends on what you're looking for, really?",
                "strong": "Two things we're known for: cutting invoice approval time, and flagging duplicate payments. Which of those is closer to what's bothering you right now?",
                "why": "Filler and hedging destroy authority on the phone, where voice is all you have. The strong version is short, structured and ends in a choice that's easy to answer by ear.",
            },
            {
                "weak": "Rep asks a question, hears two seconds of silence, and immediately says: 'or, you know, maybe that's not really an issue for you, we could talk about something else...'",
                "strong": "Rep asks the question and stays quiet for four seconds. The prospect fills the silence with the most useful sentence of the call.",
                "why": "Silence feels far longer to the person who asked. Reps who can hold it get answers reps who can't never hear.",
            },
        ],
        "mistakes": [
            "Filling every silence",
            "Stacking three questions into one sentence",
            "Monologuing because you can't see them disengaging",
            "Up-talking so every statement sounds like a request",
            "Ending the call without confirming the next step out loud",
        ],
        "strong_performance": [
            "You paused after questions instead of talking over the answer",
            "You played back what you heard at least once",
            "Your turns were short and one question at a time",
            "You used verbal acknowledgements to keep the conversation flowing",
            "The next step was stated explicitly and confirmed",
        ],
        "knowledge_check": [
            {
                "question": "You ask a question and the line goes quiet for three seconds. What should you do?",
                "options": [
                    "Rephrase the question immediately",
                    "Stay silent and let them answer",
                    "Move on to another topic",
                    "Apologise for the awkwardness",
                ],
                "answer": 1,
                "explanation": "Silence after a question is thinking time. Filling it steals the answer you asked for.",
            }
        ],
        "focus_categories": [
            "Clarity",
            "Confidence",
            "Active Listening",
            "Conversational Control",
            "Next Steps",
        ],
        "graded_principles": [
            "Turns were short and focused on one question at a time",
            "Silence was used rather than filled",
            "Understanding was confirmed by playing back what was heard",
            "Filler and hedging language were kept low",
            "The next step was stated explicitly and confirmed",
        ],
    },
}


def module_for(exercise_id: str) -> dict[str, Any] | None:
    return MODULES.get(exercise_id)


def focus_categories(exercise_id: str) -> list[str]:
    mod = MODULES.get(exercise_id)
    return mod["focus_categories"] if mod else []


def graded_principles(exercise_id: str) -> list[str]:
    mod = MODULES.get(exercise_id)
    return mod["graded_principles"] if mod else []
