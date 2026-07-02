# UniBot Course Material Staging

Status: local-only intake policy, not a public course repository.

The course-material layer is implemented in `unibot.materials` and exposed
through:

- `POST /api/unibot/materials/manifest`
- `POST /api/unibot/materials/public-summary`
- `POST /api/unibot/materials/validate`
- `POST /api/unibot/course/intake-scan`
- `POST /api/unibot/course/index/build`
- `GET/POST /api/unibot/course/exam-scope`
- `POST /api/unibot/tutor/respond`
- `POST /api/unibot/tutor/next-task`
- `POST /api/unibot/course/eval/run`

## Purpose

UniBot should eventually tutor from Python-course slides, notebooks, captions,
and exercises. Those files can be copyrighted, institution-specific, or linked
to private study context, so the default is staged-only and local.

For a local staging root, set `UNIBOT_COURSE_MATERIAL_ROOT` to the directory
that contains the course module or imported private course files. When set, the
course intake scan and command center use that root automatically; when unset,
UniBot falls back to its built-in private material tree.

## Required Metadata

Every material record needs:

- `material_id`
- `title`
- `source_kind`
- `permission_status`
- `publish_policy`
- `extraction_status`
- `review_status`
- `skill_tags`
- `source_card_ids`
- `page_or_timestamp`
- `sha256`

## Policy

Private course files can be used by the local tutor only after review and hash
evidence. Public release requires an explicit public policy, public-safe review,
and a public-safe excerpt or link-only summary.

The public summary excludes:

- source files
- local paths
- raw private course text
- student data
- exam data

## Readiness Rule

The readiness gate includes a course-material policy check. The demo manifest
must show that synthetic material can be public, while private course material
remains staged or private-only until it has explicit permission and review.

## Public Boundary Alignment

`build_demo_material_manifest()` includes a
`material_public_boundary_alignment` block. It maps four review sections:

- synthetic public demo material
- private course placeholder material
- public summary exclusions
- adaptive task public input

Each section names material IDs, public source-card IDs, readiness checks, and
human gates. The alignment is a review aid only. It does not permit publishing
private course files, local paths, raw course text, exam material, or student
data. Public release remains limited to metadata, hashes, source-card IDs, and
authorized public-safe synthetic excerpts.

## Course Tutor V1

The course tutor adds a source-card exam-scope map on top of the staging layer.
It scans local course files, classifies slides, notebooks, videos, captions,
scripts, data files, and documents, then groups them into exam-relevant skills
such as Jupyter/Colab, Python basics, pandas, boxplots, NumPy, statistics,
debugging, and machine learning.

Default behavior is conservative:

- unreviewed local files are candidates, not tutor evidence
- reviewed text/caption/notebook records can become local tutor anchors
- video files stay in the transcription queue until a rights/privacy decision
- PDFs, slide decks, and documents stay in the extraction queue until reviewed
- solution-key or exam-like names are quarantined from tutor use
- public summaries expose metadata, source-card IDs, hashes, and review status,
  not raw course text or local paths

The tutor response contract preserves the exam boundary:

- learning mode may explain, scaffold with synthetic examples, and ask next
  notebook tasks
- strict exam mode stays A0-A2 and blocks code fixes, inserted values, final
  interpretations, complete solutions, grading, proctoring, and AI detection
- every response includes a minimal Help-Ledger draft with source-card IDs,
  source reference IDs, help level, response hash, and human-review flags
