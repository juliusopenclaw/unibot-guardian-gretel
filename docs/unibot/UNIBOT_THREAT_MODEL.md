# UniBot Threat Model

Status: separate UniBot track.

## Release Review-Board Claim Alignment

The threat model carries `threat_model_release_review_board_claim_alignment` with
the contract `unibot-threat-model-release-review-board-claim-alignment-v1`. It
links source cards, source-card drift checks, red-team smoke evidence,
publication package, release runbook, review-board packet, public-safety gate,
and human submission gates.

Threat-model claims are risk-control language only. They do not approve
publication, institutional submission, provider calls, exam use, official
grading, proctoring, or KI-detection evidence.

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
| Colab DOM changes break detection. | Separate Colab, Jupyter, and manual-selection adapters report confidence; low-confidence capture is rejected. |
| AI-generated sources are false. | Source-risk category blocks weak citation claims and requires real course or official documentation. |
| Accessibility help is treated as cheating. | Accessibility support is score-neutral and separate from subject-matter help. |
| Assistance exposure becomes a grade. | The report separates help cost, attempt hashes, revisions, and transfer evidence; it explicitly rejects automatic grading and authorship claims. |
| A malicious page calls the local tutor. | The alpha extension uses Native Messaging with an exact extension origin. The HTTP compatibility path retains pairing, origin pinning, and session tokens. |
| Raw notebook text leaks through logs. | Runtime text is held in memory; local records and voluntary reports contain metadata and hashes only. |
| A local notebook path or partial upload leaks through the browser bridge. | The file picker sends no path; the Companion accepts one bounded 32 KiB-chunk upload, checks a path-free `.ipynb` label and SHA-256, expires abandoned uploads, then sanitizes before local storage. |
| A busy port or an immediately failing Jupyter process is reported as a running gateway. | The launcher probes the loopback port before spawning Jupyter and rejects an already-exited process before opening the browser or writing gateway state. |
| Public release leaks private material. | Public build excludes emails, private course files, health data, local paths, and raw AI transcripts. |
| Exam mode uses not-cleared KI. | `exam_controlled` blocks external KI unless a written clearance reference is present. |

## Controlled Exam Rehearsal v1

The controlled rehearsal is a separate synthetic review track. It does not
upgrade Mantle 2.1 or Colab into an exam-security product.

| Rehearsal risk | Control and residual boundary |
| --- | --- |
| A different or modified starting notebook is used. | Version 1 accepts one public fixture by exact raw SHA-256, sanitizes it, binds both hashes into an immutable contract, and edits a separate private working copy. |
| Jupyter or notebook code reaches an external service. | The host must have no external default route. Jupyter and its kernels run under a macOS sandbox that allows only loopback network traffic. |
| Jupyter inherits local provider credentials or user configuration. | The process receives a minimal environment with no inherited API keys and separate empty Jupyter, IPython, cache, and configuration directories. The server root contains only the private working notebook. |
| Network access returns during the session. | An independent monitor freezes the state, terminates the Jupyter process group, and records `aborted`; it never silently resumes. A managed institutional network remains required for a real exam. |
| The learner believes the browser saved changes when it did not. | The local Jupyter adapter binds host, port, and fixed rehearsal URL path, then requires exactly one visible enabled save control. A different loopback tab and absent or ambiguous detection fail closed. It never reads notebook output. |
| Preparation or state persistence fails after process startup. | Partial rehearsal directories are removed; Jupyter and the network monitor are stopped before the error is returned. A second learning or rehearsal session is rejected before startup. |
| The contract or completion artifact is changed. | Contract, starting notebook, help report, network evidence, final file, and canonical notebook hashes are bound. `unibot rehearsal verify` rejects drift. |
| A receipt exposes learner work or device details. | `ExamSubmissionManifestV1` contains counts, timestamps, policy fields, and hashes only; no cell text, output, name, transcript, session secret, or local path. |
| Browser or Companion crashes. | Persisted state contains metadata only. A safe state may resume; inconsistent or network-unsafe state becomes `aborted`. |
| The local demonstration is presented as an approved examination. | Every contract and receipt carries `not_cleared`; there is no grading, proctoring, automatic submission, identity proof, or software-issued approval. |

The macOS sandbox is demonstration evidence, not a general endpoint-security
claim. Notebook code still runs with the signed-in macOS user's filesystem
rights. The rehearsal does not control another device, the physical
environment, an administrator, or software outside the isolated Jupyter process. A real
examination therefore needs a university-managed device, browser, network,
identity process, incident route, accessibility decision, and written human
approval.

## Security Boundary

A standard browser extension can support transparency and visible filtering, but
it cannot guarantee that every model response is intercepted before display. A
real exam-grade variant must use a controlled model gateway, managed browser, or
managed Jupyter environment where raw model output is unavailable until UniBot
has filtered it.

Mantle 2.1 is therefore a practice product. Native Messaging removes the
hard-coded loopback port but does not turn Colab into a controlled exam runtime.
The extension does not claim full capture. The voluntary report remains
private, formative, local-only by default and becomes shareable only through a
learner-triggered metadata export.

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
