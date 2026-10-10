# Implementation plan: D1 diagnostic odyssey

Status: plan only. No application file in this tree is created by this document. The paths below are the tree to create when building is approved.

Owner: Ashish Kumar, working alone, in India, on free tiers, with no clinician and no counsellor available. Time figures in section G are planning estimates. They are not measurements and not a promise. Regulatory sentences are a reading of the notes dated 10 October 2026 and of pages opened on that date or on 10 October 2026 in this session. They are not legal advice.

Two tracks:

| Track | Who can use it | What it does | Where it runs |
| --- | --- | --- | --- |
| Safe core | Later: a patient, caregiver, or advocate, on their own computer. Until the open questions in section G are answered, only Ashish, and only synthetic cases. | Timeline, confirmed HPO, typed lab-reported variant, on-device change match, template PDF. | Laptop Compose. Synthetic demo may point Postgres at Neon. |
| Experimental | Not a real user. Ashish, on synthetic or public files, and only after he sets the local flag. | Local VCF in, unmodified Exomiser and LIRICAL, tool JSON out, calibration note from published cases. | A second Compose file. Localhost only. Never Neon. |

## A. File and folder tree

One monorepo. TypeScript for the browser, Python for the API and the jobs, SQL for the gate. Generated directories (`node_modules`, `.venv`, `.next`, `__pycache__`, `*.egg-info`) are not source and are not listed. Lockfiles (`uv.lock`, `package-lock.json`) appear when the tools are first run.

