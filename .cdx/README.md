# CDX estate anchor — admission candidate

**Repository:** `Motherpher/Ideburen`  
**Local anchor:** [`.cdx/anchor.json`](anchor.json)  
**Governing authority:** [Conductellence / CDX](https://github.com/Hybrismannen/Conductellence-)  
**Law:** `CDX-LAW-001` · **Standard:** `CDX-GOV-ANCHOR-001` · **Runtime contract:** `CDX-RUNTIME-001`

This Ideburen national civic evidence infrastructure has a **declared, release-pinned candidate local anchor** pointing at CDX policy 1.0.0. The anchor is intentionally marked `ANCHOR_DECLARED` / `NOT_VERIFIED` because central estate registry admission, independent pin/schema validation, and any consequential runtime enforcement have not been established.

## Binding / authority limits

- `CDX → repository`: CDX publishes constitutional policy and conformance requirements; no CDX universal repository write authority is inferred.
- `repository → CDX`: this repository declares its local governance linkage pending independent registration and verification.
- All consequential effects require explicit authority, mandate, applicable policy and evidence. **No existing scripts, CI jobs, publication process, deployment or user permission is rendered automatically CDX-enforced by this declaration.**
- Project- or domain-specific editorial/data standards remain in force. CDX does not grant external rights, public publication clearance or new permissions.

## Adoption gates

1. Register the repo as `GOVERNED_APPLICABLE` in a separately reviewed CDX estate-registry change (not yet performed).
2. Validate the committed anchor against CDX's distributed schema and pinned release/policy digest.
3. Install and test an appropriate repository-local CI conformance workflow (if applicable).
4. Identify actual consequential effects, design and test local enforcement points and evidence capture before claiming `VERIFIED_RUNTIME_BOUND`.
5. Advance `binding_state` and `verification` only with independently inspectable evidence.

**Current status: anchor declaration only; no runtime or CI verification asserted.**
