# Tasks & Progress Tracking

This directory contains task breakdown, milestone planning, and progress tracking for the OpenPanCan Gene Base project.

## What Goes Here

- **Milestone Plans** — High-level project milestones with target dates, deliverables, and success criteria. Organized by project phase (e.g., Phase 1: Foundation, Phase 2: Data Integration, Phase 3: AI Platform).
- **Sprint Backlogs** — Detailed task breakdowns for current and upcoming sprints/iterations. Each task includes description, assignee, estimated effort, status, and dependencies.
- **Feature Roadmaps** — Visual or structured roadmaps showing planned features, their priority, and timeline. Links to relevant design and spec documents.
- **Progress Reports** — Periodic summaries of what was accomplished, what's in progress, what's blocked, and metrics (e.g., genes curated, data sources integrated).
- **Meeting Notes** — Key decisions, action items, and discussion summaries from project meetings related to task planning.
- **Risk Register** — Identified project risks, their likelihood/impact, mitigation strategies, and status.

## File Naming Convention

```
YYYY-MM-DD_topic.md
```

Examples:
- `2026-07-01_phase1-milestones.md`
- `2026-07-01_sprint-1-backlog.md`
- `2026-07-01_feature-roadmap.md`

## Task Status Convention

| Status | Meaning |
|--------|---------|
| `backlog` | Identified but not yet scheduled |
| `todo` | Scheduled for current iteration |
| `in_progress` | Actively being worked on |
| `review` | Completed, awaiting review |
| `done` | Completed and verified |
| `blocked` | Cannot proceed due to dependency |
| `cancelled` | No longer needed |

## Current High-Level Tasks

1. **Repository Foundation** — Set up Git repo, directory structure, documentation framework
2. **Core Data Model** — Design and implement the gene entity data model
3. **COSMIC Integration** — Build ETL pipeline for COSMIC pancreatic cancer mutation data
4. **TCGA-PAAD Integration** — Ingest and structure TCGA pancreatic adenocarcinoma data
5. **OncoKB Integration** — Integrate OncoKB variant annotations and therapeutic implications
6. **ClinVar Integration** — Import germline cancer predisposition variants
7. **GTEx Integration** — Incorporate normal pancreas expression data
8. **Gene Search API** — Build gene-centric search and retrieval API
9. **Variant Browser** — Interactive variant exploration interface
10. **AI Model Integration** — Connect gene database to ML/AI models