```
.
├── README.md                          # What the two tracks are, and that nothing here diagnoses
├── PLAN.md                            # Evidence design and the two-track decision
├── Makefile                           # One target per step; no second task runner
├── compose.yaml                       # Safe core only: web, api, postgres
├── compose.experimental.yaml          # Genome container and literature service; not merged into compose.yaml
├── .env.example                       # Names of variables, empty values, comments on which track reads them
├── .gitignore                         # Includes .env, data/, exomiser volume dumps, ALLOW_LOCAL
├── docs/
│   ├── IMPLEMENTATION.md              # This file
│   ├── search-log.md                  # Counts of lookups actually run
│   ├── review.md                      # Correlator critic pass
│   └── templates.md                   # Index of every safe-core sentence id and its slots
├── apps/web/                          # Next.js, TypeScript, Tailwind, shadcn
│   ├── Dockerfile                     # Multi-stage build of the notebook UI
│   ├── package.json                   # Web dependencies only
│   ├── tsconfig.json                  # Strict TypeScript
│   ├── next.config.ts                 # No experimental rewrite to the genome port
│   ├── app/layout.tsx                 # Footer: not for emergencies; not a diagnosis
│   ├── app/page.tsx                   # Case list, empty and error states
│   ├── app/cases/[id]/timeline/page.tsx    # Timeline, newest first
│   ├── app/cases/[id]/symptoms/page.tsx    # Propose, then Yes / No / Not sure
│   ├── app/cases/[id]/variant/page.tsx     # Typed lab fields, no class of our own
│   ├── app/cases/[id]/changes/page.tsx     # What the public file said, and when
│   ├── app/cases/[id]/summary/page.tsx     # Preview of the PDF slots before export
│   ├── app/consent/page.tsx           # First-run screens, nothing pre-ticked
│   ├── app/emergency/page.tsx         # Stop screen when a red-flag phrase matches
│   └── components/ui/                 # shadcn primitives actually imported (button, input, table, badge)
├── services/api/                      # FastAPI, safe core only
│   ├── Dockerfile                     # python:3.12-slim, no Java, no VCF parser
│   ├── pyproject.toml                 # API dependencies; does not depend on the genome package
│   ├── app/main.py                    # Routes for records, drafts, summary, export
│   ├── app/session.py                 # Sets app.reviewer from the local session, then calls the function
│   ├── app/drafts.py                  # Inserts pending drafts; cannot insert observations
│   ├── app/summary.py                 # Fills a template id; refuses a slot that is not in the schema
│   ├── app/pdf.py                     # Renders the filled template to a one-to-two-page PDF
│   ├── app/export.py                  # Optional Phenopacket JSON and a disk FHIR Bundle, no Condition
│   ├── app/redflag.py                 # Fixed phrase list; match shows the stop screen
│   └── app/changes.py                 # Reads a downloaded change-list file; match is local
├── services/literature/               # The only A2A process
│   ├── Dockerfile                     # python:3.12-slim; NCBI key from the environment only
│   ├── pyproject.toml                 # A2A SDK and an HTTP client for NCBI
│   ├── agent.py                       # A2A server: gene symbol and HPO ids in, quoted passage out
│   └── card.json                      # Agent card: no clinical claim, no patient endpoint
├── services/genome/                   # Experimental track only
│   ├── Dockerfile                     # JRE base named by the pinned Exomiser release; data not copied in
│   ├── pyproject.toml                 # Thin wrapper; does not import services/api
│   ├── entrypoint.py                  # Exits unless the local flag is set and the bind address is loopback
│   ├── exomiser_adapter.py            # Shells out to the unmodified Exomiser CLI; parses its TSV
│   ├── lirical_adapter.py             # Shells out to the unmodified LIRICAL CLI; parses its JSON
│   └── banner.txt                     # Fixed banner prepended to every experimental result file
├── packages/contracts/                # The only shared types
│   ├── pyproject.toml                 # No I/O, no FastAPI, no Java
│   └── d1_contracts/
│       ├── __init__.py                # Re-exports the models
│       ├── drafts.py                  # Draft, AcceptedFact, Decision
│       ├── safe_card.py               # TemplateId plus slots; no free-text field
│       ├── experimental.py            # ToolRequest, ToolResult; not a subtype of SafeCard
│       └── ports.py                   # Source, Matcher, Tool protocols
├── packages/correlator/               # Pure functions used by evaluation and by the experimental adapter
│   ├── pyproject.toml                 # Imports contracts only
│   └── d1_correlator/
│       ├── overlap.py                 # Count of confirmed HPO terms on an Orphanet feature list
│       ├── frequency.py               # Bin-bound likelihood for the evaluation harness, not the PDF
│       ├── holdout.py                 # Strips gene symbols before a phenotype-only score
│       └── abstain.py                 # Frozen “too general” rule
├── packages/templates/                # The sentence library
│   ├── sentences.toml                 # Every safe-core sentence, with slot types
│   └── forbidden.txt                  # Phrases that fail the build if they appear in sentences.toml
├── packages/kb/                       # Builds the read-only knowledge file
│   ├── build.py                       # HPO, Orphadata, ClinGen slice to one SQLite file
│   └── schema.sql                     # Tables for terms, features, gene links, validity rows
├── eval/
│   ├── pins.toml                      # Store version, k=1 and k=5, abstention constants, LOINC pin if used
│   ├── synthetic/cases.yaml           # Five hand-written cases
│   ├── test_gate.py                   # Hash, double apply, revoked execute, pending row
│   ├── test_templates.py              # Forbidden-phrase scan
│   ├── test_boundary.py               # Safe core does not import services.genome or render ToolResult
│   ├── test_overlap.py                # Known-answer overlap on a tiny fixture
│   └── test_experimental_flag.py      # Entrypoint exits when the flag is missing
├── sql/
│   ├── 001_roles.sql                  # NOLOGIN owner, NOINHERIT api role, grants, revoke public execute
│   ├── 002_gate.sql                   # draft, decision, observation, snapshot; apply_decision
│   ├── 003_span.sql                   # Quote must be a substring of the note
│   └── 004_synthetic_check.sql        # Host-agnostic check that a demo role cannot insert synthetic=false
├── jobs/
│   └── clinvar_diff.py                # Streams two monthly variant_summary files; writes a public change list
└── infra/terraform/                   # Sketch only. Not applied. No genome resource.
    ├── versions.tf                    # Provider pins, when a host is ever chosen
    ├── variables.tf                   # database_url and image tags; no NCBI key; no VCF bucket
    ├── demo.tf                        # Optional later VM for the synthetic demo only
    └── README.md                      # Says apply is a separate decision and real records are out of scope
```

