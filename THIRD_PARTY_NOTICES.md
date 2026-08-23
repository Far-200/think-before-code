# Third-Party Notices and Provenance

This file records the repository lineage, source material, authoring assistance, and local modifications for `mahkameh13/think-before-code`.

Review date: 2026-08-23.

## Classification

| Relationship | Repository and pinned revision | Material or role | License |
| --- | --- | --- | --- |
| Base repository | [Far-200/think-before-code @ c733ae6](https://github.com/Far-200/think-before-code/tree/c733ae6ee4f799b9c11a345cfb692453796f26cd) | Repository structure and the original Think Before Code skill suite. The fork also contains later first-party additions. | MIT; Copyright (c) 2026 Farhaan |
| Direct adaptation | [rodbv/socratic-skills @ dda051c](https://github.com/rodbv/socratic-skills/tree/dda051c2b4390d19d32b33edc222abbfa39927ac), specifically [`skills/guide-me/SKILL.md`](https://github.com/rodbv/socratic-skills/blob/dda051c2b4390d19d32b33edc222abbfa39927ac/skills/guide-me/SKILL.md) | Guided implementation structure used in `learn-codebase-coach`: finding a concrete artifact, selecting a testing policy, decomposing work, learner-written code, and diff inspection. | MIT; Copyright (c) 2026 Rodrigo Vieira |
| Direct adaptation | [ktaletsk/learn-codebase @ cbc0304](https://github.com/ktaletsk/learn-codebase/tree/cbc0304609e76041f7f29b3ae9a1e3f1a16e07ad), specifically [`SKILL.md`](https://github.com/ktaletsk/learn-codebase/blob/cbc0304609e76041f7f29b3ae9a1e3f1a16e07ad/SKILL.md) | Socratic codebase exploration, prediction and active recall, learning-journal concepts, mastery checks, and spaced review used in `learn-codebase-coach`. | MIT; Copyright (c) 2026 Konstantin Taletskiy |
| First-party input | `docs-grounded-code-hints` | A user-authored local skill used as an additional input to `learn-codebase-coach`. No external repository was identified. | First-party; no third-party notice required |
| Authoring assistance only | [mattpocock/skills @ 5b15a47](https://github.com/mattpocock/skills/tree/5b15a47f2d7150f545fbcacbfe381787fc0230dc), specifically [`write-a-skill`](https://github.com/mattpocock/skills/blob/5b15a47f2d7150f545fbcacbfe381787fc0230dc/skills/productivity/write-a-skill/SKILL.md) | Used as a process/scaffolding skill while authoring `learn-by-googling`. No verbatim or substantial material from this authoring skill was identified in the published skill. | MIT; Copyright (c) 2026 Matt Pocock |
| Authoring assistance only | [Galaxy-Dawn/claude-scholar @ 2847aa1](https://github.com/Galaxy-Dawn/claude-scholar/tree/2847aa1735205ef31e71068d45b902f3b228b98a), specifically `skill-improver` | Used to review and improve `learn-by-googling`. No verbatim or substantial material from the improver skill was identified in the published skill. | MIT; Copyright (c) 2026 Gaorui Zhang |

“Authoring assistance only” is recorded for transparency. It does not mean that the authoring tool's instructions were copied into this repository.

## Local modifications

The local work includes:

- combining the codebase-learning, guided-implementation, and documentation-grounded-hint workflows into `learn-codebase-coach`;
- adapting the combined workflow for Codex-compatible Agent Skills;
- adding explicit explore/build mode routing, URL requirements, reference documents, and OpenAI agent metadata;
- authoring `learn-by-googling` as a source-driven learning workflow and adding its systems-thinking checks;
- adding both skills to repository documentation, activation evaluations, and the deterministic Find Your Coach router.

The resulting files are modified works and are not endorsed by the upstream authors.

## Indirect upstream acknowledgements

These projects were not directly consulted or copied during the local skill-writing sessions, but direct upstream projects acknowledge them:

- `ktaletsk/learn-codebase` credits [hluaguo/learn-faster-kit](https://github.com/hluaguo/learn-faster-kit) and [m98/fluent](https://github.com/m98/fluent) as inspirations.
- `rodbv/socratic-skills` credits [mattpocock/skills](https://github.com/mattpocock/skills), including `grill-me`, as inspiration.

They are listed to preserve the provenance chain, not as claims that their material was directly incorporated here.

## License texts for redistributed or adapted material

### Far-200/think-before-code

MIT License

Copyright (c) 2026 Farhaan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

### rodbv/socratic-skills

MIT License

Copyright (c) 2026 Rodrigo Vieira

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

### ktaletsk/learn-codebase

MIT License

Copyright (c) 2026 Konstantin Taletskiy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Compliance note

The repository-level [`LICENSE`](./LICENSE) remains the license for this distribution. This notice preserves the copyright and permission notices for substantial third-party material and records non-copying authoring assistance separately.

This provenance review is a good-faith engineering record, not legal advice.
