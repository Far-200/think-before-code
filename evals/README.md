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

CI enforces that every skill directory under `skills/` has at least
one `should_activate = true` row and at least one
`should_activate = false` row in `activation-prompts.csv` — a skill
with no negative cases has an untested activation boundary. Rows
with `target_skill = none` remain allowed (they test that *no* skill
engages) but don't count toward any skill's coverage.

## Behavior constraints

Each case in `behavior-cases.md` assumes the correct skill has already
activated, and checks what happens next: does the tutor ask one
question at a time, withhold code appropriately, avoid inventing a
mistake's root cause, and so on. These are the rules a human reviewer
(or, eventually, an automated grader reading model output against
`expected behavior` / `forbidden behavior` pairs) should check for.

## Regression testing

Both files double as a regression baseline. If a future change to a
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