`services/api` does not depend on `services/genome`. `apps/web` has no client for port 8090 (the experimental port). A test fails if either dependency appears.

## B. What stays small

### Do not build

| Not built | Why |
| --- | --- |
| A variant caller, an ACMG worksheet, or a reimplementation of Exomiser or LIRICAL | The experimental track runs those tools unchanged. Copying them would be a second ranker and an AGPL or Jackson Laboratory licence problem. |
| LangGraph, an agent gate, MCP, a vector database, assistant-ui | The writer is `apply_decision`. Lookups are Python functions. The literature service is A2A because it holds a foreign key, not because the notebook needs a protocol. |
| Model prose on any safe-core screen | Gemini’s unpaid terms, as read for the 10 October note, say not to submit personal information and not to use the service for medical advice. The model writes synthetic fixtures only. |
| NHANES alarms, ClinPGx dose quotes, and a likelihood number on the patient screen | A person with no clinician will read them as a result. Medications and lab values can sit on the timeline as accepted facts. The frequency-bin math stays in `packages/correlator` for the harness. |
| A conditions list turned on by default | The 10 October note leaves it behind a setting, off, sorted by overlap count, with the sentence that the order is not a likelihood. The notebook works with the setting off. |
| Matchmaker Exchange, GeneMatcher API calls, trial-eligibility text | Links only, with the query string visible. The word “eligible” is in `forbidden.txt`. |
| Image, voice, wearable, methylation, and polygenic-score pipelines | No reference this repo can commit, and image analysis is a different regulatory object. |
| A hosted database of real charts | Neon’s free plan has no HIPAA agreement. See section E. |
| A second audit table, a plugin loader, an event bus | The decision row is the audit. One pipeline module is enough until a third source exists. |
| i18n, a multi-patient dashboard, growth charts, scanned-PDF OCR | Later, and only after the safe core’s tests are green. OCR quality on real reports is UNCLEAR. |

### Reuse unchanged

| Piece | How it is used | Licence note |
| --- | --- | --- |
| Postgres | Compose locally; Neon only for synthetic demo rows | — |
| FastAPI, Pydantic, Next.js, shadcn | Application shell | Their own licences; not re-read this session |
| HPO obo, Orphadata Science, ClinGen curated labels, ClinVar monthly `variant_summary` | Downloaded into the knowledge file or the change-list job. Not committed. | HPO: use unmodified, cite, show version; the canonical IRI 404’d in an earlier pass. Orphadata Science: CC BY 4.0 in the earlier pass. ClinGen labels: CC0 with a requested access date, earlier pass. ClinVar: NCBI’s policy page was opened for the 10 October note (no restriction on NCBI molecular data; some submitters may claim rights; show NCBI’s notice). This session did not re-download the files. |
| Exomiser CLI | Downloaded in the experimental volume at the version pinned in `pins.toml`. Not copied into git. Not baked into the image. | Code: AGPL-3.0, GitHub licence file opened this session (`exomiser/Exomiser` LICENCE is the Affero GPL v3 text). Data bundle: the install page tells the operator to download it. This session did not re-read every file’s notice inside the zip. The earlier plan said the bundle includes OMIM. Do not commit it and do not publish an image that contains it. Whether every file in the zip allows a solo local run is UNCLEAR until those notices are read. |
| LIRICAL CLI | Same pattern. Prebuilt zip from its releases. Not rebuilt, so this repo does not compile a derivative. | GitHub marks the licence “Other”. The licence file’s grant, as returned in search this session, is worldwide, royalty-free, non-exclusive, non-transferable, non-sublicensable, non-commercial. The rest of that file was not read. UNCLEAR beyond that grant. |
| shadcn components | Copy only the primitives the screens import | — |

