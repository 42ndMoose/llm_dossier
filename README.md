# LLM dossier

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
