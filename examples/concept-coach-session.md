# Example Concept Coach Session

This is an illustrative `concept-coach` session, written to show the
skill's flow: the learner's existing partial understanding is used
rather than re-collected, one focused question at a time, a tiny
concrete situation exposes the actual gap, the smallest necessary
explanation is given once the gap is genuinely a missing fact rather
than a missing inference, and understanding is checked with a nearby
application before the session closes. It is not a transcript of an
actual chat log — it is a realistic example built to match the
behaviour described in
[`skills/concept-coach/SKILL.md`](../skills/concept-coach/SKILL.md).

This is deliberately not a DSA session, and no code is delivered as a
solution to a real task — only a small didactic snippet used to make
the concept observable. The concept is dependency injection.

---

**Learner:** I keep running into "dependency injection" in code
reviews and tutorials, and I sort of nod along, but I don't actually
get what problem it's solving. I'm not working on anything specific
right now — I just want to actually understand it.

**Quackrates:** Fair enough — no code needed for this one yet.
Imagine a class called `PaymentService` that, inside its own
constructor, creates a `StripeGateway` object itself and holds onto
it. Nothing else changes that. What do you expect happens if you want
to test `PaymentService` without actually calling Stripe?

**Learner:** I guess... you'd have to call Stripe? Or mock something?

**Quackrates:** You said "mock something." If `PaymentService`
creates `StripeGateway` internally, where could your test replace
that gateway without changing `PaymentService`?

**Learner:** Hm. Actually I'm not sure how you'd replace it, since
`PaymentService` builds its own `StripeGateway` internally. You'd
have to change the class itself to swap it out.

**Quackrates:** That's the actual pressure. Nothing is broken about
`PaymentService` — it works fine in production. But right now, is
"which gateway `PaymentService` talks to" a decision `PaymentService`
makes for itself, or a decision something outside of it makes?

**Learner:** `PaymentService` makes it, since it's the one constructing
`StripeGateway`.

**Quackrates:** Right. Now here's the small case:

```python
class PaymentService:
    def __init__(self):
        self.gateway = StripeGateway()
```

versus:

```python
class PaymentService:
    def __init__(self, gateway):
        self.gateway = gateway
```

In the second version, who decides which gateway `PaymentService`
ends up using?

**Learner:** Whoever creates the `PaymentService` — they pass in
whatever gateway they want.

**Quackrates:** And in a test, what would you pass in?

**Learner:** A fake gateway that just records calls instead of
actually hitting Stripe.

**Quackrates:** That's dependency injection — not a framework, not a
container, just that second constructor shape. The class stops
deciding its own collaborators and instead receives them. Before I
say more: does "injection" sound like it's describing something a
tool does to your code, or something your code's own design is
choosing to allow?

**Learner:** Something the design allows, I think? Nothing's actually
being injected by some external machinery, it's just... a parameter.

**Quackrates:** Exactly that. The "injection" is just passing the
dependency in from outside instead of constructing it inside. The
frameworks and containers people also call "dependency injection" are
optional automation for wiring those parameters up in a large system
— they're not the concept itself. Given that, here's a nearby check:
suppose a `ReportGenerator` class currently does `self.db =
PostgresConnection()` inside its own constructor. What's the smallest
change that would let a test give it a fake database instead?

**Learner:** Change the constructor to take a `db` parameter and store
whatever gets passed in, instead of creating the connection itself.

**Quackrates:** And what would you expect to go wrong if
`ReportGenerator` also called `self.db.connect()` immediately inside
that same constructor, before any test even ran?

**Learner:** ...that would still try to hit a real database during the
test, even though we passed in a fake one — unless the fake also has a
`.connect()` method that does nothing.

**Quackrates:** That's exactly the kind of edge the concept exposes
once it's actually understood rather than recited — swapping the
constructor argument isn't enough on its own if something inside still
assumes a specific real implementation. Where do you think that
leaves the rule for what a class *should* assume about a dependency
it's been handed?

**Learner:** I guess it should only assume the shape or interface it
needs — not that it's specifically Postgres or specifically Stripe.

**Quackrates:** That's the concept, in your own words, holding up
under a variation you hadn't been told about in advance.

---

_End of example. A real session may take longer to reach the
pressure, use a different starting concept, or need an explicit
missing-fact explanation if the learner has no nearby intuition to
predict from — the constants are using what the learner already said,
one focused question at a time, a tiny concrete situation before any
lecture, and a nearby check before the concept is treated as
established. No production system is built, and no real task is
solved along the way._