### Line-count budget

Ceilings, chosen so a solo builder deletes scope instead of splitting files. They are not measurements. A module that crosses its ceiling by more than a fifth, without a one-line reason added to this file, loses a feature instead of gaining a helper.

| Module | Ceiling (lines) |
| --- | ---: |
| `packages/contracts` | 350 |
| `packages/correlator` | 700 |
| `packages/templates` (`sentences.toml` plus the loader) | 500 |
| `packages/kb/build.py` | 250 |
| `services/api` (all Python) | 1,200 |
| `services/literature` | 350 |
| `services/genome` (wrapper only; upstream tools count as zero) | 450 |
| `apps/web` (TSX, excluding `components/ui`) | 1,400 |
| `sql/` | 350 |
| `eval/` | 800 |
| `jobs/clinvar_diff.py` | 200 |

### Deleting rather than adding

Before a new file is added, name the file it replaces. If it replaces nothing, it is not added. In particular: do not add a safe-core renderer for `ToolResult`; do not add a third Compose file; do not add a Python ranker “so the experimental track works offline without the 80 GB download.” That download is the cost of running the real tool. A fake ranker would only exercise plumbing and would be labelled as such if it ever existed, which it should not.

## C. Abstraction

### Shared packages

`packages/contracts` is the only package both tracks import. It has no database driver and no HTTP client.

`packages/correlator` is pure. The evaluation harness imports it. The experimental adapter may attach a correlator overlap count next to a tool result, inside `ToolResult`, for the methods page. The safe-core PDF renderer imports `SafeCard` only.

`packages/templates` is data. The API loads it. The web app does not contain a copy of the sentences.

### Ports

```text
Source.propose(note) -> list[Draft]
Matcher.apply(accepted, public_file) -> list[Draft]     # change list; still a draft until the user confirms
Tool.run(request) -> ToolResult                         # experimental only
```

Adapters in the safe core: dictionary HPO source, typed-variant form, change-list matcher. Adapters in the genome container: Exomiser, LIRICAL. Each adapter is one file. There is no registry and no entry-point scan. Wiring is a dict in `services/api/app/main.py` for the safe sources and a dict in `services/genome/entrypoint.py` for the tools.

### One pipeline contract

A draft body is canonical JSON (UTF-8, NFC, sorted keys, no whitespace). The database trigger hashes it. Slots in a `SafeCard` are typed: an HPO id, a date, a short quote, an integer count, a source version. The renderer rejects an unknown slot and rejects a string that is not one of those types. `ToolResult` has `tool_name`, `tool_version`, `argv` with secrets redacted, and `raw_path` pointing at the tool’s file on the local volume. It has no method `to_safe_card`.

Uniform targets, all in the `Makefile`:

| Target | What it does |
| --- | --- |
| `make kb` | Builds the SQLite knowledge file under `./data` (gitignored) |
| `make demo` | `docker compose up` for the safe core |
| `make test` | Gate tests, template scan, import boundary, five synthetic cases |
| `make change-list` | Local diff of two pinned ClinVar monthly files |
| `make eval-store` | Phenopacket Store run; not used in the default CI job |
| `make literature` | Starts only the literature container |
| `make experimental` | Refuses unless the local flag file exists; then the second Compose file |

### Where a shared interface would be a lie

- One `Score` type for “three of your symptoms are on the list” and for Exomiser’s rank. They are different objects. The first is a `SafeCard`. The second is a `ToolResult`.
- An `Agent` port. Nothing in the safe core chooses a next action.
- MCP as the port. The caller is this repo. A protocol with no outside client is a second API.
- A plugin discovered from the filesystem. Two tools, both known, both in one container. A loader hides the import-boundary test.
- LangGraph as the wait-for-user step. The wait is a `pending` row. A graph pause double-applied a write in the earlier integrated-plan exercise.

