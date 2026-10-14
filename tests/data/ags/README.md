# Synthetic AGS4 test files

Made-up data for the M5 ingest tests (`docs/data/ingest.md` §11). No company data (SPEC §12.3).
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
