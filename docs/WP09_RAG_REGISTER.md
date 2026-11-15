# WP09 — RAG Quality Register, baseline 2026-11-15

**Registreringen är en initial kod- och källregisterrevision. Den genererade loggen i `build/wp09/` är kanonisk för varje enskild körning.**

| RAG | ID | Avvikelse/belägg | Ägare/åtgärd |
| --- | --- | --- | --- |
| RED | `POLYGONS_UNAVAILABLE` | Lantmäteriet-konto inväntas; officiella årsvisa gränser ej hämtade | GIS maintainer: Inhämta licensierad geometri; för 2022 statistik behövs 2022 årgång |
| RED | `QGIS_RUNTIME_PENDING` | Ingen verklig körning av QGIS projekt/topologi | GIS maintainer: Verifiera 290 topologiskt giltiga kommungeometrier i verklig PyQGIS-runtime |
| RED | `SOURCE_REFA_INCOMPLETE` | HARP ITR2, ITR5, ITR6 saknar fullständig manuell originalgranskning | Research reviewer: Läs respektive original och dokumentera tabell/sida/version/källkedja |
| RED | `LICENSE_CLEARANCE_PENDING` | Source rights_status är ej godkänd för återpublicering | Data steward: Datera separat licens-/rättighetsprövning per releasad datamängd |
| RED | `PRIVACY_REVIEW_PENDING` | Statisk sekretesskanning är inte ett rättsligt publiceringsgodkännande | Data steward: Genomför prövning för offentlig exponering, känsliga grupper och småtal |
| RED | `DIRECTOR_RELEASE_APPROVAL_MISSING` | Godkända ADR ≠ godkänd publik release | Director: Godkänn namngiven, versionsfryst release efter avslutad QA |
| AMBER | `FFSPATIAL_CONSUMER_NOT_RUN` | WP08 är kontraktstestad men inte körd i FF-Spatial lokala mottagare | GIS maintainer: Kör separat godkänd mottagartest utan att ändra FF-Spatial |
| AMBER | `SORM_LAN_ANNEXES_NOT_AUDITED` | Sörmlands nio bilagor indexerade men inte fullgranskade | Research reviewer: Extrahera med metod/år/population och manuellt RefA |
| AMBER | `WP05_PRIMARY_DECISIONS_OPEN` | Beslutsindex saknar originalspecifik juridisk revision | Research reviewer: Kontrollera protokoll/paragrafer och uppföljningshandlingar |
| AMBER | `SOURCE_CHECKSUM_COVERAGE` | Endast två lokala XLSX har binär SHA-256 bokförd | Data steward: Säkra övriga originalfiler och beräkna hash utan att publicera dem |
| GREEN | `ENGINEERING_BASELINE_PASS` | Programmerade kontroller passerar när CI är grön | Maintainer: Fortsätt utvecklings-/datagranskning |

**Resultat:** 6 rödspärrar för release, 4 gula uppföljningar och 1 grön teknisk kontroll när baseline-validatorer passerar. Eventuella ytterligare tekniska fel från verklig körning läggs ovanpå denna lista och kan öka antalet röda poster.

**Releasebeslut:** BLOCKED. **Teknisk utveckling:** kan fortsätta om tekniska kontroller passerar. **Lantmäteriet:** kontoansökan har skickats; ingen åtkomst, årgång eller fil får markeras verifierad förrän faktisk leverans har kontrollerats.
