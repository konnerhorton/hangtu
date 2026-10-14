# Synthetic AGS4 test files

Made-up data for the M5 ingest tests (`docs/data/ingest.md` §11) and the M6 QC tests (`docs/data/qc.md` §8). No company data (SPEC §12.3).
AGS files can't hold comments, so this page says what each one is for.

The files are written by `_make_files.py`. Change the data there and rerun it, rather than editing a file:

    uv run python tests/data/ags/_make_files.py

`tests/ags/test_files.py` fails if a committed file differs from what the script writes.

| File | Version | Purpose |
|---|---|---|
| `site_si.ags` | 4.2 | Three borings in SI: PROJ, TRAN, UNIT, TYPE, ABBR, DICT (user-defined `XPPT`), LOCA, GEOL, SAMP, ISPT, LLPL, LNMC, GRAG, GRAT, PTST, CPTP, FGHG, FGHS, XPPT. It has `NP`, `Dry`, a refusal, `<1`, `>100`, `#2.65`, blanks, and `LLPL` and `LNMC` on the same specimen. |
| `site_us.ags` | 4.2 | The same data in US units (ft, in, psf, tsf, pcf for a density and for a unit weight, cm/s). Values are the SI values divided by exact factors, written to 10 significant figures (`10SF`, `9SCI`), so the twin-file test can use a 1e-9 tolerance. |
| `site_v404.ags` | 4.0.4 | The same borings, with `IPRG`/`IPRT` instead of `FGHG`/`FGHS`, `RUCS` with `RUCS_E` (removed in 4.2), the old unit spellings `degC` and `Bar`, and no headings added in 4.1 (`ISPT_N60`, `GRAG_PDEN`, `GRAG_SUFF`). |
| `defects.ags` | "4.9" | One case per ingest finding: an unknown version (`V000`), `Ft` (`U001`), `feet` (`U002`), a blank unit in `ISPT_CAS` (`U003`), `kPa` in `LOCA_NATE` (`U004`), `wet` in `LNMC_MC` (`T001`), an orphan `LLPL` specimen (`V10c`), and a user-defined group with no DICT entry (`V9`, `V18`). `M001` comes from `site_v404.ags`. |
| `qc_defects.ags` | 4.2 | One case per computed QC rule (`qc.md` §4.2–§4.10), on five holes in SI; it is clean for python-ags4 and ingest. BH1–BH4 are on a 50 m grid, BH5 has no coordinates, ground level, final depth or geology. Cases, by line: L001, L002, L003, G001 BH5 (58, ISPT 106); L004 HORN 64; L005 BH4 18.00 m (57); L006 always; G002 BH1 2.50–3.00 (70–71), BH2 log stops at 7.50 (73); G003 BH3 (75–76); D001 SAMP 85; D002 ISPT 96; D003 ISPT 103; D004 ISPT 98; D005 SAMP 89; D007 LLPL 116; S001 97; S002 99; S003 BH4 (104–105); S004 100; S005 101; A001–A004 LLPL 112–115; P001 GRAT 137; P002 GRAT 131; P003 GRAG 124; P004 GRAT 139–141; K001 PTST 147, FGHG 153; C001 GEOL 77; C002 `LOCA_TYPE` absent. Cascades (a case that necessarily raises a second rule) are listed in `tests/qc/test_qc_acceptance.py`. |
