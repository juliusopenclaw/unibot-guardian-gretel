# UniBot Colab/Gemini Mantle-Gateway Concept

Status: superseded public-safe concept draft, not the active release contract,
not legal advice, not exam clearance.
Date: 2026-06-14

## Executive Position

The active Mantle release contract uses A0-A4 for local practice and A0-A2 as
the unapproved controlled-exam candidate boundary. The A5 tier described later
in this historical concept is a future design option only; it is not exposed by
the current Chrome side panel or institutional release packet.

UniBot should not be presented as a free AI solver for exams. The defensible concept is a two-layer architecture:

1. `practice_overlay`: a visible mantle over Colab/Gemini or Jupyter for practice, prompt cards, pasted-output review, and Help Ledger documentation.
2. `exam_controlled_gateway`: a controlled notebook route for any real exam setting, activated only after written authority approval and limited to A0-A2 support unless a stricter written rule says otherwise.

The practice overlay demonstrates the pedagogical idea. The gateway is the reviewable exam architecture.

## Policy Reading

Current University of Cologne materials support a differentiated approach:

- Generative AI can be a tool whose use may be allowed, partially allowed, or forbidden in a specific exam.
- The decisive exam-law criterion is independent work.
- If AI is used while independent work remains, the Justitiariat states that exam law does not object in principle.
- In open-book exams where aids are generally allowed, AI use can be permissible if independent work remains.
- A ban on active AI use must be specific, enforceable, and proveable enough to be meaningful.
- Documentation and transparency are central.

Primary sources:

- UzK Justitiariat, KI and exam law: https://verwaltung.uni-koeln.de/stabsstelle02.1/content/faq/data/kuenstliche_intelligenz/index_ger.html
- UzK KI in education: https://uni-koeln.de/studium-lehre/lehrende/ki-in-der-bildung/wie-kann-ich-generative-ki-im-kontext-von-lehre-und-lernen-produktiv-anwenden
- ITCC KI guideline FAQ: https://itcc.uni-koeln.de/services/software/kuenstliche-intelligenz/faq-zur-ki-richtlinie
- Phil-Fak KI exam FAQ: https://phil-fak.uni-koeln.de/fakultaet/pruefungsrecht/taeuschungsversuche-plagiate/faq-umgang-mit-ki
- Phil-Fak KI guideline PDF: https://phil-fak.uni-koeln.de/sites/phil-fak/lehre_studium/fachuebergreifend/Leitlinien_KI-Nutzung_PHIL.pdf
- HF KI in exam work summary: https://hf.uni-koeln.de/data/eso24/File/2026%20-%20HF-INFO%20KI%20in%20Prufungsleistungen%20Zusammenfassung.pdf
- SZI page on individual study accommodations - https://inklusion.uni-koeln.de/informationen/nachteilsausgleich/index_ger.html
- MedFak page on study and exam accommodations - https://medfak.uni-koeln.de/studium-lehre/beratung-service/nachteilsausgleich

## Architecture Decision

### Practice Overlay

Purpose:

- help students use Colab/Gemini and Jupyter reflectively;
- generate a Socratic Prompt Card;
- review pasted external AI output before use;
- block final solutions, complete code, inserted values, final interpretations, private data, and weak source claims;
- store only hashes and structured Help Ledger metadata by default.

Recommended implementation:

- Chrome MV3 extension;
- content script for visible status and selected text handoff;
- side panel for prompt card, output review, Help Ledger, reflection, and adaptive microtasks;
- local UniBot API at `127.0.0.1:8765`;
- offline fallback that remains visibly practice-only.

Technical limits:

- Chrome content scripts run in isolated worlds and should not be treated as hard exam security.
- Declarative network rules can block or modify requests by rules, but they are not semantic solution filters.
- External Gemini output may already have reached the learner before a copy/paste postfilter runs.

Chrome sources:

- Content scripts: https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts
- Side Panel API: https://developer.chrome.com/docs/extensions/reference/api/sidePanel
- Declarative Net Request: https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest

### Controlled Gateway

Purpose:

- handle approved exam use in a controlled, reviewable route;
- keep materials local or in a managed environment;
- freeze allowed materials with SHA evidence;
- filter AI/tutor output before display;
- export notebook, manifest, Help Ledger, process log, and red-line receipt.

Recommended implementation:

- local Jupyter/desktop exam app or managed Jupyter route;
- no external cloud AI by default in exam mode;
- if internet or Google search is allowed, define allowed source categories and keep active generative answer/code generation behind UniBot;
- A0-A2 as the default request;
- A3-A5 only if expressly approved;
- A6 blocked and marked as repeat/invalidated-task condition.

Jupyter source:

- Jupyter AI connects AI agents to notebooks and includes permission gates before file writes, command execution, or tool use: https://jupyter-ai.readthedocs.io/en/v3/

## Colab/Gemini Position

Google sources confirm that Colab/Gemini can generate code and that outputs require validation. Google also introduced Learn Mode, which frames Gemini as a coding tutor giving step-by-step guidance instead of simply writing code.

Sources:

- Colab Learn Mode: https://blog.google/innovation-and-ai/technology/developers-tools/colab-updates/
- Colab Enterprise Gemini code completion/generation: https://docs.cloud.google.com/colab/docs/use-code-completion

Implication:

