# WP01 — Foundation acceptance record

Date: 2026-11-13

Scope (from original work order): repository layout, README, licensing analysis, SECURITY, contributing, issue templates, CI, ADRs, and a reproducible clean checkout.

| Deliverable | Evidence | Status |
| --- | --- | --- |
| Repository | `Motherpher/Ideburen`, main | Implemented |
| Directory layout and clear domain boundaries | `data/`, `geo/`, `docs/`, `src/`, `tests/`, `schemas/`, `manifests/`, `.github/` | Implemented |
| README & commands | `README.md`, `docs/BOOTSTRAP.md` | Implemented |
| Software license | `LICENSE` (MIT) | Implemented |
| Dataset license analysis | `docs/LICENSING.md` | Implemented; per-dataset rights still pending |
| Security and contribution process | `SECURITY.md`, `CONTRIBUTING.md` | Implemented |
| Issue templates | Three task-specific forms and config | Implemented |
| ADR process | `docs/adr/` and two **proposed** ADRs | Implemented; Director approval remains pending |
| PR review checklist | `.github/pull_request_template.md` | Implemented |
| Continuous integration | `.github/workflows/validate.yml` | Confirm latest run success |
| Clean checkout commands | `docs/BOOTSTRAP.md`, CI isolated checkout | Verify latest CI and artifact |

**Scope boundary:** WP01 technical completion is not approval of WP02–WP10, source redistribution, public data release or operational FF-Spatial binding. ADRs remain Proposed pending Director acceptance.