A2A stops at the literature container. The genome container is not an agent. It is a CLI wrapper.

## D. Containers

One Dockerfile per service, as listed in section A. No Dockerfile at the repo root.

| Image | Base | What is in the image | What is a volume |
| --- | --- | --- | --- |
| `api` | `python:3.12-slim` | Application code and wheels | `./data/kb.sqlite` (read-only), `./data/cases` for uploaded PDFs in local mode |
| `web` | `node:22-alpine`, then a small runtime stage | Built Next.js app | None for health data |
| `literature` | `python:3.12-slim` | A2A server | None. No database URL. NCBI key from the environment, not from a file in the image. |
| `genome` | The JRE image named in the pinned Exomiser release notes | Wrapper plus the upstream CLI zips | Exomiser and LIRICAL data, the input VCF, the output directory. Bind `127.0.0.1` only. |

Compressed sizes of `python:3.12-slim` and `node:22-alpine` were not measured this session. UNCLEAR. Do not quote a megabyte figure until `docker image ls` has been run.

The genome image does not `COPY` the data zips. The Exomiser install page (read this session) says the data download is approximately 80 GB when the phenotype zip and both assemblies are fetched, and it asks for at least 100 GB free, preferably on an SSD. Exome analysis is listed there as 4 GB RAM minimum; genome analysis as 8 GB RAM minimum; about 1.5 GB RAM per assembly loaded. A GitHub issue on that repo shows one extracted hg38 file listed at 30G (`2602_hg38_variants.mv.db`). This plan pins one assembly, hg38, unless a fixture VCF is hg19. The zip is still large. A laptop without 100 GB free does not run the experimental track.

`compose.yaml` services: `web`, `api`, `postgres` (`postgres:16`). No `genome`, no `literature`.

`compose.experimental.yaml` services: `genome`, `literature`. It is not an override file that gets merged by default. `make demo` does not pass it. The genome service has no published port on `0.0.0.0`.

Postgres in the safe Compose file is the real-user database when `DATABASE_URL` is the Compose host. When `DATABASE_URL` contains a Neon host, the API refuses a case whose `synthetic` flag is false (the check is in the API and in `004_synthetic_check.sql` for the demo role).

## E. Where it runs

### Verified this session

