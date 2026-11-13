# WP02 — Authoritative geographic identifier verification, 2026-11-13

**Reference authority:** Statistics Sweden (SCB), *Län och kommuner 2026 i kodnummerordning*, https://www.scb.se/hitta-statistik/regional-statistik-och-kartor/regionala-indelningar/lan-och-kommuner/lan-och-kommuner-i-kodnummerordning/ (checked 2026-11-13).

**Method:** Full enumeration of SCB's 2026 published numerical-code list, comparison against all 290 code+name pairs in the previously staged CSV, preserving exact diacritics and whitespace-separated composite names. Both directions compared: SCB-minus-repo and repo-minus-SCB. Result **290/290 exact matches; 0 missing, 0 extra, 0 code/name mismatches**. Official county list is 21 entries, with matching two-character county code prefixes. No CSV source download was possible through the available environment, so validation used the rendered official SCB listing, not a claim of byte-for-byte import of the SCB XLSX.

**Primary metadata status:** `data/curated/dimensions/municipalities.csv` and `counties.csv` now have `reference_year=2026` and `verification_status=primary_verified`. The four-character codes are **strings**, not numbers, so `0114` is preserved.

**Important limitations:** Verification is of the *2026 identifier reference*, not historic existence or administrative boundary topology. A name/code in the 2026 list does not prove that the same municipality or geography existed in 2000. Historic comparisons require vintage-specific crosswalks and boundaries. No geographic polygon was downloaded or validated in this WP.

The source may change in future years; update only by repeating a complete official reference comparison with a new `reference_year`, source reference and HARP log.
