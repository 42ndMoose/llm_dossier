---
id: "00-start-here"
order: "000000"
number: ""
level: 1
title: "Start Here"
keywords:
  - "navigation"
  - "toc"
  - "claims ledger"
summary:
  - "Landing page for humans and LLMs."
  - "Explains the public pages, source files, and internal claim markers."
related: []
exclude_from_source: true
---

This build keeps the token-saving navigation model, but tightens the dossier into a cleaner paper-like structure.

Key rules:
- Read section pages through the table of contents instead of loading everything at once.
- Patch the smallest relevant file in `/dossier/parts/`.
- Public pages are written for reading. The internal `[C]` markers are only there to build the claims ledger and source map. They are stripped from the public HTML.

Navigation:
- TOC: `./index.html`
- Claims Ledger: `./claims.html`
- Claims JSON: `./claims.json`
- Claims JSON (min): `./claims.min.json`

Editorial posture:
- This rebuild integrates the existing repo structure with the uploaded source-note papers.
- It is a structural and editorial integration, not a fresh from-scratch re-verification of every claim in the dossier.
- Where detail would bloat the main narrative, it is compressed into short, proportionate subsections instead of taking over the whole dossier.