Neon free plan, from the [free-plan FAQ](https://neon.com/faqs/free-plan-limits-and-quotas) and the [plans page](https://neon.com/docs/introduction/plans), opened 10 October 2026:

- $0.
- 100 projects.
- 10 branches per project.
- 100 CU-hours per project per month.
- Autoscaling up to 2 CU.
- Scale to zero after 5 minutes, and that cannot be turned off.
- 1 GB Postgres storage per project, 20 GB across projects.
- 5 GB public network transfer per project per month.
- Instant restore history 6 hours, capped at 1 GB of changes.
- 1 manual snapshot.
- Inserts that would grow a project past 1 GB fail. Neon does not delete rows to make room.

HIPAA, from the [HIPAA guide](https://neon.com/guides/hipaa-compliant-applications): Free and Launch are not HIPAA compliant and should not be used for PHI. HIPAA is a Scale-plan feature, with a BAA. The synthetic demo may use Neon. A real chart may not.

GitHub Actions, from the [Actions billing docs](https://docs.github.com/en/billing/concepts/product-billing/github-actions), opened this session: standard GitHub-hosted runners are free for public repositories. Private repositories on GitHub Free include 2,000 minutes per month and 500 MB of artifact storage. Larger runners are billed even for public repositories. Whether this project’s remote is public is a fact about the host, not about the plan. The default job must stay inside the free public-runner path: no larger runner, no Exomiser download.

Vercel Hobby, from the [Hobby plan](https://vercel.com/docs/plans/hobby) and [fair-use](https://vercel.com/docs/limits/fair-use-guidelines) pages opened this session: $0, personal non-commercial use. Included amounts named on those pages include 100 GB Fast Data Transfer, 10 GB Fast Origin Transfer, 1,000,000 CDN requests, 1,000,000 function invocations, 4 CPU-hours active CPU, and 360 GB-hours provisioned memory. Exceeding included usage pauses the Hobby project until the window resets. A commercial deployment needs a paid plan. A portfolio demo with no payment and no ads fits the personal-use wording as this plan reads it. That reading is not Vercel’s ruling.

### Not verified

A free long-running host for FastAPI (hours, not a short function) was not opened. UNCLEAR. Gemini free-tier model ids and rate limits were not re-opened this session. The 10 October note quotes the Gemini API additional terms effective 23 March 2026: unpaid content may be used to improve Google products; do not submit sensitive information; not for clinical practice or medical advice. This plan uses that reading and does not send real text.

GitHub-hosted runner disk size was not opened. UNCLEAR. It is the wrong place for an 80 GB data volume either way.

### Placement

| Track | Run | Deploy |
| --- | --- | --- |
| Safe core, real records | Laptop. `make demo` with Compose Postgres. Nothing about the variant leaves the machine except a download of a public change-list file. | Not deployed. A family that cannot run Docker needs a helper. That limit stays in the README. |
| Safe core, synthetic demo | Same Compose, `DATABASE_URL` on Neon, banner “do not enter real information.” | Optional later: the Next.js app on Vercel Hobby, still talking to a Neon project that rejects non-synthetic cases. The API process for that demo is the laptop or a host whose free tier has been read. No such host is named here. |
| Literature | `make literature` on the laptop. Sends the accepted gene symbol and HPO ids the user chose to put in the request. Does not send the note body. | Not on the patient Compose file. Not on Neon. |
| Experimental | Laptop only, after `ALLOW_LOCAL` exists (gitignored) and `D1_TRACK=experimental-local`. | No Terraform resource, no registry push, no Vercel project, no Neon table. |

## F. Production shape

Still $0 for the pilot. Terraform in `infra/terraform/` is a sketch of one later VM for the synthetic demo: the `web` and `api` images, `DATABASE_URL` pointing at Neon, no genome service, no VCF bucket, no NCBI key on the API. `terraform apply` is not part of this plan. The trigger to apply it is a second person using the synthetic demo, not a real chart. A real chart stops the hosted path.

### CI

`.github/workflows/test.yml`, on push, public standard runners:

- `make test` against a Postgres service container.
- Template scan.
- Import-boundary test.
- The five synthetic cases.
- The experimental entrypoint test (it must exit when the flag is missing).

That workflow does not download Phenopacket Store, ClinVar monthly files, or Exomiser data. `make eval-store` and `make change-list` are local.

A second workflow file, `experimental.yml`, runs only when someone starts it by hand. It runs the same entrypoint refusal test. It does not run Exomiser.

### Flags that keep the experimental track off a real user

All of these are in the tree, and `make test` fails if one is removed:

1. `compose.yaml` has no `genome` service. The boundary test reads the file.
2. `services/genome/entrypoint.py` exits unless `D1_TRACK` is `experimental-local`, the bind address is `127.0.0.1`, and the file `services/genome/ALLOW_LOCAL` exists. That file is gitignored. A clone does not have it.
3. `deploy/public-services.txt` (created with the workflows) lists `web` and `api` only. The test fails if `genome` or `literature` appears.
4. `infra/terraform/demo.tf` has no genome resource. The test greps it.
5. `SafeCard` and `ToolResult` are different types. `app/pdf.py` cannot import `ToolResult`.
6. Every experimental result file starts with `banner.txt`: research use only, not for diagnostic procedures, not a patient or caregiver output.
7. The API, when `DATABASE_URL` is a Neon host, rejects `synthetic = false`.

There is no switch in the notebook UI that uploads a VCF.

### Secrets

`.env` is gitignored. `.env.example` lists `DATABASE_URL`, `NCBI_API_KEY`, `GEMINI_API_KEY`, `D1_TRACK`. The API container receives `DATABASE_URL` only. The literature container receives `NCBI_API_KEY` only. The genome container receives neither. Gemini is used by `eval/` on the host, not by a container that serves a user. CI has no required secret.

### Observability

JSON logs on stdout: time, request id, route, status. The log line does not include note text, variant text, or a VCF path. No third-party tracing account. Docker’s logs are the local view. Vercel Hobby’s included runtime logs, if the frontend is ever hosted there, are the host’s own retention; the account-plans page opened this session mentions 1 hour of runtime logs on Hobby. That is a frontend host limit, not a clinical audit log.

### Backups and migrations

Local real-user mode: the README tells the operator to run `pg_dump` on a schedule they choose. This repo does not ship a cloud backup of that dump. Neon’s 6-hour restore window is a property of the synthetic project only. It is not a backup of anyone’s chart.

Migrations are the numbered files in `sql/`. The API role cannot own them. A `make migrate` target applies them as the `NOLOGIN` owner. The gate tests run against a migrated database, including: permission denied without `EXECUTE`; a second decision raises; a hash mismatch raises; a pending row remains when the function is not called; a pooled session setting does not authorize the next transaction.

### Evaluation in CI

The push workflow runs the five synthetic cases, the template scan (including  the forbidden words from the 10 October note: diagnosis claims, “pathogenic” in the product’s own voice, dose words, “eligible”), the red-flag phrase list, and the PDF-injection fixture (text inside a synthetic PDF does not become a slot). It prints the “cannot claim” line for each: these checks pass on these cases.

The store metrics (k = 1 and k = 5, abstentions as misses, 249 unique maps, 531 exclusions printed, degree baseline from Orphanet phenotype rows) stay in `make eval-store`, which a stranger runs after downloading the zip. CI does not fetch that zip.

The experimental track’s calibration, when someone has the data volume, is the upstream tool’s rank on the store’s public cases, reported separately from the safe-core overlap count. Gene symbols stay out of the phenotype-only function. A VCF spiked from the store is an experimental methods result on published cases, not a performance number for a living person. That job is local because of the data size.

### Pilot

One person. Five synthetic cases. `make demo`, `make test`, one `psql` session showing a pending draft that is still pending. No family, no clinic, no VCF. A later favor is Ashish running the same Compose on his laptop with synthetic data only.

### Scaling triggers

- Knowledge-base SQLite or the monthly change list is too large for a home connection: the change list falls back to gene-level rows, and the README says so. The byte size is UNCLEAR until `make change-list` has been run. The 10 October note measured ClinVar’s 2026-10 `variant_summary` at about 451 MB compressed and the 2021-01 file at about 67 MB. This session did not re-list the FTP site.
- Neon project near 0.7 GB or near the CU-hour cap: keep the knowledge base on disk, or stay on Compose. Do not load ClinVar XML into Neon.
- Laptop free disk under 100 GB: do not install the experimental data.
- Anyone asks to put a real chart on Neon, or to expose the genome port: stop.

### Cost at this pilot

| Item | Cost | Limit that matters |
| --- | --- | --- |
| Compose Postgres on the laptop | $0 | The operator’s disk and their own `pg_dump` |
| Neon free, synthetic demo only | $0 | 1 GB, 100 CU-hours, no HIPAA agreement |
| GitHub Actions, public standard runners | $0 | Free for public repositories; do not download Exomiser data |
| Vercel Hobby, if used for the frontend | $0 | Personal non-commercial caps listed in section E |
| HPO, Orphadata, ClinVar, ClinGen downloads | $0 | Change-list size UNCLEAR |
| Exomiser and LIRICAL data, experimental laptop | $0 to download | About 80 GB and 100 GB free disk, from the Exomiser install page |
| Gemini free tier | $0 | Synthetic fixtures only; key unset by default |
| NCBI key | $0 | Unset unless `make literature` is run |
| Terraform apply, a paid model, a lawyer | Not in this pilot | A lawyer is an open question, not a free tier |

## G. Phases for one person

Estimates for phases 0–2 are the ones in the 10 October notebook note, where they are labelled as that author’s estimates, not a sourced schedule. Phase 3 is this plan’s estimate, same status. Stop at a stop-rule even if the week count is not used up.

**Phase 0, about 2 weeks. Measure, write no UI.**

- Build the knowledge-base file. Record its size in this document.
- Diff two ClinVar monthly files. Record the change-list size. If it is too large for a normal home connection, the watcher is gene-level.
- Run the overlap count on Phenopacket Store `0.1.27`, including a lay-term degradation. The 10 October note counted layperson synonyms in HPO `v2026-09-01`: 4,695 of about 19,900 current terms. That count was not repeated this session.
- If the lay-style run is near random on the 249-disease subset, the conditions list stays off and the README says the match is not useful under lay wording.
- Pick the red-flag source. It is not chosen yet.

**Phase 1, about 6 weeks. Safe core on synthetic cases.**

Timeline, symptom confirm, database gate, typed variant form, change-list match, template library, forbidden scan, red-flag stop screen, PDF, consent screens, Compose, Neon synthetic demo. Gate tests and the template scan are the exit.

**Phase 2, about 4 weeks. Depth that is still safe.**

“Not on the gene’s list” as overlap counts in a template. Conditions-to-ask-about behind a setting, default off. Phenopacket export. Trial and registry links with the query visible. Local PDF text extraction for a digital lab report, fields unsaved until confirmed. Scanned OCR stays out. README tables for what the public cases did and did not show.

**Phase 3, about 4 weeks. Experimental container.**

Pin Exomiser and LIRICAL versions. Volume for data. Adapters shell out. Flag tests. One public fixture VCF already shipped by Exomiser’s own examples, not a person’s file. Methods note: rank and a calibration line on published cases, with the tool name and version. No notebook button.

**Not in these phases.** A hosted service for real families. A study with real users. Other languages. A local model on real notes. Images. Matchmaking. Any screen that tells someone they have a disease.

### Open questions

Only Ashish can answer these. Defaults are what the build uses if he does not.

1. **Is the first real-user mode a tool on that person’s computer, plus a synthetic demo?** The default is yes. A hosted app for real families needs a compliant database and a lawyer. Neon free is not that database.
2. **Which country’s rules frame the first reading, the United States or India?** The default is to write the screens in English, keep the India policy section in `PLAN.md`, and not claim either CDSCO or FDA has cleared anything. The 10 October regulatory note says a patient-facing ranked genome tool has no low-risk route that author found, and that India and EU device rules for this software were only partly opened. CDSCO’s software guidance (document dated 21 July 2026 on the note) treats intended use as including promotion, and lists software that suggests or excludes a condition as regulated. This plan does not put that ranking in the notebook.
3. **Is there a one-time budget for a lawyer before any real person uses the laptop build?** If no, the README keeps “research prototype” on the real-user Compose path as well as on the demo, and the PDF header stays “Prepared by the patient or caregiver using a record tool. Not a medical document.”
4. **Does the experimental track stay in this monorepo?** The default is yes, as `services/genome`, because that is the decision in the request, with the flags in section F. The regulatory note preferred a separate repository and a separate name so the notebook is not promoting the engine. The import boundary is this plan’s substitute. A later split of that directory is possible because the safe core does not import it.
5. **Red-flag list: which public authority’s patient page?** Unset. Phase 0 picks one and cites it. Until then the stop screen exists and the phrase file is empty, which is a failing test, so Phase 1 cannot finish on an empty list.
6. **gnomAD on a card.** Still no on the safe core. The Broad policies page was not re-fetched this session. Exomiser may print a frequency inside its own file; that file is experimental output, attributed to Exomiser, and is not copied into a template slot.
