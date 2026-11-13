# CDX estate anchor — Director-governed CDX control scope

**Repository:** `Motherpher/Ideburen`  
**Local anchor:** [`.cdx/anchor.json`](anchor.json)  
**Governing authority:** [Conductellence / CDX](https://github.com/Hybrismannen/Conductellence-)  
**Law:** `CDX-LAW-001` · **Standard:** `CDX-GOV-ANCHOR-001` · **Runtime contract:** `CDX-RUNTIME-001`

This Ideburen national civic evidence infrastructure has a **Director-approved, release-pinned local CDX anchor** pointing at CDX policy 1.0.0. The anchor is intentionally marked `ANCHOR_DECLARED` / `NOT_VERIFIED` because central registry merge and any consequential runtime enforcement have not been established (the local pinned-release/schema audit has passed in CI).

## Binding / authority limits

- `CDX → repository`: CDX publishes constitutional policy and conformance requirements; no CDX universal repository write authority is inferred.
- `repository → CDX`: this repository declares its local governance linkage pending independent registration and verification.
- All consequential effects require explicit authority, mandate, applicable policy and evidence. **No existing scripts, CI jobs, publication process, deployment or user permission is rendered automatically CDX-enforced by this declaration.**
- Project- or domain-specific editorial/data standards remain in force. CDX does not grant external rights, public publication clearance or new permissions.

## Adoption gates

1. Complete merge of the Director-approved prospective CDX estate admission in [CDX PR #74](https://github.com/Hybrismannen/Conductellence-/pull/74); the `human-sovereign-approval` required check remains pending.
2. Retain the successfully executed local [CDX Anchor Conformance workflow](https://github.com/Motherpher/Ideburen/actions/runs/43458964194) and recheck it on future changes.
3. Maintain `.github/workflows/cdx-anchor-audit.yml` as the read-only policy-pin/schema/identity check; it does not mediate effects.
4. Identify actual consequential effects, design and test local enforcement points and evidence capture before claiming `VERIFIED_RUNTIME_BOUND`.
5. Advance `binding_state` and `verification` only with independently inspectable evidence.

**Current status: Director-approved CDX governance scope; local CI anchor audit PASS, central registry PR awaiting GitHub sovereign status check, runtime effect mediation NOT VERIFIED.**
