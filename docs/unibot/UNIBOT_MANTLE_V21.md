# UniBot Mantle 2.1

Status: implemented public alpha, practice use only.

Implementation and documentation: Gretel, AI agent operating through the
Codex engineering runtime. GLM-5.2 did not contribute to this implementation
because the configured Z.AI account returned business code `1113` for
insufficient balance. Human merge and release review remain required.

## Learner Flow

1. Install `UniBot Companion.app` and its user-scoped Native Messaging host.
2. Load the fixed-ID Manifest V3 extension in Chrome.
3. Start a fixed or adaptive session with a declared maximum help level.
4. Select one Colab or Jupyter cell and describe the learner's own attempt.
5. Request A0-A4 help. Adaptive escalation moves one level at a time and needs
   a changed attempt plus explicit confirmation.
6. Preview and voluntarily export the metadata-only learning report.

## Help Contract

| Level | Allowed help | Cost for one task |
| --- | --- | ---: |
| A0 | Goal and next-step question | 0 |
| A1 | Error type or smallest diagnostic location | 0 |
| A2 | Concept cue, official source anchor, and one check | 5 |
| A3 | Formula structure, variable mapping, or pseudocode | 12 |
| A4 | Incomplete scaffold with blanks or analogous structure | 25 |

The task cost is the highest reached level, not the sum of repeated requests.
Escalation charges only the difference from the prior level. These values are
an assistance-exposure budget. They are not a percentage of authorship,
learning, or independent work.

## Data Flow

- Chrome sends the selected cell and learner attempt to the local Native Host.
- The deterministic tutor analyzes Python syntax, visible traceback terms,
  skill tags, local formula cards, and versioned official source anchors.
- Raw task, cell, attempt, and tutor transcript text are not persisted.
- The Companion writes only a hash-bound session contract, metadata event
  journal, and active/stopped state. A new Chrome panel can send
  `session.resume` and recover the active contract after a Companion restart.
- `session.delete` removes the contract, state, event journal, and associated
  sanitized notebook copy immediately. Ended sessions are cleaned after seven
  days; sanitized notebook copies are cleaned after 24 hours.
- A real local Jupyter process is represented only by a restricted process
  record. `gateway.status` and `gateway.stop` allow the Companion to recover or
  terminate that process after a Chrome restart; the Jupyter token is never
  written to the record. The notebook retention clock starts again when the
  gateway ends.
- The Sidepanel exposes semantic tab/panel relationships, live status regions,
  visible keyboard focus, and a tested narrow layout. The Playwright check is
  concrete browser evidence, not a claim of completed institutional WCAG
  certification; that review remains a human accessibility gate.
- The local JSONL record contains only hashes, levels, source IDs, timestamps,
  assistance points, and status. Files are owner-readable only.
- The voluntary report contains the pseudonym chosen for the session, contract
  hash, help profile, attempt count, source IDs, uncertainty, and report hash.
- No runtime learner content is sent to GLM, GitHub, Apple, or another provider.

## Transport And Installation

The extension ID is fixed by the public manifest key. The Mac installer writes
exact-origin manifests for Google Chrome and Chromium and creates an
ad-hoc-signed app in `~/Applications`. A Developer ID signature and Apple
notarization are still required before general binary distribution.

The extension does not use a hard-coded API port. The older paired HTTP API
remains available for development and one alpha compatibility cycle.

## Limits

- Colab is a learning surface. DOM changes may force manual text selection.
- A normal extension cannot prevent other tabs, external tools, copy/paste, or
  Colab network access and therefore cannot guarantee exam security.
- Captured code is parsed but never executed by the tutor.
- Notebook execution occurs only after the learner deliberately launches the
  token-protected local Jupyter gateway.
- Apple's on-device model is not enabled in the alpha. The deterministic tutor
  is the complete fallback and the release authority.
- Real exams remain `not_cleared` and require institutional, privacy, security,
  teaching, managed-browser, and controlled-network approval.

## Verification

- Unit and API tests cover immutable contracts, A0-A4 boundaries, adaptive
  escalation, privacy blocking, metadata-only storage, reports, and provider
  failure classification.
- The fixed scientific corpus contains 180 synthetic scenarios, with 30 each
  for allowed hints, assistance budget, source binding, solution leakage,
  privacy, and prompt injection.
- Playwright covers Jupyter cell capture without outputs, the full mocked
  side-panel workflow, and narrow widths.
- A headed package harness loads the real MV3 extension and verifies its stable
  ID and rendered side panel.
- The Native Messaging framing and installed launcher are tested separately.
  Playwright's bundled Chromium did not discover the user-installed host on the
  development Mac; this remains an explicit release canary for Google Chrome.
