# UniBot Threat Model

Status: separate UniBot track.

## Assets

- Student independence and exam integrity.
- Private course material and private communications.
- Health, disability, and accommodation information.
- Raw external AI output.
- Help Ledger, source cards, and selftest scores.
- Public GitHub release boundary.

## Risks And Controls

| Risk | Control |
| --- | --- |
| External AI gives a complete solution. | Postfilter blocks final solutions, complete code, values, and final interpretations; only a Socratic hint is shown. |
| Student pastes private data into Gemini or UniBot. | Privacy detector flags emails, phone numbers, matriculation hints, health/accommodation terms, local paths, and secrets. |
| Overlay is mistaken for exam security. | Product language states practice overlay only; exam mode requires controlled channel or managed environment plus written approval. |
| Colab DOM changes break detection. | Extension offers copy/paste fallback and does not claim full capture. |
| AI-generated sources are false. | Source-risk category blocks weak citation claims and requires real course or official documentation. |
| Accessibility help is treated as cheating. | Accessibility support is score-neutral and separate from subject-matter help. |
| Independence Score becomes a grade. | Score is private, formative, local-only, and never an official assessment. |
| Public release leaks private material. | Public build excludes emails, private course files, health data, local paths, and raw AI transcripts. |
| Exam mode uses not-cleared KI. | `exam_controlled` blocks external KI unless a written clearance reference is present. |

## Security Boundary

A standard browser extension can support transparency and visible filtering, but
it cannot guarantee that every model response is intercepted before display. A
real exam-grade variant must use a controlled model gateway, managed browser, or
managed Jupyter environment where raw model output is unavailable until UniBot
has filtered it.

## Red-Team Smoke Cases

- "Hier ist der komplette Code ..." -> blocked.
- Python code block with imports and plotting -> blocked.
- "werte = [1, 2, 3]" -> blocked as value insertion.
- Email, diagnosis, matriculation hint, local path, API key -> blocked.
- "laut Studie ..." without verifiable source -> source-risk.
- `exam_controlled` without written approval -> blocked.
- A0 accessibility-only help -> score-neutral.
- Notebook with outputs or solution markers -> blocked.
- Ledger reflection with private data -> redacted.
- Public release fixture with private data, secrets, raw transcript marker, or
  private material reference -> blocked.

Run these checks through `POST /api/unibot/redteam/run` or the Python function
`run_redteam_smoke()`.
