# UniBot Source Cards

Checked on: 2026-06-13.

Each card gives a product rule for UniBot. Public documents may be cited in the
GitHub project; private course material, emails, health data, and local paths may
not.

## Release Review-Board Claim Alignment

The source-card layer carries `source_card_release_review_board_claim_alignment`
with the contract `unibot-source-card-release-review-board-claim-alignment-v1`.
It keeps public scientific, legal, privacy, technical, and pedagogical claims
anchored to public-link-only source IDs, product rules, drift checks, red-team
evidence, notebook handoff, publication package, release runbook, review-board
packet, bachelor thesis package, public-safety gate, and human submission gates.

Source cards do not approve publication, institutional submission, provider
calls, exam use, official grading, proctoring, or KI-detection claims. They are
a review substrate for human decisions.

## Legal And University Sources

| ID | Checked on | Relevanz | Risiko | Source | Product rule |
| --- | --- | --- | --- | --- | --- |
| `hg-nrw-2025` | 2026-06-13 | Exam governance in Köln/NRW context | high | [HG NRW, current 2025 version](https://recht.nrw.de/lrgv/gesetz/07052025-gesetz-ueber-die-hochschulen-des-landes-nordrhein-westfalen-hochschulgesetz-hg/) | Exam rules, disability accommodation, online exams, and data protection must remain authority-led; UniBot cannot self-approve an exam mode. |
| `hg-nrw-62b` | 2026-06-13 | Inclusion policy and institutional responsibility | high | HG NRW section 62b | Accommodation interests belong in the institutional disability/inclusion process; UniBot may document needs but not decide them. |
| `hg-nrw-64` | 2026-06-13 | Formal exam conduct and privacy constraints | high | HG NRW section 64 | Exam regulations must define assessment, procedure, breaches, and online-exam privacy; UniBot exam mode needs written fit with the applicable rules. |
| `uoc-ki-lehre` | 2026-06-13 | Teaching policy for generative AI | high | [University of Cologne generative AI in teaching](https://uni-koeln.de/studium-lehre/ki-in-der-bildung/wie-kann-ich-generative-ki-im-kontext-von-lehre-und-lernen-produktiv-anwenden) | KI use in teaching and exams must be transparent and tied to the applicable examination rules. |
| `uoc-hilfsmittel` | 2026-06-13 | Exam aid clarification and language constraints | high | [University of Cologne WiSo aids in exams](https://wiso.uni-koeln.de/de/fakultaet/dekanat/zentrale-fakultaetsverwaltung/pruefungsamt/rund-um-pruefungen/hilfsmittel) | Aids require explicit examiner or exam-board clearance; UniBot must not use clearance language without a real written basis. |
| `uoc-ki-faq` | 2026-06-13 | Exam restrictions for external KI | high | [University of Cologne KI FAQ](https://verwaltung.uni-koeln.de/stabsstelle02.1/content/faq/data/kuenstliche_intelligenz/index_ger.html) | A banned KI aid can be a cheating act; therefore exam mode blocks external KI unless written clearance exists. |
| `uoc-nachteilsausgleich` | 2026-06-13 | Accessibility and accommodation process | high | [University of Cologne Nachteilsausgleich](https://hf-studium.uni-koeln.de/studienorganisation/nachteilsausgleich) | Accommodation is individual and institutional; accessibility help in UniBot remains score-neutral and non-decisional. |
| `gdpr-2016-679` | 2026-06-13 | Data protection and lawful processing baseline | high | [GDPR, EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) | Apply lawfulness, transparency, purpose limitation, minimisation, security, and accountability. |
| `dsk-ai-privacy-2024` | 2026-06-13 | AI/privacy operational guidance | high | [DSK AI and data protection](https://www.datenschutzkonferenz-online.de/media/oh/20240506_DSK_Orientierungshilfe_KI_und_Datenschutz.pdf) | Prefer closed/controlled systems, define purpose, validate outputs, make logic transparent, and avoid unnecessary prompt histories. |
| `eu-ai-act-2024` | 2026-06-13 | EU AI governance and risk framing | high | [EU AI Act 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng) | Education evaluation, learning-outcome steering, and test-behaviour monitoring can become high-risk; UniBot keeps scores private and avoids proctoring. |
| `dfg-gwp` | 2026-06-13 | Research integrity and reproducibility requirements | medium | [DFG good research practice](https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/gwp) | Master-thesis work needs transparent methods, documentation, versioning, limits, and reproducible evidence. |

## Technical And Product Sources

| ID | Checked on | Relevanz | Risiko | Source | Product rule |
| --- | --- | --- | --- | --- | --- |
| `google-colab-gemini` | 2026-06-13 | External code-assistance behavior in practice layer | medium | [Colab Enterprise Gemini code help](https://docs.cloud.google.com/colab/docs/use-code-completion) | Gemini output can be plausible but wrong; UniBot must require validation and source checks. |
| `gemini-code-assist-validation` | 2026-06-15 | Vendor validation warning for code assistance | medium | [Gemini Code Assist overview](https://developers.google.com/gemini-code-assist/docs/overview) | Model output can be plausible but wrong; the simulation loop must validate and filter before use. |
| `openai-evals` | 2026-06-15 | Evaluation structure for LLM systems | medium | [OpenAI Evals guide](https://developers.openai.com/api/docs/guides/evals) | Use fixed scenarios, clear graders, and repeatable reports to test model-system behaviour. |
| `deepseek-chat-completion-api` | 2026-06-15 | DeepSeek-compatible student-agent interface | high | [DeepSeek Chat Completion API](https://api-docs.deepseek.com/api/create-chat-completion) | DeepSeek integration stays mock-first; live calls require explicit opt-in and redacted synthetic inputs. |
| `chrome-content-scripts` | 2026-06-13 | Overlay integration and DOM access model | medium | [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts) | Browser overlay can read/modify page DOM and pass messages, suitable for practice UX. |
| `chrome-webrequest-mv3` | 2026-06-13 | MV3 security boundary for exam usage | high | [Chrome WebRequest Manifest V3](https://developer.chrome.com/docs/extensions/reference/api/webRequest) | MV3 blocks most extensions from blocking network responses; overlay is not hard exam security. |
| `chrome-limited-use` | 2026-06-13 | Extension data-collection and disclosure constraints | medium | [Chrome Web Store Limited Use](https://developer.chrome.com/docs/webstore/program-policies/limited-use) | Extension data collection must be disclosed, limited to the visible purpose, and not over-collected. |
| `jupyter-ai` | 2026-06-13 | Controlled notebook route options | high | [Jupyter AI](https://github.com/jupyterlab/jupyter-ai) | Notebook-native AI tooling is feasible; a local/managed Jupyter route is better for controlled exam P2. |

## Research And Education Sources

| ID | Checked on | Relevanz | Risiko | Source | Product rule |
| --- | --- | --- | --- | --- | --- |
| `cs50-ai-2024` | 2026-06-13 | Course-scale AI tutor pattern | medium | [Teaching CS50 with AI](https://dl.acm.org/doi/10.1145/3626252.3630938) | Course-specific AI can scale support when built around teaching constraints and human oversight. |
| `vanlehn-2011` | 2026-06-13 | Pedagogical evidence for step-based tutoring | high | [Relative effectiveness of human tutoring systems](https://www.tandfonline.com/doi/abs/10.1080/00461520.2011.611369) | Step-based tutoring and feedback are stronger than answer delivery; UniBot should scaffold the next step. |
| `kulik-fletcher-2016` | 2026-06-13 | ITS outcome evidence and evaluation focus | medium | [ITS meta-analysis](https://journals.sagepub.com/doi/10.3102/0034654315581420) | Intelligent tutoring can improve learning, but evaluation must measure learning process outcomes. |
| `unesco-genai-2023` | 2026-06-13 | International principle alignment | medium | [UNESCO GenAI guidance](https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research) | Protect privacy, human agency, and pedagogical validation. |
| `oecd-digital-education-2026` | 2026-06-13 | Policy trend and educational deployment posture | medium | [OECD Digital Education Outlook 2026](https://www.oecd.org/en/publications/oecd-digital-education-outlook-2026_062a7394-en.html) | Avoid false mastery: external AI should scaffold cognitive work, not replace it. |
