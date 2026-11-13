# License and reuse audit — WP01

## Software
`LICENSE` contains MIT for original repository software. Before any software redistribution, retain license/copyright notices; third-party packages retain their own separate licenses. `CITATION.cff` identifies the codebase, not underlying data sources.

## Dataset rights are independent
Original PDFs, SCB extracts, Lantmäteriet polygon layers, municipal register exports, Drive files, institutional decisions and third-party databases **are not covered by the repository's MIT license**. Public availability alone does not establish permission to republish their bytes, licensed derivatives or personal data. Each dataset requires a separate `rights_status`, copyright/license attribution, rights holder and review date in its provenance manifest before a release.

## Current source families
| Family | Handling in public repository | Current rights conclusion |
| --- | --- | --- |
| Original Google Drive files | Reference title/id only; no binary mirror | **not cleared for redistribution** |
| Uploaded project XLSX | Process locally; no raw workbook commit | **not cleared** |
| SCB published statistical tables | Cite and verify exact source terms for relevant table/version | **pending dataset-level review** |
| Municipality and regional public PDFs | Link and quote within applicable constraints; do not mirror by default | **pending rights audit** |
| Lantmäteriet administrative polygons | Download only via authorized service with recorded terms | **no polygon source installed** |
| Derived aggregated internal data | Publication requires provenance, method and disclosure review | **not yet cleared** |

## Privacy and security
The public repository holds no contact persons, personal emails, unpublished lists or credentials. Organizational data may still carry a risk of personal identification at small geographical grain; this needs a separate data protection analysis where applicable.

## Gate
A green CI run is **not** a license, HARP or release approval. Director sign-off is mandatory for publication.
