# LLM update guide

This file exists to give any generic LLM a direct ruleset for adding or updating dossier content.

## Non-negotiable editing model
- Treat `dossier/parts/*.md` as the only editable source of truth.
- Treat `dossier/source.md` as generated intermediate output.
- Treat `dossier/site/*` as generated public artifacts.
- Never patch generated HTML or JSON unless the task is explicitly about build tooling.

## What to preserve
- Preserve the current section structure unless a new section is clearly warranted.
- Preserve front matter fields and section ordering.
- Preserve the dossier's direct tone and explicit naming of institutions, networks, and actors.
- Preserve proportionality: keep major structural arguments large, keep minor receipts contained.

## What to avoid
- Do not duplicate a claim in several sections.
- Do not insert weak filler that dilutes the stronger claims.
- Do not silently remove sharp framing that is supported by the dossier's evidence model.
- Do not turn source sections into vague summaries when they are meant to carry direct concrete claims.

## Best update workflow for an LLM
1. Read `dossier/parts/0-start-here.md` and the target section file.
2. Decide whether the update belongs in an existing section.
3. Insert the smallest precise patch that preserves section focus.
4. Add or strengthen `[C]` claims where useful.
5. Rebuild the site artifacts.

## If a new topic must be added
Use the same front matter schema used by the existing part files:

```yaml
---
id: "example-id"
order: "001300"
number: "13"
level: 1
title: "Example title"
keywords:
  - "keyword one"
summary:
  - "One-sentence description."
related: []
---
```

Then write the body in the same style as neighboring sections.
