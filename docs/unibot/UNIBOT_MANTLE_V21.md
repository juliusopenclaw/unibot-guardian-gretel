# UniBot Mantle 2.1

Status: implemented public alpha, practice use only.

Implementation and documentation: Gretel, AI agent operating through the
Codex engineering runtime. GLM-5.2 did not contribute to this implementation
because the configured Z.AI account returned business code `1113` for
insufficient balance. Human merge and release review remain required.

## Learner Flow

1. Install `UniBot Companion.app` and its user-scoped Native Messaging host.
2. Load the fixed-ID Manifest V3 extension in Chrome.
3. Confirm the visible practice boundary: the session is voluntary practice,
   not an examination, and the contract records `practice_only`.
4. Start a fixed or adaptive session with a declared maximum help level.
5. Select one Colab or Jupyter cell and describe the learner's own attempt.
6. Request A0-A4 help. Adaptive escalation moves one level at a time and needs
   a changed attempt plus explicit confirmation.
7. End the session explicitly when the practice task is complete; the local
   report remains available until deletion, but further tutor turns are closed.
8. Optionally open one synthetic transfer task after the session ends. UniBot
   provides no help for this task, does not judge the answer, and records only
   a hash, character count, and status.
9. Preview and voluntarily export the metadata-only learning report.

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
- Each `tutor.turn` request must carry the active session-contract identifier.
  Missing or stale identifiers are rejected before the tutor records an event,
  so a closed or restarted Sidepanel cannot append help to another session.
- The session contract contains the immutable scope `practice_only`. The
  Sidepanel requires a visible learner confirmation of that scope before it
  sends `session.start`, and the local Companion rejects native start messages
  that omit the same confirmation. This is a boundary control, not a legal or
  examination approval.
- The compatible paired HTTP API requires the same explicit confirmation when
  creating `/api/v2/session/contracts` and rejects `/api/v2/socratic/help`
  until that practice session exists. The older direct practice route remains
  an alpha compatibility path and does not create an examination session.
- The deterministic tutor analyzes Python syntax, visible traceback terms,
  skill tags, local formula cards, and versioned official source anchors.
- Raw task, cell, attempt, and tutor transcript text are not persisted.
- The Companion writes only a hash-bound session contract, metadata event
  journal, and active/stopped state. A new Chrome panel can send
  `session.resume` and recover the active contract after a Companion restart.
- `session.delete` removes the contract, state, event journal, and associated
  sanitized notebook copy immediately. Ended sessions are cleaned after seven
  days; sanitized notebook copies are cleaned after 24 hours.
- `session.stop` is available in the Sidepanel as an explicit end action. It
  freezes the immutable session contract, keeps only the declared local
  metadata for the retention window, and prevents further tutor turns until a
  new session is created after deletion.
- The optional transfer task is exposed only after `session.stop`. The prompt
  is synthetic and public; it is not written to the session journal. A
  voluntary answer is checked for private-data markers before hashing. The
  report exposes only `recorded`/`not_started`, a prompt hash, an answer hash,
  character count, and timestamps. It contains no raw prompt or answer,
  correctness result, grade, authorship claim, or automatic learning outcome.
  The transfer task is evidence for a later scientific evaluation, not a
  student score.
- A real local Jupyter process is represented only by a restricted process
  record. `gateway.status` and `gateway.stop` allow the Companion to recover or
  terminate that process after a Chrome restart; the Jupyter token is never
  written to the record. Launch checks the requested loopback port before
  starting Jupyter and rejects an immediate process exit instead of reporting a
  false start. The notebook retention clock starts again when the gateway ends.
- The Sidepanel accepts either an allowlisted public HTTPS notebook URL or a
  learner-selected local `.ipynb` file. Chrome never provides a local path to
  the Companion. Local files are transferred as 32 KiB Native-Messaging
  chunks, with one active upload, a 10 MiB limit, a 60-second in-memory timeout,
  a path-free filename, and a SHA-256 check. The Companion validates and
  sanitizes the complete byte stream before writing the temporary practice
  copy; interrupted, invalid, or abandoned raw uploads are discarded.
