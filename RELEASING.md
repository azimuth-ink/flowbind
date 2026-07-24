# Releasing

## Versioning
- Repo releases are semver git tags (`vX.Y.Z`). The repo version and the
  schema `apiVersion`s evolve independently: a repo release may or may not
  bump a schema version; schema versioning rules live in the spec documents.

## Procedure
1. Ensure `main` is green (the `validate` workflow).
2. Tag and push:
   ```bash
   git tag -a v0.1.0 -m "v0.1.0"
   git push origin v0.1.0
   ```
3. The `release` workflow re-runs every gate, builds the source zip and the
   paper PDF (from `paper/polymorphic-diagram-preprint.md` via `tools/typeset_paper.py`), and publishes a
   GitHub Release with those assets.
4. If the Zenodo–GitHub integration is enabled for this repository, Zenodo
   archives the release and mints a DOI automatically.

## DOIs
Zenodo mints a **version DOI** per release and a **concept DOI** that always
resolves to the latest version. Cite the **concept DOI** in `CITATION.cff`,
the README badge, and the paper's Data & Code Availability line so citations
never go stale. After the first release: add the DOI to `CITATION.cff`
(`doi:` field), replace the README badge placeholder with Zenodo's badge
markdown, update the paper, and rebuild the PDF
(`python3 tools/typeset_paper.py paper/polymorphic-diagram-preprint.md polymorphic-diagram-preprint-vX_Y.pdf`).
