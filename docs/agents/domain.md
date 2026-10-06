# Domain documentation

This is a single-context repository for a GitHub profile banner and its portable production skill. There is no monorepo or need for a context map.

## Read the relevant source

- `README.md` embeds `artifacts/banner.svg`, the single profile banner artifact. The repository root contains no duplicate or symbolic-link copy.
- [Banner production references](../references.md) records sources and lasting design decisions.
- [Banner workflow](../banner-build.md) describes generic authoring inputs, assembly, and the bundled neutral example.
- [Animated Foliage Banner](../../skills/animated-foliage-banner/SKILL.md) defines the public workflow, including flat-image input.
- [The scene-contract check](../../skills/animated-foliage-banner/scripts/check_fur_motion.py) validates the documented input structure; it is not a general SVG validator or a visual fidelity check.

If `CONTEXT.md` or relevant files in `docs/adr/` exist later, read them before changing the corresponding concepts or decisions. Create them only when actual domain work warrants them; do not create empty placeholders. Keep their terminology consistent and identify conflicts with an existing decision.

## Documentation, task records, and logs

Public documentation describes enduring behavior, techniques, sources, and repository conventions. Write it in English, along with code comments and image descriptions. Keep user identities, private artwork inputs, local paths, and source metadata out of public documentation and reusable skills. Only explicitly authorized final artwork may carry personal content.

Specifications and issue records belong in the dedicated `.scratch/` tracker. Keep status, acceptance criteria, and task discussion there.

Dated reviews, validation runs, and troubleshooting transcripts belong in `logs/`. Both local task records and execution logs use Simplified Chinese; retain literal commands, identifiers, and captured output. Do not place run reports in `docs/` or require ignored local records to understand a public document. Extract a useful general rule into documentation instead of publishing its execution transcript.

Before publication, confirm that local source inputs, task records, execution logs, and agent instructions are absent from `git ls-files`. Ignore rules do not remove already tracked content; see [Git's ignore FAQ](https://github.com/git/htmldocs/blob/gh-pages/gitfaq.adoc).