- The content adapter reports a versioned adapter identifier for JupyterLab,
  Colab, or manual selection. If more than one different notebook cell appears
  active, the adapter returns low confidence and no source text; the Sidepanel
  requires an explicit learner selection instead of guessing. Notebook output
  is never part of the selection payload.
- The browser status banner is a labelled, polite status region with a visible
  `Ausblenden` action. Dismissing it removes only the visual notice; it does not
  stop the local session, change help limits, or create a learner profile.
- The Sidepanel exposes semantic tab/panel relationships, live status regions,
  visible keyboard focus, a tested narrow layout, and bounded automatic
  reconnection after a native-host restart. The Playwright check is
  concrete browser evidence, not a claim of completed institutional WCAG
  certification; that review remains a human accessibility gate.
- The header states two release boundaries in plain language: local practice
  can be ready while general distribution is still not approved. This is
  repeated after reconnecting so a technically healthy local Companion cannot
  be mistaken for a generally released or exam-approved product.
- Companion installation copies the public `unibot` package and its
  `exam_mode.py` dependency into a restricted local runtime under macOS
  Application Support. Native-host and app launchers point to that copy rather
  than the Git checkout, and an installation test verifies the import without
  the source tree. A signed/notarized bundled Python interpreter remains a
  separate human release gate.
- The local JSONL record contains only hashes, levels, source IDs, timestamps,
  assistance points, and status. Files are owner-readable only; the optional
  accessibility preference is not written to the record, and no reason,
  diagnosis, or accommodation status is recorded.
- The optional display preference is stored locally as one boolean so that a
  learner does not have to re-enable the larger controls after a Sidepanel
  restart. It is not a profile, is not sent to a provider, and can be switched
  off at any time.
- The voluntary report contains the pseudonym chosen for the session, contract
  hash, help profile, attempt count, source IDs, uncertainty, pseudonymous
  session metadata, and report hash. It does not contain use of the optional
  accessibility display preference; the display remains score-neutral and the
  report does not infer a need or decision.
  If the learner used the optional transfer task, it adds only the task ID,
  prompt/answer hashes, character count, status, and explicit
  `not_assessed`/`not_cleared` boundaries.
- No runtime learner content is sent to GLM, GitHub, Apple, or another provider.

## Transport And Installation

The extension ID is fixed by the public manifest key. The Mac installer writes
exact-origin manifests for Google Chrome and Chromium and creates an
ad-hoc-signed app in `~/Applications`. A Developer ID signature and Apple
notarization are still required before general binary distribution.
The Companion diagnosis and installation path fail closed when a native-host
manifest is symlinked, readable by other users, or points outside the
user-scoped UniBot Application Support runtime. This check is local and reports
only bounded status metadata.

For an institutional review, the public extension can be packaged without the
repository with:

```text
unibot extension package --output ./unibot-mantle.zip
```

The package contains only the Manifest V3 extension files, uses a fixed ZIP
timestamp for reproducibility, records a SHA-256 hash, and keeps the exam
deployment status `not_cleared`. It does not contain the Companion runtime,
learner data, notebooks, or private project files.

For a meeting with the Prüfungsamt, Inklusionsbüro, Datenschutz, IT/SZI, and
the teaching unit, the extension package and the public-safe institutional
review packet can be assembled locally with:

```text
unibot release candidate --output ./unibot-review-candidate
```

The resulting candidate contains the MV3 ZIP, the synthetic demonstration
notebook, the public demo, the institutional presentation and accessibility
materials, the structured and readable review-board packet, and manifests
binding their hashes to the clean public Git commit that produced them. The
builder refuses to create the handoff from a dirty working tree. It remains a
public-draft handoff only; it is not an exam approval, legal opinion,
accessibility certification, or automatic publication.

