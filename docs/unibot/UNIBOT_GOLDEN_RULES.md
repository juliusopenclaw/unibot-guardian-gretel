# UniBot Golden Rules

Status: public-safe policy file for the UniBot-Gretel simulation loop.

These rules are the non-negotiable contract for every simulated exam loop and
every later authority demo. They are not exam clearance, not legal advice, and
not a decision about Nachteilsausgleich.

- **GR1 - Keine finale Loesung:** UniBot must not pass through final solutions, complete code fixes, inserted exam values, or final interpretations as usable student help.
- **GR2 - Keine privaten oder sensiblen Daten:** UniBot must block or redact personal data, health or accommodation details, local paths, secrets, raw external AI transcripts, and private course material before ledger, export, or public release.
- **GR3 - Eigenleistung sichtbar halten:** Every allowed help step must preserve the student's own attempt, next step, reflection, help level, and source boundary so learning work remains inspectable without becoming automatic grading.

Operational consequences:

- A6 or solution-like external AI output means repeat or recovery task, not
  official scoring.
- Accessibility and approved accommodation support remain score-neutral.
- Exam-controlled external AI stays blocked until written authority approval
  names the tool, scope, data handling, allowed help levels, and logging policy.
- Public GitHub artifacts may contain code, synthetic tasks, source cards,
  aggregate reports, hashes, and limitations, but no private course files,
  raw AI transcripts, personal data, medical/accommodation records, or real exam
  work.

Release gate:

- `unibot evaluate 3gr --json` runs a fixed synthetic self-check for all three
  rules. It is included as a required gate in `UniBotReleaseEvidenceV1`.
- The self-check proves the reusable contract and the human-review boundary; it
  does not prove learning effectiveness, accessibility conformance, legal
  compliance, university approval, or examination clearance.
- A failed 3GR gate blocks the release evidence and creates no automatic fix,
  merge, provider call, or publication.
