# Evals

This directory is a human-readable, automation-ready specification for
how the skills in this repository should activate and behave. It is
not, currently, a fully automated test suite — there is no runner in
this repository that scores a live model against these cases yet.
What exists is the specification that such a runner would consume,
plus a format precise enough for a human reviewer to run the same
checks by hand today.

## What's here

- **`activation-prompts.csv`** — a table of example learner prompts,
  each labeled with a `target_skill` (the skill being tested for that
  row) and whether it should activate for that prompt. Used for
  activation testing and negative activation testing.
- **`behavior-cases.md`** — detailed scenarios per skill describing
  expected behavior, forbidden behavior, and success criteria once a
  skill has activated. Used for behavior-constraint testing.
- **`finder-cases.csv`** — routing cases for the
  [Find Your Coach](../find-your-coach/) page: a declared answer path
  and the skill (or honest no-match outcome) it must reach. Unlike the
  two files above, these are executed today, not just specified — see
  [Finder routing cases](#finder-routing-cases).

`activation-prompts.csv` and `behavior-cases.md` cover all thirteen
skills, including the general `think-before-code` learning partner,
the repository-learning workflow `learn-codebase-coach`, the
source-driven research workflow `learn-by-googling`, and the two
software-engineering skills that sit outside the DSA lifecycle:
`specification-coach` before implementation, when the desired
behaviour isn't defined yet, and `code-review-coach` after code
exists. Their boundaries against neighboring skills and direct-service
requests are tested in the same positive/negative pairing style as the
DSA skills' boundaries.

## Activation testing

A prompt in `activation-prompts.csv` with `should_activate = true` is
a case where the skill named in `target_skill`'s frontmatter
`description` should cause an agent to select it over the other
skills in this repository, or over no skill at all.

## Negative activation testing

A row with `should_activate = false` is a case where the skill named
in `target_skill` should **not** activate for that prompt — either
because a different skill is the correct match, or because no skill
in this repository should engage at all (a generic programming
question, for instance). These rows exist specifically to catch
over-eager activation, which is just as much a defect as a skill
failing to activate when it should.

The same (or a very similar) user prompt may legitimately appear
twice: once as a positive row for the skill that should handle it,
and once as a negative row for a neighboring skill that shouldn't —
that pairing is what makes a routing boundary testable.

## Coverage requirement

Every skill directory under `skills/` must have at least one
`should_activate = true` row and at least one
`should_activate = false` row in `activation-prompts.csv` — a skill
with no negative cases has an untested activation boundary. Rows
with `target_skill = none` remain allowed (they test that *no* skill
engages) but don't count toward any skill's coverage.

This rule, along with the CSV's shape, unique ids, and valid
`target_skill` values, is enforced by
[`scripts/validate_evals.py`](../scripts/validate_evals.py). CI runs
that script, so you can check the same rules before pushing:

```bash
python scripts/validate_evals.py
```

## Behavior constraints

Each case in `behavior-cases.md` assumes the correct skill has already
activated, and checks what happens next: does the tutor ask one
question at a time, withhold code appropriately, avoid inventing a
mistake's root cause, and so on. These are the rules a human reviewer
(or, eventually, an automated grader reading model output against
`expected behavior` / `forbidden behavior` pairs) should check for.

## Finder routing cases

`finder-cases.csv` tests a different thing from the two files above.
Activation and behavior cases describe what a *model* should do;
finder cases describe what the deterministic router in
[`find-your-coach/`](../find-your-coach/) does. There is no model in
that path at all — the page walks a declared tree in
`find-your-coach/routes.json` — so these cases can be, and are,
checked automatically on every push.

The schema is fixed:

```text
id,path,expected_result,reason
```

- **`id`** — a stable case id (`F001`-style today; the format is not
  enforced, only uniqueness and non-emptiness).
- **`path`** — the option ids a visitor clicks, in order, separated by
  `>`. Option ids are unique across the whole tree, so a path reads as
  an unambiguous route: `o_start_dsa>o_dsa_stage_statement`.
- **`expected_result`** — the result id the path must land on. Skill
  results are named after the skill they recommend
  (`r_problem_decoder`); the two honest dead ends are
  `r_no_match_implementation` and `r_no_match_delivery`.
- **`reason`** — why that path belongs at that destination. Boundary
  cases say which neighbouring skill they are being distinguished
  from.

[`scripts/validate_finder.py`](../scripts/validate_finder.py) walks
every path through the real route data and fails if it stops early,
runs past a result, or arrives somewhere other than
`expected_result`. It also requires that every result and every option
in the tree is exercised by at least one case, so a new branch cannot
ship without a routing case behind it — the same spirit as the
activation coverage requirement above. Run it locally with:

```bash
python scripts/validate_finder.py
```

The cases deliberately include both no-match outcomes. A router that
can only ever recommend something is a router that will recommend
something wrong, and "Think Before Code does not do this" is a result
worth regression-testing.

## Regression testing

The activation and behavior files double as a regression baseline. If a future change to a
`SKILL.md` file causes a previously-passing case to fail — a skill
that used to correctly decline to activate now does, or a skill that
used to withhold code now reveals it early — that's a regression, and
the relevant case should be added to or checked against before merging
the change.

## Running these checks locally today

Until an automated runner exists, a contributor can:

1. Pick a row from `activation-prompts.csv`.
2. Paste the `prompt` into an agent configured with this repository's
   skills.
3. Confirm the skill named in `target_skill` activates (or doesn't,
   for `should_activate = false` rows) and that the reason in the
   `reason` column actually holds.
4. Pick a matching scenario from `behavior-cases.md` and confirm the
   `expected behavior` items happen and the `forbidden behavior` items
   don't, across a short simulated exchange.

## How a future automated runner could consume these files

`activation-prompts.csv` is plain, quoted CSV with a fixed column
order (`id,target_skill,should_activate,prompt,reason`), so it can
be loaded directly by any CSV reader and scored by checking which
skill actually activated against the `target_skill` /
`should_activate` columns. `behavior-cases.md` is structured
consistently enough (fixed field labels per case) that a script could
parse it into the same shape, but no such parser exists in this
repository yet — see the roadmap in the main README.
