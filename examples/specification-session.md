# Example Specification Session

This is an illustrative `specification-coach` session, written to
show the skill's flow: one ambiguity at a time, the learner making
every product decision, vague language challenged rather than
interpreted, one proposed requirement deliberately excluded as a
non-goal, and acceptance criteria built from decisions the learner
already made. It is not a transcript of an actual chat log — it is a
realistic example built to match the behaviour described in
[`skills/specification-coach/SKILL.md`](../skills/specification-coach/SKILL.md).

This is deliberately not a DSA session. The learner arrives with an
ordinary, bounded feature request and leaves with a specification an
implementation agent could act on — written by them. No
implementation code appears anywhere.

---

**Learner:** I need to write this up properly before I hand it to an
agent. The ticket just says: "Add CSV export to the orders page."
Every time I've done this the agent invents half the requirements and
I only notice when the PR shows up.

**Quackrates:** Then we define it first. Before deciding fields or
implementation: should the export contain every order the account can
access, or only the rows represented by the filters currently applied
on the page?

**Learner:** The filtered ones. That's the whole point — people
filter down to a date range and then want that in a spreadsheet.

**Quackrates:** Good — that's a real decision, and it rules out a
different feature. What does the orders page do today when someone
wants that data out of it?

**Learner:** Nothing, really. They select rows with the mouse and
paste into Excel, which breaks whenever an address has a comma in it.

**Quackrates:** So the current behaviour is manual copy-paste with a
known failure mode. What must become observably different once this
ships?

**Learner:** There's a button, they click it, they get a CSV file of
whatever's currently filtered.

**Quackrates:** Then let's pin down what's in the file. The orders
table shows quite a lot — which columns does the export contain?

**Learner:** All of them, obviously. Just export everything.

**Quackrates:** "Everything" splits two ways here, and the split
matters. Does the file contain the columns visible in the table, or
every field stored on an order — including ones the table never
shows, like internal notes or the payment processor's reference?

**Learner:** Oh. Not internal notes, definitely. Finance asked for
this and they shouldn't see those.

**Quackrates:** So the file is a defined column set, not a dump of
the record. Can you name that set?

**Learner:** Order ID, date, customer name, customer email, status,
total, and the currency. That's what finance reconciles against.

**Quackrates:** That's a specification-grade answer. You mentioned
finance shouldn't see internal notes — is there anyone who can see
the orders page but shouldn't be able to export it?

**Learner:** Hmm. Support agents can see the page. I don't think they
should be pulling customer emails out in bulk.

**Quackrates:** Then that's a permission decision, and it's yours to
make. What happens when a support agent opens the orders page?

**Learner:** They should see the page normally but not the button.
Hiding it is enough — nobody's attacking us from inside.

**Quackrates:** Hiding a button is a UI decision; whether the export
is *reachable* is a behavioural one. If a support agent hits the
export endpoint directly, what should happen?

**Learner:** Fine, yes — it should refuse. Hidden button *and* the
request is rejected.

**Quackrates:** Now the empty case. Someone filters to a date range
with no orders in it and clicks export. What do they get?

**Learner:** An empty file, I guess? Or maybe an error. Actually I
don't know.

**Quackrates:** Both are defensible, which is exactly why it can't be
left to the agent. Which one do you want to be responsible for
explaining to finance?

**Learner:** A file with just the header row. An error would make
them think the feature is broken when actually their filter is wrong.

**Quackrates:** Decision recorded. You said earlier that the export
should be fast — I want to come back to that, because it isn't
checkable yet.

**Learner:** Right, it should just be fast. Nobody wants to sit there
waiting.

**Quackrates:** "Fast" isn't something anyone can pass or fail a
build on. For the largest export a normal account would realistically
run, what would someone have to observe for you to call it
acceptable?

**Learner:** Our biggest customer has maybe 40,000 orders in a year.
If they filter to a full year, the download should start within a few
seconds — say five. Beyond that they'd assume it hung.

**Quackrates:** Now it's observable: 40,000 rows, download begins
within five seconds. That's a criterion. Should the export handle
accounts far larger than that — a million rows, streamed, resumable?

**Learner:** No. We don't have anyone near that and I'd rather not
build for it.

**Quackrates:** Then say so explicitly, or an agent will build it
anyway. That's your non-goal.

**Learner:** Non-goal: no streaming, chunking, or background-job
export. Synchronous request, and if we ever get a customer that big
we revisit it.

**Quackrates:** One failure path left that I'd call high impact:
the request takes longer than expected, or the server errors
mid-generation. What does the user see?

**Learner:** An error message on the page saying the export failed
and to try again. Not a half-written file — that's worse than
nothing, because they'd reconcile against incomplete data.

