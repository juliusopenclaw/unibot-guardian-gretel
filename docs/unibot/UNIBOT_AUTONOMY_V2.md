# UniBot Autonomy v2

Status: active public-safe development policy

## Roles

- Gretel is the AI implementation and documentation agent.
- GLM-5.2 produces a redacted proposal and an independent review.
- Julius or another named human reviewer owns merge, publication, ethics,
  legal assessment, and real university submission.

## Cycle

1. Select one `ready` product, research, or security work item.
2. Require a visible product or research delta, a hypothesis, at most four
   candidate files, and executable acceptance tests.
3. Build context only from selected public files already tracked by Git.
4. Run the public-safety scan before any provider call.
5. Request one structured GLM-5.2 proposal.
6. Gretel implements the bounded change in a `gretel/` branch and runs tests.
7. Request one structured independent GLM-5.2 review.
8. Open or update one draft pull request. A human remains the merge gate.

No ready product work means no provider call, no patch, and no commit.

Provider failures are classified before they reach the automation shell.
Insufficient balance or resource code `1113` is non-retryable for that run;
rate limits, timeouts, invalid JSON, and unknown SDK failures also stop without
repository changes, rollout credit, or public traceback content.

## Hard Limits

- Cadence: every six hours.
- One work item, four candidate files, two model calls, and two correction
  attempts per run.
- Maximum run time: 45 minutes.
- Maximum combined model context: 60,000 input and 8,192 output tokens.
- Monthly GLM budget: 20 USD.
- One open Gretel draft pull request at a time.
- No direct main-branch change and no autonomous merge.

## Provider Boundary

The provider scope is exactly `public-unibot-only`. The key is read from a
dedicated macOS Keychain item and is never stored in this repository, a dotenv
file, a prompt, a run artifact, or a log. GLM receives no tools and no raw
filesystem access.

Blocked context includes private course or exam material, learner records,
mailbox or calendar data, health or accommodation data, local paths,
credentials, raw external-model transcripts, and unrelated Gretel workspaces.

## Run Evidence

Local run summaries live in the ignored `.unibot` state directory. They contain
the work ID, model version, context and result hashes, token counts, estimated
cost, validation status, and human-review requirement. Raw prompts, raw private
context, automatic approval, and Final-Go are never recorded.

Short-lived automation clones set `UNIBOT_STATE_DIR` to one dedicated neutral
runtime directory. This preserves rollout counters and aggregate costs between
runs without writing generated state into iCloud, Git, or the public repository.

## Legacy Loop

`UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md` and
`unibot/autonomous_research_loop.py` remain available as frozen v1 compatibility
surfaces for one alpha cycle. They must not receive new receipt-tail, hash-tail,
or readiness-tail work. All new autonomous work uses this v2 policy and
`unibot/autonomy_work_items.json`.

## Mantle 2.1 Queue

The semantic-precision benchmark, Native companion hardening, live Colab
canary, and 180-scenario evaluation are complete and bound to the current
public release evidence. The optional local language-realizer benchmark
remains a `candidate`, not an executable order. While the open draft PR awaits
human review, the autonomy loop must remain inactive: it creates no new model
call, patch, receipt-only commit, or release decision. Learner notebook
content is outside the GLM provider scope in every stage.
