# Grassmarket API surface

**Generated 2026-09-03 from the live FastAPI app** (`create_app().openapi()`). **185 endpoints** across 27 tags.

This is the contract the front end is built against. Regenerate with `uv run python scripts/dump_api_surface.py`; the machine-readable spec is `docs/openapi.json`.

Every route except `/health*`, `/auth/*` and the shared-report links requires a bearer JWT, and every owned resource is filtered by `owner_consultant_id` in the repository layer (non-negotiable #9). A cross-owner read returns **404, never 403** — the existence of another advisor's record is never revealed.

## Retired routes — do not design against these

**15 of the routes below answer `410 Gone`.** They are listed because they still appear in the OpenAPI spec, so a design or a generated client will find them and assume they work. They do not.

Peer rating, Rating Committee sign-off and calibration were built for a network larger than this one. **The founder signs what goes out instead** (ADR-0041, GRS-0188). The machinery behind them — repository sections, tables, the kappa/AC1 stats engine — is intact and still unit-tested, so reversing this is re-mounting routers, not rebuilding the feature. **Confirmed staying off, 2026-09-03.**

What this means for a design: there is no blind/peer rating surface, no committee queue and no calibration session to build. `GET /queue` reports `rate` as a dormant kind, in words, for exactly this reason — see GRS-0253.

Each is marked **RETIRED** in the tables below.

| Method | Path |
|---|---|
| `GET` | `/assessments/rating-requests` |
| `GET` | `/assessments/{assessment_id}/committee` |
| `POST` | `/assessments/{assessment_id}/committee/decide` |
| `POST` | `/assessments/{assessment_id}/modules/{module_key}/consensus` |
| `GET` | `/assessments/{assessment_id}/modules/{module_key}/my-rating` |
| `PUT` | `/assessments/{assessment_id}/modules/{module_key}/my-rating` |
| `GET` | `/assessments/{assessment_id}/modules/{module_key}/ratings` |
| `GET` | `/calibration/sessions` |
| `POST` | `/calibration/sessions` |
| `GET` | `/calibration/sessions/{session_id}` |
| `POST` | `/calibration/sessions/{session_id}/close` |
| `GET` | `/calibration/sessions/{session_id}/my-rating` |
| `POST` | `/calibration/sessions/{session_id}/ratings` |
| `GET` | `/calibration/sessions/{session_id}/results` |
| `GET` | `/committee/queue` |

## Contents

- [arena](#arena) — 7
- [assessments](#assessments) — 18
- [auth](#auth) — 12
- [bench](#bench) — 2
- [calibration](#calibration) — 7
- [certification](#certification) — 8
- [client-report](#clientreport) — 3
- [committee](#committee) — 3
- [compliance](#compliance) — 3
- [consultants](#consultants) — 1
- [deliverables](#deliverables) — 5
- [documents](#documents) — 5
- [earnings](#earnings) — 11
- [entities](#entities) — 6
- [founder-review](#founderreview) — 7
- [guidance](#guidance) — 1
- [health](#health) — 2
- [narratives](#narratives) — 3
- [path-b](#pathb) — 9
- [pipeline](#pipeline) — 23
- [queue](#queue) — 1
- [registry](#registry) — 2
- [report-links](#reportlinks) — 4
- [shared-report](#sharedreport) — 2
- [validation](#validation) — 6
- [voice-notes](#voicenotes) — 5
- [workbench](#workbench) — 29


## arena

| Method | Path | What it does |
|---|---|---|
| `GET` | `/arena/scenarios` | List Scenarios |
| `POST` | `/arena/scenarios` | Create Scenario |
| `GET` | `/arena/scenarios/{scenario_id}` | Get Scenario |
| `POST` | `/arena/scenarios/{scenario_id}/sessions` | Start Session |
| `GET` | `/arena/sessions` | List Sessions |
| `GET` | `/arena/sessions/{session_id}` | Get Session |
| `POST` | `/arena/sessions/{session_id}/submit` | Submit Session |

## assessments

| Method | Path | What it does |
|---|---|---|
| `GET` | `/assessments` | List Assessments |
| `POST` | `/assessments` | Create Assessment |
| `GET` | `/assessments/for-entity/{entity_id}` | List Assessments For Entity |
| `GET` | `/assessments/portfolio` | Brokerage Portfolio |
| `GET` | `/assessments/rating-requests` | **RETIRED (410 Gone)** — My Rating Requests |
| `GET` | `/assessments/{assessment_id}` | Get Assessment |
| `PUT` | `/assessments/{assessment_id}` | Update Assessment |
| `POST` | `/assessments/{assessment_id}/finalise` | Finalise Assessment |
| `GET` | `/assessments/{assessment_id}/live-score` | Get Live Score |
| `POST` | `/assessments/{assessment_id}/modules/{module_key}/consensus` | **RETIRED (410 Gone)** — Resolve Module Consensus |
| `GET` | `/assessments/{assessment_id}/modules/{module_key}/my-rating` | **RETIRED (410 Gone)** — Get My Module Rating |
| `PUT` | `/assessments/{assessment_id}/modules/{module_key}/my-rating` | **RETIRED (410 Gone)** — Update My Module Rating |
| `POST` | `/assessments/{assessment_id}/modules/{module_key}/my-rating/submit` | Submit My Module Rating |
| `POST` | `/assessments/{assessment_id}/modules/{module_key}/raters` | Assign Rater |
| `GET` | `/assessments/{assessment_id}/modules/{module_key}/ratings` | **RETIRED (410 Gone)** — List Module Ratings |
| `POST` | `/assessments/{assessment_id}/scenarios` | Evaluate Assessment Scenarios |
| `GET` | `/assessments/{assessment_id}/sell-opportunities` | Get Sell Opportunities |
| `GET` | `/assessments/{assessment_id}/suggestions` | Get Wizard Suggestions |

## auth

| Method | Path | What it does |
|---|---|---|
| `POST` | `/auth/accept-invitation` | Accept Invitation |
| `DELETE` | `/auth/act-as` | Stop Act As |
| `GET` | `/auth/act-as/candidates` | Act As Candidates |
| `POST` | `/auth/act-as/{consultant_id}` | Start Act As |
| `POST` | `/auth/change-password` | Change Password |
| `GET` | `/auth/google/callback` | Google Callback |
| `GET` | `/auth/google/start` | Google Start |
| `POST` | `/auth/invitations` | Create Invitation |
| `POST` | `/auth/login` | Login |
| `GET` | `/auth/me` | Me |
| `POST` | `/auth/refresh` | Refresh |
| `POST` | `/auth/session/exchange` | Exchange Session |

## bench

| Method | Path | What it does |
|---|---|---|
| `GET` | `/bench/performance/{advisor_id}` | Get Performance |
| `GET` | `/bench/queue` | Get Queue |

## calibration

| Method | Path | What it does |
|---|---|---|
| `GET` | `/calibration/sessions` | **RETIRED (410 Gone)** — List Sessions |
| `POST` | `/calibration/sessions` | **RETIRED (410 Gone)** — Create Session |
| `GET` | `/calibration/sessions/{session_id}` | **RETIRED (410 Gone)** — Get Session |
| `POST` | `/calibration/sessions/{session_id}/close` | **RETIRED (410 Gone)** — Close Session |
| `GET` | `/calibration/sessions/{session_id}/my-rating` | **RETIRED (410 Gone)** — Get My Rating |
| `POST` | `/calibration/sessions/{session_id}/ratings` | **RETIRED (410 Gone)** — Submit Rating |
| `GET` | `/calibration/sessions/{session_id}/results` | **RETIRED (410 Gone)** — Get Results |

## certification

| Method | Path | What it does |
|---|---|---|
| `GET` | `/certification/{advisor_id}` | Get Record |
| `POST` | `/certification/{advisor_id}/coursework` | Record Coursework |
| `GET` | `/certification/{advisor_id}/events` | List Events |
| `POST` | `/certification/{advisor_id}/exam` | Record Exam |
| `POST` | `/certification/{advisor_id}/observed-lead` | Log Observed Lead |
| `POST` | `/certification/{advisor_id}/promote` | Promote |
| `POST` | `/certification/{advisor_id}/shadow` | Log Shadow |
| `POST` | `/certification/{advisor_id}/signoff` | Record Signoff |

## client-report

| Method | Path | What it does |
|---|---|---|
| `GET` | `/deliverables/{deliverable_id}/client-report.pdf` | Download Client Report |
| `GET` | `/deliverables/{deliverable_id}/report-prose` | Get Report Prose |
| `PUT` | `/deliverables/{deliverable_id}/report-prose` | Save Report Prose |

## committee

| Method | Path | What it does |
|---|---|---|
| `GET` | `/assessments/{assessment_id}/committee` | **RETIRED (410 Gone)** — Committee Queue |
| `POST` | `/assessments/{assessment_id}/committee/decide` | **RETIRED (410 Gone)** — Decide Committee Item |
| `GET` | `/committee/queue` | **RETIRED (410 Gone)** — Committee Work Queue |

## compliance

| Method | Path | What it does |
|---|---|---|
| `GET` | `/compliance/audit` | Audit Log |
| `GET` | `/compliance/personal-data/{advisor_id}` | Export Personal Data |
| `POST` | `/compliance/personal-data/{advisor_id}/delete` | Delete Personal Data |

## consultants

| Method | Path | What it does |
|---|---|---|
| `GET` | `/consultants/by-email` | Lookup By Email |

## deliverables

| Method | Path | What it does |
|---|---|---|
| `GET` | `/assessments/{assessment_id}/deliverable-preview` | Preview Assessment Deliverable |
| `GET` | `/deliverables` | List All Deliverables |
| `GET` | `/deliverables/{deliverable_id}/download` | Download Deliverable |
| `GET` | `/engagements/{engagement_id}/deliverables` | List Deliverables |
| `POST` | `/engagements/{engagement_id}/deliverables` | Generate Deliverable |

## documents

| Method | Path | What it does |
|---|---|---|
| `GET` | `/documents` | List Documents |
| `POST` | `/documents` | Upload Document |
| `GET` | `/documents/{document_id}` | Get Document |
| `GET` | `/documents/{document_id}/content` | Download Document |
| `POST` | `/documents/{document_id}/engagement/{engagement_id}` | Attach To Engagement |

## earnings

| Method | Path | What it does |
|---|---|---|
| `GET` | `/earnings/commissions` | List Commissions |
| `POST` | `/earnings/commissions/consultancy` | Record Consultancy Commission |
| `POST` | `/earnings/commissions/product` | Record Product Commission |
| `POST` | `/earnings/commissions/{line_id}/client-paid` | Record Client Paid |
| `POST` | `/earnings/commissions/{line_id}/payment` | Advance Payment |
| `GET` | `/earnings/consultancy-commissions` | List Consultancy Commissions |
| `GET` | `/earnings/product-commissions` | List Product Commissions |
| `POST` | `/earnings/recovery-fees/{attribution_id}/claim` | Claim Recovery Fee |
| `GET` | `/earnings/statement` | Download Statement |
| `GET` | `/earnings/summary` | Get Summary |
| `GET` | `/earnings/timeline` | Get Timeline |

## entities

| Method | Path | What it does |
|---|---|---|
| `GET` | `/entities` | List Registry Targets |
| `GET` | `/entities/facets` | Registry Facets |
| `GET` | `/entities/search` | Search Entities |
| `GET` | `/entities/{entity_id}` | Get Entity |
| `GET` | `/entities/{target_id}/contacts` | List Registry Contacts |
| `POST` | `/entities/{target_id}/influencer-map` | Generate Influencer Map For Target |

## founder-review

| Method | Path | What it does |
|---|---|---|
| `GET` | `/assessments/{assessment_id}/founder-approval` | Current Approval |
| `POST` | `/assessments/{assessment_id}/founder-approval` | Approve Current Version |
| `POST` | `/assessments/{assessment_id}/submit-for-review` | Submit For Review |
| `GET` | `/deliverables/{deliverable_id}/report-approval` | Current Report Approval |
| `POST` | `/deliverables/{deliverable_id}/report-approval` | Approve Report |
| `POST` | `/deliverables/{deliverable_id}/submit-report-for-review` | Submit Report For Review |
| `GET` | `/founder-review/queue` | Review Queue |

## guidance

| Method | Path | What it does |
|---|---|---|
| `GET` | `/guidance/subcomponents/{subcomponent_key}` | Subcomponent Guidance |

## health

| Method | Path | What it does |
|---|---|---|
| `GET` | `/health` | Health |
| `GET` | `/health/ready` | Ready |

## narratives

| Method | Path | What it does |
|---|---|---|
| `GET` | `/deliverables/{deliverable_id}/narratives` | List Narratives |
| `POST` | `/deliverables/{deliverable_id}/narratives` | Propose Narratives |
| `POST` | `/narratives/{narrative_id}/approve` | Approve Narrative |

## path-b

| Method | Path | What it does |
|---|---|---|
| `POST` | `/extractions` | Propose Extraction |
| `GET` | `/extractions/{extraction_id}` | Get Extraction |
| `POST` | `/extractions/{extraction_id}/confirm` | Confirm Extraction |
| `GET` | `/extractions/{extraction_id}/provenance` | List Provenance |
| `GET` | `/transcripts` | List Transcripts |
| `GET` | `/transcripts/consent-line` | Get Consent Line |
| `POST` | `/transcripts/media` | Ingest Media |
| `POST` | `/transcripts/text` | Ingest Text |
| `GET` | `/transcripts/{transcript_id}` | Get Transcript |

## pipeline

| Method | Path | What it does |
|---|---|---|
| `GET` | `/engagements` | List Engagements |
| `POST` | `/engagements` | Create Engagement |
| `GET` | `/engagements/{engagement_id}` | Get Engagement |
| `POST` | `/engagements/{engagement_id}/assessments` | Link Assessment |
| `POST` | `/engagements/{engagement_id}/comms` | Append Comms Entry |
| `GET` | `/pipeline/board` | Get Board |
| `GET` | `/pipeline/forecast` | Get Forecast |
| `GET` | `/prospects` | List Prospects |
| `POST` | `/prospects` | Create Prospect |
| `GET` | `/prospects/{prospect_id}` | Get Prospect |
| `PATCH` | `/prospects/{prospect_id}` | Update Prospect |
| `GET` | `/prospects/{prospect_id}/contacts` | List Contacts |
| `POST` | `/prospects/{prospect_id}/contacts` | Create Contact |
| `DELETE` | `/prospects/{prospect_id}/contacts/{contact_id}` | Delete Contact |
| `PATCH` | `/prospects/{prospect_id}/contacts/{contact_id}` | Update Contact |
| `GET` | `/prospects/{prospect_id}/history` | Prospect Stage History |
| `PATCH` | `/prospects/{prospect_id}/stage` | Update Stage |
| `GET` | `/recovery-fees` | List Recovery Fees |
| `GET` | `/workshops` | List Workshops |
| `POST` | `/workshops` | Create Workshop |
| `GET` | `/workshops/{workshop_id}` | Get Workshop |
| `POST` | `/workshops/{workshop_id}/deliver` | Deliver Workshop |
| `POST` | `/workshops/{workshop_id}/recovery-fee` | Attribute Recovery Fee |

## queue

| Method | Path | What it does |
|---|---|---|
| `GET` | `/queue` | Needs You Queue |

## registry

| Method | Path | What it does |
|---|---|---|
| `GET` | `/registry` | Get Registry |
| `GET` | `/registry/profiles` | List Profiles |

## report-links

| Method | Path | What it does |
|---|---|---|
| `GET` | `/deliverables/{deliverable_id}/links` | List Links |
| `POST` | `/deliverables/{deliverable_id}/links` | Create Link |
| `GET` | `/report-links/{link_id}/reads` | Read Summary |
| `POST` | `/report-links/{link_id}/revoke` | Revoke Link |

## shared-report

| Method | Path | What it does |
|---|---|---|
| `GET` | `/shared/report/{token}` | Read Shared Report |
| `POST` | `/shared/report/{token}/events` | Record Read Event |

## validation

| Method | Path | What it does |
|---|---|---|
| `GET` | `/benchmark` | List Benchmark |
| `POST` | `/benchmark/ingest` | Ingest |
| `GET` | `/predictions` | List Predictions |
| `POST` | `/predictions` | Register |
| `GET` | `/predictions/follow-ups/due` | Due Follow Ups |
| `POST` | `/predictions/{prediction_id}/realise` | Realise |

## voice-notes

| Method | Path | What it does |
|---|---|---|
| `GET` | `/voice-notes` | List Proposals |
| `POST` | `/voice-notes` | Propose |
| `GET` | `/voice-notes/{proposal_id}` | Get Proposal |
| `POST` | `/voice-notes/{proposal_id}/confirm` | Confirm |
| `POST` | `/voice-notes/{proposal_id}/discard` | Discard |

## workbench

| Method | Path | What it does |
|---|---|---|
| `GET` | `/workbench/certifications/course` | List My Course Certifications |
| `POST` | `/workbench/certifications/course/signoff` | Signoff Course Certification |
| `GET` | `/workbench/courses` | List Courses |
| `POST` | `/workbench/courses` | Create Course |
| `GET` | `/workbench/courses/published` | List Published Courses |
| `GET` | `/workbench/courses/{slug}` | Get Course |
| `GET` | `/workbench/courses/{slug}/completions` | List Lesson Completions |
| `PUT` | `/workbench/courses/{slug}/draft` | Save Course Draft |
| `POST` | `/workbench/courses/{slug}/lessons/{lesson_id}/approve` | Approve Course Lesson |
| `GET` | `/workbench/courses/{slug}/lessons/{lesson_id}/checkpoints` | Get Checkpoint Progress |
| `POST` | `/workbench/courses/{slug}/lessons/{lesson_id}/checkpoints/{slide_order}` | Confirm Checkpoint |
| `POST` | `/workbench/courses/{slug}/lessons/{lesson_id}/complete` | Complete Lesson |
| `POST` | `/workbench/courses/{slug}/publish` | Publish Course |
| `GET` | `/workbench/courses/{slug}/published` | Get Published Course |
| `GET` | `/workbench/courses/{slug}/section-progress` | Section Progress |
| `POST` | `/workbench/courses/{slug}/sections/{module_id}/test` | Attempt Section Test |
| `GET` | `/workbench/courses/{slug}/versions` | List Course Versions |
| `GET` | `/workbench/drills/cards` | List Drill Cards |
| `POST` | `/workbench/drills/cards` | Create Drill Card |
| `GET` | `/workbench/drills/cards/due` | List Due Drill Cards |
| `POST` | `/workbench/drills/cards/{card_id}/answer` | Answer Drill Card |
| `GET` | `/workbench/learning/modules` | List Learning Modules |
| `POST` | `/workbench/learning/modules` | Create Learning Module |
| `POST` | `/workbench/learning/modules/{module_id}/complete` | Complete Learning Module |
| `GET` | `/workbench/quizzes` | List Quizzes |
| `POST` | `/workbench/quizzes` | Propose Quiz |
| `GET` | `/workbench/quizzes/{quiz_id}` | Get Quiz |
| `POST` | `/workbench/quizzes/{quiz_id}/approve` | Approve Quiz |
| `POST` | `/workbench/quizzes/{quiz_id}/reject` | Reject Quiz |
