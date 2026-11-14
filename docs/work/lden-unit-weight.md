# lden-unit-weight: a unit weight held in a user-defined heading

## Intent

### Goal
Record that hangtu reads a lab bulk unit weight only from `LDEN_BDEN`, not from a user-defined heading, and say so
where users look. If a second file needs a user-defined heading read, the mapping goes into M16's readings map.

### Why
- A real file (client data, not in the repo) gives its lab unit weights only in a user-defined `LDEN_UWT`
  (kN/m³, defined in `DICT`), with no `LDEN_BDEN`. QC `C001` flags every `LDEN` row (`qc/min_fields.yaml` requires
  `LDEN_BDEN`) and `p.density()` leaves all of them out. AGS4 `LDEN` has no unit weight heading, so anyone who
  extracts unit weights from a report hits this.
- The file came from the user's own extractor. It can write `LDEN_BDEN` = γ / g as a derived value, say so in
  `LDEN_REM`, and keep `LDEN_UWT` as printed. That fixes the file for every tool that reads it, not just hangtu.
- Only one file needs this so far. A heading map would add a data-model mechanism (SPEC §7) for that one file.

### Constraints
- SPEC §2.6: hangtu never guesses what a user-defined heading means. A kN/m³ heading isn't read as a unit weight
  unless the user says so.
- Published text cites no internal file (CLAUDE.md).

### Out of scope
- **A heading map** (for example `{"LDEN_UWT": "bulk_unit_weight"}`, with hangtu deriving ρ = γ / g). Deferred to
  M16's readings map, to be added when a second file holds a standard group's quantity in a user-defined heading.
  This file has three: `LDEN_UWT`, `LPEN_QU` and `ISPT_B150`. M16's draft maps user-defined *groups*, so a
  user-defined heading in a standard group is a case its map would also have to cover. This goes to `docs/TODO.md`
  with that trigger.
- The extractor's change, which belongs in its own repo.
- `C001` and `p.density()` keep their behavior. 🟡 Proposed: the `C001` message gets no hint about user-defined
  headings, because the hint would have to guess which heading was meant.
- The file review's other items (pocket penetrometer 0, SPT past termination, the datum text, and the rest).

### SPEC sections touched
- None changes. SPEC §2.6 and §7 hold as written.
- `docs/data/datasets.md` §6.8: a bullet saying the bulk unit weight comes only from `LDEN_BDEN` (and `IDEN_IDEN`),
  never from a user-defined heading, and that a file holding only a unit weight needs `LDEN_BDEN` = γ / g.
- `docs/site/parameters/01-unit-weight-and-vertical-stress.md`, "Pitfalls": the `LDEN_UWT` bullet adds that hangtu
  doesn't read such a heading, so `p.density()` leaves those rows out until the file has `LDEN_BDEN`.
- `docs/TODO.md`: a new item for the heading map, with its trigger.
- `STATUS.md`: "Next" moves on to wave 0 / wave 3.
- 🟡 Proposed: no `CHANGELOG.md` entry, since no behavior changes.

### Decisions (intent review, 2026-11-14)
1. **hangtu doesn't read unit weights from user-defined headings; the extractor writes `LDEN_BDEN`.** The fix at
   the source works for every tool, needs nothing from hangtu, and keeps the printed value alongside the derived one.
   Rejected: a heading map now, either as a project setting or with M16, for only one file.
2. **When a second file needs it, the heading map goes into M16's readings map, not into a separate setting.**
   Users then have one place to say what a user-defined heading means. Rejected: a standalone project setting,
   which would end up as a second map beside M16's.

## Plan
One docs commit, `lden-unit-weight: document that a unit weight heading isn't read`. It edits
`docs/data/datasets.md` §6.8, the "Pitfalls" bullet on the unit weight site page, adds the `docs/TODO.md` item and
updates `STATUS.md` "Next" (the close-out). Check: `uv run pytest tests/docs/test_site.py` (published text cites
no internal file) and `uv run zensical build --clean --strict` after `docs/prepare_site.py`. Then merge with
`--no-ff`.
