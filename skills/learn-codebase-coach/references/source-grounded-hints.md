# Source-Grounded Hints

Use this reference for coding hints, documentation questions, unfamiliar APIs, version-sensitive behavior, errors, regressions, and disputed advice.

## Research workflow

1. Identify the exact language, library, API, concept, error, and likely installed version.
2. Inspect the learner's code and error text first. Do not invent missing details.
3. Search current sources and open the underlying pages. Do not rely on search-result snippets.
4. Prefer sources in this order:
   1. Official language, framework, library, or platform documentation.
   2. Canonical project repository: source, tests, examples, releases, issues, and discussions.
   3. Maintainer-authored migration guides, design notes, or answers.
   4. Reputable standards and vendor resources such as MDN, language enhancement proposals, RFCs, Microsoft Learn, Google Developers, AWS documentation, and official project forums.
   5. Stack Overflow or community guidance with reproducible reasoning and relevant versions.
   6. Independent explanations only when stronger sources do not answer the question.
5. Prefer behavior matching the learner's installed version. Report disagreements and uncertainty.
6. Give the smallest useful hint, include at least one direct and verified URL that supports it, then wait for the learner's attempt.

Use repository evidence to clarify actual implementation, undocumented edge cases, regressions, and version changes. Prefer stable links to tagged files, commits, releases, or specific comments. State whether an issue is open, closed, fixed, proposed, or unreleased. Treat source and tests as implementation evidence, not automatically as public API guarantees.

Use community guidance only as a supplement. Check dates, versions, reasoning, and whether supported behavior has changed. Label outdated, insecure, or version-specific advice.

## Source labels

Label material as appropriate:

- **Primary/official**
- **Maintainer evidence**
- **Community guidance**
- **Independent explanation**

Do not force every category into every hint. Include only evidence that helps, but include at least one source URL in every hint.

## URL requirement

- Include at least one directly useful URL in every hint, including Level 1 direction hints.
- Prefer the exact official documentation section for the relevant concept, API, error, or version.
- If official documentation is insufficient, link to stable evidence in the canonical repository, then maintainer or reputable community guidance.
- Link directly to the supporting page, section, tagged file, release, issue comment, or answer. Avoid search-result pages and generic homepages when a precise URL exists.
- Verify that the page supports the hint before sending it. Never invent or guess a URL.
- If source access fails and no URL can be verified, explain the verification problem and pause instead of presenting an unsourced hint.

## Hint ladder

Start at Level 1 unless the learner asks for a stronger hint:

1. **Direction:** identify the concept or API.
2. **Documentation clue:** summarize or briefly quote the relevant documented behavior and connect it to the task.
3. **Structural hint:** provide method names, shapes, types, verbal control flow, pseudocode, or a small unrelated example while withholding the task's implementation. Do not provide a copy-paste snippet for the learner's task.
4. **Near-solution:** identify the exact correction but leave the edit to the learner.
5. **Complete solution:** provide only after the learner explicitly exits coaching mode.

For assignments, do not reproduce the complete answer at Levels 1–4.

## Suggested response shape

Keep the response compact and adapt headings to the amount of evidence:

- **Hint:** one actionable clue at the current level.
- **Helpful URL:** at least one direct, verified link, preferably to official documentation. This item is mandatory for every hint.
- **What the sources say:** when useful, add a short quotation or clearly labeled paraphrase with a source label.
- **How it applies:** connect the evidence to the learner's code or error without finishing the task.
- **Your next step:** one action for the learner and any output to report.
- **Caveat:** version differences, deprecation, open issues, conflicts, security concerns, or uncertainty when relevant.

## Citation rules

- Quote only the minimum supporting text and preserve it exactly.
- Mark summaries as paraphrases; never present them as quotations.
- Put a direct link next to each quoted or factual source claim.
- Include the page title, source type, and relevant version or date when useful.
- Do not fabricate wording, authorship, status, votes, versions, or links.
- Respect source quotation and copyright limits.

## Quality gate

Before sending a hint, verify that it contains at least one directly useful URL, the source supports the claim, the link is direct, version and date relevance were considered, community advice is labeled, quotations are exact and short, and the response remains within the active coaching level.
