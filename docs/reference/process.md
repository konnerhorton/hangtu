# How work gets done on hangtu

Personal reference notes. Adapted from Anthropic's [AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook), which assumes an existing product. These notes add the part it leaves out: starting from zero with a product-level spec.

## The documents

| Document | Scope | Lifetime | Answers |
|---|---|---|---|
| `SPEC.md` | Whole product | Permanent; changes with the product | What is hangtu, and what holds for every feature? |
| `CLAUDE.md` | Whole repo | Permanent; under a page | How do I work in this repo (commands, conventions, recurring mistakes)? What's next? Done work is in SPEC §12.4 and git, not here |
| `docs/work/<id>.md` | One unit of work | `## Intent` frozen once done, `## Plan` frozen once merged | What do we want and why (Intent)? Which files, in what order, proven by which tests (Plan)? |
| Feature spec | One feature | Kept while the feature exists | What exactly does it do, and how do we know it works? |
| `docs/drafts/` | Upcoming features and future phases | Until promoted to a feature spec | Draft feature specs and early notes. Input for intents; only items marked "decided" are decisions |
| `docs/plots/drafts/` | Plots not yet specified | Until promoted to `docs/plots/PXX-*.md` | Draft plot specs in the TEMPLATE format. Input for a plot's spec step; not decisions |
| `docs/drafts/parameters/` | One sheet per ground parameter, and the index | Sheets until promoted to site pages; the index is permanent | What is known about each parameter (tests, methods, sources), and how far along each of its stages is |
| `docs/TODO.md` | Backlog | Permanent | What hasn't been decided or researched yet? |

The **feature spec** for a plot is `docs/plots/PXX-*.md`. For other work it is the `## Spec` section of `docs/work/<id>.md`, or a new topic doc under `docs/` when it will outlive the change, such as the Phase 2 data model.

Each unit of work is one file, `docs/work/<id>.md`, named after its branch. The intent commit creates it with `## Intent`, and each later loop step's commit adds its section (`## Spec` when needed, then `## Plan`), so nothing is merged at the close-out.

## Stages and waves

hangtu's roadmap is organized by parameter (SPEC §1.3). Every parameter climbs four **stages**: A data, B direct derivation, C correlations, D selection. A **wave** groups stages that share an engine, so a wave moves several parameters forward a stage each. Each wave is one or more milestones in SPEC §12.4, and each milestone is one or more units of work through the loop below.

**Data and analysis are separate units.** When a wave or milestone proposes both a dataset (stage A) and the analyses built on it (stage B or C), they become two units, data first: for example M14 (a) density data, then M14 (b) phase relations. Each then fits in one review, and the shape of the data is settled before formulas are built on it.