- Colab/Gemini is useful for practice and didactic alignment.
- For exams, free Gemini use is too broad unless the exam rule expressly permits it.
- The safer proposal is: Google/Web documentation may be allowed as source access, while generative answer/code help must pass through UniBot's A0-A2 gateway or remain disabled.

## Help Levels

| Level | Meaning | Exam default |
|---|---|---|
| A0 | no subject help; accessibility-only support | allow if approved as assistive function |
| A1 | source, syntax, tool orientation | allow and document |
| A2 | Socratic question, no new code or result | allow and document |
| A3 | conceptual hint | explicit decision required |
| A4 | code skeleton or debug direction | high risk; explicit written limit |
| A5 | concrete fix or partial solution | generally outside default exam request |
| A6 | complete solution, inserted values, final interpretation | block; repeat/flag task |

Do not frame this as an exact percentage of own work. Use `independence evidence`, `help-level profile`, and `human-reviewable documentation` instead.

## Research Support

Educational AI programming assistants can be designed to help without revealing solutions:

- CodeAid reports an LLM programming assistant for a 700-student class that aims to help without revealing code solutions: https://arxiv.org/abs/2401.11314
- CodeHelp describes guardrails for scalable programming help without directly revealing solutions: https://arxiv.org/abs/2308.06921

This supports UniBot's core design rule: useful tutoring can be bounded as scaffolding rather than solution delivery.

## Future Course Tutor Mode

The exam gateway should remain narrow. The later `course_tutor_mode` can be richer, more motivating, and more instructional, as long as it is separated from exam deployment.

Purpose:

- turn cleared course videos, transcripts, slides, notebooks, and public documentation into active learning objects;
- guide notebook work through prediction, execution, observation, debugging, source checking, and reflection;
- convert passive video watching into short learning segments, retrieval prompts, misconception checks, and notebook applications;
- maintain a private formative learner model without grading, surveillance, or disciplinary use.

Pedagogical design principles:

- Universal Design for Learning: multiple means of engagement, representation, action, and expression; adjustable display; accessible and assistive tools; graduated support for practice and performance.
- Active learning: the learner must do discipline-relevant work, not merely consume generated explanations.
- Retrieval and spacing: the tutor should schedule low-stakes recall, distributed practice, and short transfer tasks.
- ICAP: activities should move from passive viewing to active annotation, constructive self-explanation, and interactive tutor or peer work.
- Source-bound tutoring: generated guidance must remain linked to source cards, course context, and uncertainty notes.

Sources:

- CAST UDL Guidelines 3.0: https://udlguidelines.cast.org/
- Freeman et al. 2014, active learning in STEM: https://www.pnas.org/doi/10.1073/pnas.1319030111
- Dunlosky et al. 2013, effective learning techniques: https://journals.sagepub.com/doi/10.1177/1529100612453266
- Chi and Wylie 2014, ICAP framework: https://eric.ed.gov/?id=EJ1044018

Mode separation:

| Mode | Purpose | Help boundary |
|---|---|---|
| `exam_controlled_gateway` | approved exam aid | narrow A0-A2 default, A6 blocked |
| `practice_overlay` | Colab/Gemini/Jupyter practice | prompt card and postfilter |
| `course_tutor_mode` | course learning with videos, notebooks, sources, and spaced practice | instructionally rich, not an exam solver |

Authority-facing summary:

> In exams, UniBot is a narrow controlled aid. In learning, UniBot is a source-bound tutor that turns course videos, notebooks, and documentation into active, accessible, evidence-informed study.

## AI Act Boundary

The EU AI Act lists education AI systems for evaluating learning outcomes and monitoring/detecting prohibited behavior during tests as high-risk categories.

Source: https://ai-act-service-desk.ec.europa.eu/en/ai-act/annex-3

UniBot should therefore avoid:

- automatic grading;
- official assessment;
- proctoring;
- AI-detection or disciplinary proof;
- automated accommodation decisions.

UniBot should remain:

- assistive;
- transparent;
- minimal-data;
- local-first where possible;
- human-reviewable;
- not officially active in exams without written clearance.

## Current Pipeline Evidence

`python3 scripts/unibot_pipeline_smoke.py --json` was run on 2026-06-14.

Result:

- pipeline status: `pass`
- checks: 12/12 passed
- red-team: 9/9 passed
- source cards: 21
- readiness: `public_draft_ready`
- exam deployment: `not_cleared`

This is the desired current state: ready for public-safe draft review and local practice demo, not ready for real exam deployment.

## Submission Language

Recommended authority-facing phrasing:

> UniBot is a controlled assistive layer, not a solution AI. It provides A0-A2 support by default: accessibility help, source/tool orientation, and Socratic questions. It blocks final solutions, inserted values, final interpretations, automatic grading, proctoring, AI detection, and accommodation decisions. Every help event is logged in a minimal Help Ledger so independent work remains reviewable by humans.

## Open Decisions For Authority Review

1. Which materials may be frozen into the allowed-material manifest?
2. Which help levels are allowed, restricted, or blocked?
3. Which accessibility functions are point-neutral?
4. Is internet access allowed, and if yes, which categories?
5. Is Colab/Gemini fully disabled, practice-only, or allowed only through UniBot's A0-A2 gateway?
6. Must the Help Ledger be submitted?
7. Who reviews the export package?
8. What is the fallback if the app, notebook, or local kernel fails?
