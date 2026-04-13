# Dossier automation workflow

This repo is source-driven. The editable source of truth is `dossier/parts/*.md`.
Everything else is generated from those files.

## Source-of-truth rules
- Edit `dossier/parts/*.md` only.
- Do not hand-edit `dossier/source.md`.
- Do not hand-edit `dossier/site/*.html`, `toc.json`, `claims.json`, `claims.min.json`, `claims.html`, `timeline.*`, or `source.html`.
- Rebuild after every source edit.

## What each layer does
- `dossier/parts/*.md`: canonical section files.
- `dossier/source.md`: merged intermediate built from parts.
- `dossier/site/*.html`: public navigable section pages.
- `dossier/site/claims.*`: claims ledger generated from `[C]` markers and evidence blocks.
- `dossier/site/timeline.*`: timeline generated from claims that include `DATE:` metadata.
- `dossier/site/source.html`: clean human reading view of the merged source.

## How an LLM should update the dossier
1. Find the smallest relevant file in `dossier/parts/`.
2. Patch that file instead of spreading the same point across multiple sections.
3. Keep front matter intact: `id`, `order`, `number`, `level`, `title`, `keywords`, `summary`, `related`.
4. Preserve the tone, section scope, and numbering logic.
5. Add claims with evidence using the existing `[C]` format.
6. Avoid duplication. Merge overlapping points into the stronger existing section.
7. Keep significance proportional. Do not let a minor anecdote overshadow a structural section.
8. Rebuild the repo artifacts.

## Claim block format
A claim can be written as a sentence ending with `[C]`. The lines under it until the next blank line are treated as its evidence block.

Example:

```md
A coordinated advertiser-enforcement layer standardized monetization risk categories across major platforms. [C]
DATE: 2024-06-01
TITLE: Brand-safety coordination as enforcement layer
TAGS: garm, advertisers, censorship
NOTE: Keep this tied to documented policies, taxonomies, and enforcement hooks.
Evidence:
- https://example.com/source-one
- https://example.com/source-two
```

Optional metadata inside the evidence block:
- `DATE: YYYY-MM-DD`
- `TITLE:`
- `TAGS:` comma-separated
- `NOTE:` short nuance

## When to create a new part file
Create a new `dossier/parts/*.md` file only when:
- the topic is structurally distinct,
- it cannot fit cleanly into an existing section,
- and it is substantial enough to justify its own page.

If you create a new part file, give it front matter matching the existing pattern and place it in the right `order`.

## Build commands
From repo root:

```bash
python tools/build_all.py
```

Or step by step:

```bash
python tools/build_source.py
python tools/split_dossier.py dossier/parts dossier/site
python tools/build_claims.py dossier/source.md dossier/site
python tools/build_timeline.py dossier/site
python tools/build_source_html.py dossier/source.md dossier/site/source.html
```