**Quackrates:** Then let's turn the decisions into criteria you could
check. Start with the filter one — what would someone observe to
confirm it works?

**Learner:** Filter the orders page to a date range with a known
number of rows, click export, and the file has that many data rows
plus a header. Same filter, same count.

**Quackrates:** That's checkable. Now the permission decision, as an
observable criterion.

**Learner:** As a support agent: the export button isn't rendered,
and a direct request to the export endpoint is rejected rather than
returning a file.

**Quackrates:** And the empty case.

**Learner:** Filter to a range with zero orders, click export, get a
file containing only the header row — not an error.

**Quackrates:** Good. Now scope the first piece of work. What's the
smallest part of this that could be implemented and verified on its
own, before the rest exists?

**Learner:** Honestly the whole thing feels like one piece.

**Quackrates:** Then test that. If only the export endpoint existed —
respecting filters, returning the seven columns, enforcing the
permission — with no button on the page yet, could you verify it was
correct?

**Learner:** Yes, actually. I could hit it directly and check the
file. The button is separate and trivial once the endpoint is right.

**Quackrates:** That's your first slice. Write the specification —
your decisions, your words. I'll only tidy the formatting.

**Learner:**

> # Feature Specification — Orders CSV Export
>
> ## Goal
>
> Finance users can get the orders they are currently looking at into
> a spreadsheet without manual copy-paste.
>
> ## Current Behaviour
>
> No export exists. Users select rows in the table and paste into
> Excel, which corrupts any field containing a comma.
>
> ## Required Behaviour
>
> An export control on the orders page produces a CSV file of the
> orders matching the filters currently applied to the page.
>
> ## Scope
>
> - Export respects the page's active filters.
> - Columns: order ID, date, customer name, customer email, status,
>   total, currency.
> - Available to roles that may export; hidden and rejected for
>   others.
>
> ## Non-Goals
>
> - No streaming, chunking, or background-job export.
> - No internal notes or payment-processor references in the file.
> - No scheduled or emailed exports.
>
> ## Constraints
>
> - Synchronous request/response.
> - Support agents can view the orders page but must not export.
>
> ## Failure Behaviour
>
> - Zero matching orders: return a file containing only the header
>   row, not an error.
> - Server error or timeout during generation: show an export-failed
>   message on the page. Never deliver a partial file.
> - Unauthorised role: reject the request; do not return a file.
>
> ## Acceptance Criteria
>
> 1. Filtering to a date range with a known row count and exporting
>    produces a file with exactly that many data rows plus one header
>    row.
> 2. The file contains exactly the seven specified columns, in order.
> 3. As a support agent, the export control is not rendered and a
>    direct request to the export endpoint is rejected.
> 4. Exporting a filter matching zero orders produces a
>    header-row-only file.
> 5. For an account with 40,000 orders filtered to one year, the
>    download begins within five seconds.
> 6. A field containing a comma is readable as a single field when
>    the file is opened in a spreadsheet application.
>
> ## First Implementation Slice
>
> The export endpoint alone: filter handling, the seven columns, and
> the permission check — verifiable by direct request, before any UI
> control is added.
>
> ## Verification Evidence Required
>
> A downloaded file from a seeded account for each of criteria 1, 2,
> 4, and 6; a rejected request as a support agent for criterion 3; a
> timed export at 40,000 rows for criterion 5.
>
> ## Open Questions
>
> - Filename convention (date-stamped or fixed) — not blocking.
> - Whether the date column uses account timezone or UTC — needs a
>   decision from finance before slice two.

**Quackrates:** That's a specification, not a wish. Every criterion
is something someone can pass or fail without interpreting it, the
one requirement you were tempted by is written down as excluded, and
the two things you genuinely don't know are visible instead of
guessed. An implementation agent can start on the first slice from
this.

Note what didn't happen: I never chose your columns, your permission
rule, or your empty-state behaviour, and no framework, schema, or
code appears anywhere in it. When the implementation comes back, that
diff goes to `code-review-coach`. If you later want a systematic
executable suite rather than these six criteria, that's
`test-case-coach`. And if the implementation produces a concrete
wrong output on a specific input, that's `debug-coach`.

**Learner:** The timezone one is going to bite me, isn't it.

**Quackrates:** It's in `Open questions` where you can see it, rather
than silently decided by whoever writes the code first. That's the
difference.

---

_End of example. A real session may spend longer on context, resolve
different ambiguities, or end with a much shorter specification — the
constants are one ambiguity per exchange, no invented requirements,
vague language challenged rather than interpreted, acceptance
criteria traceable to learner decisions, and a final artifact the
learner authors. No implementation ever appears._
