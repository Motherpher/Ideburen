# WP09 — Quality & Governance Audit

**Datum:** 2026-11-15. **Status:** teknisk revisionsmotor implementerad; publiceringsgrind RÖD. **Arbetsorderns DoD**: röd/gul/grön QA-logg och inga blockerande fel **i en release**. Därför sker ingen release vid röd status.

## Styrning och auktoritet

- Director har godkänt ADR-0001 och ADR-0002, **inte** en publik datarelease.
- Pius System Codex 5.0, Appendix O: `Harvard Reference & Source Audit Protocol (HARP)`; exakta steg `ITR1 → ITR2 → ITR4 → ITR5 → ITR6`. **ITR3 finns inte i detta protokoll.**
- RefA är en fullständig källrevision. En maskinell metadatakontroll, checksummekontroll eller förekomst av original-URL utgör **inte** RefA.
- Rollen Research/source reviewer utför claim-specifik primärverifiering och Harvard-referenser med originalbelägg; Data steward kontrollerar definitionsfrågor och integritet; GIS maintainer kontrollerar geometri; Director beslutar separat om releaser.

## Maskinell revision

Kommando (reproducerbar, standardbibliotek):

```bash
python -m ideburen.cli validate
python -m ideburen.sources validate
python -m ideburen.statistics validate
python -m pytest -q
python -m ideburen.cli build --out build
python -m ideburen.statistics build --out build
python -m ideburen.cli package --input build --out build/ideburen_tables.gpkg
python -m ideburen.gis prepare --gpkg build/ideburen_tables.gpkg --source-dir build --out build/gis_handoff.json
python -m ideburen.ffspatial_adapter build --handoff build/gis_handoff.json --gpkg build/ideburen_tables.gpkg --source-dir build --out build/ffspatial_adapter --generated-at $(date -u +%Y-%m-%dT%H:%M:%SZ) --ff-spatial-commit 76dcadfb5d116e238d404ad106465b8a39111d6f
python -m ideburen.governance audit --source-dir build --out build/wp09
```

`build/wp09/wp09_audit.json` = maskinläsbar revisionsrapport inklusive release-status;
`build/wp09/wp09_qa_log.csv` = röd/gul/grön avvikelselogg med åtgärd/ägare;
`build/wp09/wp09_harp_source_matrix.csv` = en rad per registrerad källa och revisionssteg.

### Separata kommandon för separata beslut

- `python -m ideburen.governance audit --source-dir build --out build/wp09` returnerar 0 om den tekniska revisionen passerar, men registrerar fortfarande `release_status=BLOCKED`.
- `python -m ideburen.governance release-check --source-dir build --out build/wp09-release` returnerar 2 när release-gaten är blockerad. Det kommandot **ska inte** ersättas med ett grönt CI-test eller ignoreras inför en publik publicering.
- Teknikfel i grundkontroller, publicerade binärfiler/känsliga register eller manipulerade dataartefakter ger teknisk RÖD och avbryter även QA-kommandot.

## RAG: regeldefinition

| RAG | Betydelse | Konsekvens |
| --- | --- | --- |
| GREEN | Kontroll i verifierad, begränsad omfattning passerar | Teknisk utveckling/QA får fortsätta |
| AMBER | Ofullständigt underlag eller separat beroende, men inte nödvändigtvis tekniskt fel | Begär komplettering; publicera inte berörda påståenden |
| RED | Release-gate blockerad eller tekniskt integritetsfel | Publicera inte; tekniskt fel stoppar CI |

Det är **avsiktligt möjligt** med grön teknisk byggkedja och röda release-hinder. Det innebär att reproducerbar kod kan vara fungerande utan att källornas publicerbarhet är godkänd.

## Kontroller av innehåll och datakvalitet

**Källor:** Källregistret måste vara unikt, fullständigt mot arkivinventeringen och relationsvaliderat. Binär SHA-256 är inte jämställt med licens eller RefA. ITR2/ITR5/ITR6 för originals relevanta innehåll står öppna tills manuell kontroll är dokumenterad. Harvard ITR4 kräver utöver redan registrerad referenstext kontroll av fullständig publikationsuppgift, URL och åtkomstdatum.

**Statistik:** Sju juridiska former i Uppsala 2022 är annan population än SCB:s nationella X105. Nationella observationer får inte fylla kommunpolygoner. `unknown`, `not_observed`, `out_of_source_scope` och exakt talet 0 är skilda tillstånd. WP04:s 10 angivna och 280 okända kommunsiffror blir inte en jämförbar 290-kommunsdatabas.

**Beslut:** 27 WP04-händelser är ett forskningsindex och inte 27 juridiskt självständigt kontrollerade beslut. En normativ uppföljningsplikt är inte en observerad uppföljning. Kausal och rättslig relation kräver dokumenterat stöd, inte datumordning.

**Geografi:** SCB 2026 identitetsnycklar är inte 2022 polygoner; 2022 observationer kan inte utan godkänd metod kopplas till 2026 gränskarta. Extern åtkomst till Lantmäteriet är ansökt men ännu inte bekräftad; historisk 2022-gräns kan kräva separat arkivkälla.

**Sekretess:** Statisk kontroll av versionerade textfiler och råa binärfiler ger teknisk begränsad detektion av eventuella kontaktuppgifter och hemlighetsmönster. Den ersätter inte juridisk riskbedömning, sekretessklassificering eller registerutdragsgranskning. Privata original och autentiseringsuppgifter ska inte delas i publikt repo.

**Artefakter:** Fulla GeoPackage/CSV-previewfiler laddas tills vidare **inte upp** till GitHub Actions som offentligt/halvpublikt åtkomliga artifacts. Arbetsflödet validerar dessa internt och exporterar endast sanerad WP09 QA-logg.

## Kvalitetsstatus och begränsning

De maskinella testerna verifierar referensintegritet, statistikens datakontrakt, checksummor, sekretessmönster och schemarelaterade processer. De genomför inte verklig PDF-sidläsning, geografisk topologi i QGIS eller den slutliga akademiska/manuella HARP-analysen. Ingen automatisk körning godkänner en extern datarelease.

Se `docs/WP09_ACCEPTANCE.md`, `docs/WP09_RAG_REGISTER.md` och `docs/RELEASE_STATUS.md`.