The extension does not use a hard-coded API port. The older paired HTTP API
remains available for development and one alpha compatibility cycle.

## Limits

- Colab is a learning surface. DOM changes may force manual text selection.
- The public live-Colab canary uses only the official synthetic Colab entry
  notebook and records adapter metadata, confidence, and bounded counts. If
  Colab exposes only read-only placeholders or no unambiguous editable cell,
  the canary must report `manual_selection_required`; it never stores source
  text or notebook output. It runs in headed Chromium so that the MV3 content
  script and service worker are exercised; headless rendering alone is not
  sufficient evidence. Run it with `npm run test:colab-canary`.
- A normal extension cannot prevent other tabs, external tools, copy/paste, or
  Colab network access and therefore cannot guarantee exam security.
- Captured code is parsed but never executed by the tutor.
- Notebook execution occurs only after the learner deliberately launches the
  token-protected local Jupyter gateway.
- Apple's on-device model is not enabled in the alpha. The deterministic tutor
  is the complete fallback and the release authority.
- Real exams remain `not_cleared` and require institutional, privacy, security,
  teaching, managed-browser, and controlled-network approval.

## Controlled synthetic rehearsal

The separate `synthetic_exam_rehearsal` scope demonstrates a stricter A0-A2
flow with the fixed public fixture. It requires the host to be offline, runs
local Jupyter under a loopback-only macOS sandbox, freezes the gateway before
export, and emits a metadata-only integrity receipt. The side panel can resume
the local metadata state after reconnection and never reads notebook output.

This is a controlled rehearsal for institutional review, not an exam mode.
Its status remains `not_cleared`; it provides no automatic submission,
grading, identity evidence, proctoring, or legal approval. The complete
contract and reproducible checks are in
`UNIBOT_CONTROLLED_EXAM_REHEARSAL_V1.md`.

## Verification

- Unit and API tests cover immutable contracts, A0-A4 boundaries, adaptive
  escalation, privacy blocking, metadata-only storage, reports, and provider
  failure classification.
- The fixed scientific corpus contains 180 synthetic scenarios, with 30 each
  for allowed hints, assistance budget, source binding, solution leakage,
  privacy, and prompt injection.
- Playwright covers Jupyter and Colab cell capture without outputs, the full
  mocked side-panel workflow, local notebook file selection through the
  chunked Native-Messaging protocol, and narrow widths.
- A headed package harness loads the real MV3 extension and verifies its stable
  ID and rendered side panel.
- On macOS, the release canary runs the installed Google Chrome binary with
  `UNIBOT_CHROME_EXECUTABLE=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome npm run test:chrome-canary`.
  Since Chrome 137, the branded browser no longer accepts the old
  `--load-extension` launch path. The harness therefore uses Chrome's
  explicitly enabled local DevTools extension-loading command, a fresh
  temporary browser profile, and a temporary copy of the already-installed
  Native Messaging manifest. The profile and copy are deleted after the run.
  A signed/managed Chrome package must keep the fixed public extension ID. An
  unpacked extension without a manifest key receives a temporary development
  ID; for that separate local-only case, the explicit pairing harness is
  `UNIBOT_CHROME_EXECUTABLE=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome npm run test:chrome-development-pairing`.
  It binds that temporary ID only for the canary and restores the fixed host
  manifest afterward. This remains a manual human release gate rather than a
  CI or institutional approval claim.
- The Native Messaging framing and installed launcher are tested separately.
  The real Google Chrome canary is the authoritative transport check for the
  installed Native Messaging host; bundled Chromium continues to use the
  deterministic browser harness and does not claim native transport.
- `unibot companion diagnose` and the native `companion.diagnose` message expose
  only boolean installation checks, signature state, and release boundaries.
  They never return learner content, notebook tokens, or local paths. `ready`
  means `ready_for_local_practice`; the explicit
  `distribution_status=blocked_human_release_gates` remains until a bundled
  Developer-ID interpreter, Developer-ID signature, Apple notarization, and
  human release review exist.
