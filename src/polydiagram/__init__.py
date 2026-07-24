"""Polydiagram — reference validators for the Polydiagram open specification.

Business flows as governed architecture artifacts with telemetry binding:
flow descriptors plus a layered diagram language (Topology / Layer / View).

Spec, schemas, examples, and the companion preprint:
https://github.com/azimuth-ink/polydiagram
Archived: https://doi.org/10.5281/zenodo.21524083

Console entry points:
  polydiagram-flows    — validate *.flow.yaml against the Flow schema + rules R1–R6
  polydiagram-diagram  — validate Topology/Layer/View documents, rules DG1–DG9

The canonical module sources live in the repository's ``tools/`` directory and
are mapped into this package at build time; ``spec/schemas/`` is likewise
mapped to ``polydiagram/schemas/``.
"""

__version__ = "0.2.2"