A wave's units add three things to the loop:
- **Spec:** promote the sheets the wave covers from `docs/drafts/parameters/` to site pages (`docs/site/parameters/NN-*.md`, from the sheets' `TEMPLATE.md`), verify the [U] citations the wave relies on and hand-calculate the golden values from the verified source, check what of the sheet can be published (values and citations, not whole tables or charts; TODO #30), and propose the new names against the whole registry. The wave's acceptance criteria go in its `docs/work/` file.
- **Build:** each method's equation, inputs, validity and source go in its function's docstring (the checklist in `TEMPLATE.md`); the page links to the API reference rather than restating them.
- **Close:** update the stage status of each sheet in the parameter index.

## The loop for each unit of work

A unit of work is a milestone, a plot, a fix or a decision. Keep it small enough to review in one sitting.

1. **Intent**: create the unit's branch, then create `docs/work/<id>.md` with a short `## Intent` section covering goal, why, constraints, what's out of scope, and the SPEC sections it touches. Brainstorm it with Claude and review it yourself before committing.
2. **Spec**: write or update the feature spec (or add the `## Spec` section when there is no other home for it). Check it against `SPEC.md`. If it needs a cross-cutting decision changed, change `SPEC.md` now, deliberately, rather than letting the code drift from it.
3. **Plan**: Claude Code plan mode, then add the `## Plan` section and commit it. It names the files, the order, and the tests that prove each acceptance criterion.
4. **Build**: implement the plan. If the plan has to change, update the `## Plan` section in the same commit.
5. **Test**: check against the acceptance criteria and golden values, and look at the figure yourself.
6. **Close**: merge. In the same PR, update `SPEC.md` (decisions, and the unit's Status in §12.4), the plot status in `docs/plots/README.md`, `docs/TODO.md`, and the "Next" sentence at the top of `CLAUDE.md` when the next unit changes. `CLAUDE.md` names what's next, never what's done.

For a trivial fix, skip the intent and plan and just write a good commit message. Use the full loop when a decision is involved.

## Git and commits

The rules that hold for every commit (staging by name, never committing red, the message format and approval) are in `CLAUDE.md`, "Git and commits", so they're in front of Claude every session. The rest:

- **Each unit of work gets its own branch** off `main`, named after it (`m0-scaffolding`, `p01-property-profile`). It is merged into `main` after review with `git merge --no-ff`, so each unit is one merge commit: `git log --first-parent main` lists the units, and `git revert -m 1 <merge>` undoes one whole.
- **Each loop step gets its own commit:** intent, spec, plan, then the build. The close-out updates (statuses, SPEC, TODO) go in the last build commit.
- **During a build, commit at each green, coherent point.** Usually that's one plan step, with ruff and pytest passing. While working on a step, run the tests it touches; run the whole suite in parallel once, before the commit. Use judgment: a commit is one idea a reviewer can follow in a single read. If a step goes past roughly 300 changed lines (not counting test data), split it.
- **Don't mix kinds of change.** A refactor or rename gets its own commit, separate from new behavior.

## Starting from zero

The playbook's loop needs something for each intent to point at. In an existing product that's the code. In a new project it's `SPEC.md`. So the order is:

1. **Product spec first.** Write down the scope, phasing and cross-cutting decisions (done: `SPEC.md`).
2. **M0 (scaffolding) is the first run through the loop.** Once it lands, fill in the commands section of `CLAUDE.md`.
3. **Each later milestone or plot is one run through the loop.** Milestones in SPEC §12.4 map onto intents, and each names its wave (above). A milestone can be split into several intents, for example M8 into P04, P05 and P06.
4. **Phase boundaries are where the spec is redesigned.** At M4 (the start of Phase 2), turn `docs/drafts/phase2-data.md` into intents and specs, and move the decisions that apply across Phase 2 into `SPEC.md`.

## How detailed should SPEC.md be?

Use one test: **put a decision in SPEC.md if two different features could get it wrong or decide it inconsistently.** Units, column names, the plot contract, depth conventions and error style all pass this test. A QC threshold or a dataset's column list affects only one feature, so it goes in that feature's spec.

Other guides:
- **Decisions and reasons, not designs.** Record "convert to SI on ingest, because…", not the pipeline diagram.
- **Current state, not history.** Git keeps the history.
- **Don't fully specify phases you aren't building yet.** Write the constraints that are already decided, and keep the rest in `docs/drafts/`. Early detail goes stale and reads as if it were decided.
- **Config tables and YAML belong in the repo's real files**, not copied into the spec.
- **Size check:** about 300–450 lines is healthy for this project. If a section keeps growing, a feature spec is probably hiding inside it.

## Does SPEC.md eventually go away?

**It shrinks, but it stays.** As features ship, the source of truth for *behavior* moves:
- what a function does → code, docstrings, tests;
- the column list → `columns.yaml` (`ht.columns()`);
- defaults and tables → `config/defaults.yaml`;
- how to use it → README, tutorial, API docs.

When a SPEC section is fully covered by those, replace it with a one-line pointer.

What stays is what code can't hold:
- **who it's for** and what's out of scope;
- the **phasing and roadmap**;
- **cross-cutting principles and the reasons for them**, for example "never guess units" or "never drop data silently". Without these, a future contributor or Claude could undo a decision without knowing why it was made.

By v1.0, `SPEC.md` will probably be a short product and architecture document with a decision log. If it gets to the point of only listing decisions, convert it to ADRs (`docs/decisions/NNNN-*.md`, one decision per file) and drop the single file. Don't do that while the product is still being designed. One file is easier to review now.
