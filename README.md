# LLM dossier rebuild

This is a rebuilt version of the `llm-test-pad` dossier structure.

What changed:
- Keeps the parts-driven build pipeline and token-saving public navigation.
- Replaces the casual `Trump 2.0` wording with `Trump's second term` or `the second-term Trump administration`.
- Removes the old Bondi/Comey-specific framing.
- Integrates the uploaded source-note papers into the dossier proportionately instead of letting them sprawl across the whole project.
- Keeps the internal `[C]` markers only as build scaffolding for the claims ledger. They are stripped from the public section pages.

## Structure
- `dossier/parts/` holds the editable source sections.
- `dossier/source.md` is the merged source file generated from the parts.
- `dossier/site/` holds the built public HTML and claim artifacts.
- `tools/` holds the build scripts.

## Build
From the repo root:

```bash
python tools/build_all.py
```

Or run the steps separately:

```bash
python tools/build_source.py
python tools/split_dossier.py dossier/parts dossier/site
python tools/build_claims.py dossier/source.md dossier/site
```
