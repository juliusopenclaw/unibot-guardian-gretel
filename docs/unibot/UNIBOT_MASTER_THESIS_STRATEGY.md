# UniBot Master Thesis Strategy

> Legacy alternative study route. The active public UniBot framing is a
> Gretel-built, bachelor-thesis-level research package; this document is kept
> for historical planning context and does not change the active release or
> institutional presentation scope.

Status: separate UniBot track.

## Research Frame

Working title:
Socratic Integrity Layers for AI-Assisted Programming Practice in Higher
Education.

Core question:
Can a transparent Guardian layer around general-purpose coding AI preserve
student cognitive work while improving access, reflection, and learning support
in an introductory Python/neuroscience context?

## Method

Use Design Science Research:

1. Build a narrow Guardian MVP.
2. Run formative usability and learning-process tests with synthetic tasks.
3. Red-team solution leakage, privacy leakage, prompt injection, source risks,
   and exam-mode misuse.
4. Revise the artifact and document limitations.

## Evaluation Boundary

- No real exam performance.
- No grades.
- No diagnoses.
- No proctoring.
- No AI detection as disciplinary evidence.
- No automatic decision on accommodation.

## Measures

- Does the system convert answer-giving into Socratic prompts?
- Does the learner still state the next step in their own words?
- Are private data and final solutions blocked?
- Is the Help Ledger understandable to students and reviewers?
- Does the private score reflect help intensity without penalising accessibility?
- Do participants report less false mastery and clearer source awareness?

## Evaluation Packet

The machine-readable evaluation packet exposes synthetic tasks, a codebook,
formative measures, consent boundaries, stop rules, data-management limits,
quality gates, and source cards through:

- `POST /api/unibot/evaluation-packet`
- `POST /api/unibot/evaluation-packet-markdown`
- `POST /api/unibot/evaluation-tasks`
- `POST /api/unibot/pilot-protocol`
- `POST /api/unibot/pilot-protocol-markdown`
- `POST /api/unibot/data-protection-screening`
- `POST /api/unibot/data-protection-screening-markdown`
- `POST /api/unibot/review-board-packet`
- `POST /api/unibot/review-board-packet-markdown`

It is a draft until ethics, Datenschutz, and exam-authority review decide what
may be used in a real pilot.

## Public Reproduction Package

- Code for `unibot/`.
- Browser extension spike.
- Synthetic tasks and demo outputs.
- Source cards.
- Threat model.
- Evaluation protocol and red-team checklist.
- Machine-readable evaluation packet with synthetic tasks and codebook.
- Course-material staging policy with hashes, review status, skill tags, and
  public summaries only.
- Adaptive task-plan demo showing how local skill-state signals become
  practice-only follow-up tasks.
- Local demo test plan for reproducible practice walkthroughs and public-safe
  bug reports.
- Demo feedback contract for local issue reports and public-safe aggregate
  summaries.
- Feedback triage contract for converting validated demo reports into
  prioritized, public-safe maintenance items.
- GitHub issue bundle draft for public collaboration without private data.
- Release and contributor runbook for a reproducible public quickstart,
  contribution rules, release gates, troubleshooting, and careful public
  language.
- Compliance matrix linking source cards to product rules, controls, blocked
  uses, reviewer groups, and verification evidence.
- Pilot protocol with participant information, consent checklist,
  data-management plan, ethics review triggers, session flow, stop rules, and
  readiness gates.
- Data-protection screening with processing activities, risk register, open
  Datenschutz decisions, and review gates before any real pilot data collection.
- Authority handoff packet as a public-safe review artifact.
- Review board packet mapping institutional reviewer packets, open decisions, and
  required evidence per authority track before exam-control planning.
- System Card, Data Card, and limitations.

The public package is also available through:

- `POST /api/unibot/publication-package`
- `POST /api/unibot/publication-package-markdown`
- `POST /api/unibot/release-runbook`
- `POST /api/unibot/release-runbook-markdown`
- `POST /api/unibot/compliance-matrix`
- `POST /api/unibot/compliance-matrix-markdown`
- `POST /api/unibot/pilot-protocol`
- `POST /api/unibot/pilot-protocol-markdown`
- `POST /api/unibot/data-protection-screening`
- `POST /api/unibot/data-protection-screening-markdown`

Private course material, emails, health data, raw logs, and local file paths are
excluded from the public package.
