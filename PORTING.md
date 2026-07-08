# Porting SCHEMA-RASPP to Python 3

This fork modernizes the original [mattasmith/SCHEMA-RASPP](https://github.com/mattasmith/SCHEMA-RASPP)
(last upstream commit 2013, Python 2) to run on Python 3, with a regression test
suite that pins the numerical behaviour to the original tool.

## Summary

- The package is pure standard library (no numpy/biopython), ~9 modules.
- The Python 2→3 conversion (`print`→`print()`, `has_key`→`in`,
  `raise X, msg`→`raise X(msg)`, `string.letters`→`string.ascii_letters`,
  `xrange`→`range`, `except X, e`→`except X as e`) was already done in the
  "first upgrade"/"fixing" commits.
- **Verified faithful.** Running the *original* code under Python 2.7 and this
  port under Python 3 on the bundled β-lactamase example gives **byte-identical**
  output for `pdbseq`, `schemacontacts` (1040 contacts), and `schemaenergy`
  (E and m). An independent from-scratch recomputation of the SCHEMA disruption
  energy also matches. So the port introduced **no numerical regression**.

## One real fix: deterministic RASPP curve

`raspp.curve()` built a **set** of unique results and iterated it directly:

```python
unique_results = set([...])
for (avg_energy, crossovers) in unique_results:   # order differs Py2 vs Py3
```

Set iteration order differs between Python 2 and 3 (and is not guaranteed
stable), so when several crossover patterns share an average-energy value inside
the same average-mutation bin, *which one was reported* depended on the
interpreter rather than the algorithm. Fix:

- iterate `sorted(unique_results)` (deterministic), and
- within a bin keep the lower `(E, m)` — on an energy tie this reports the
  strictly better (lower average-mutation) library.

Effect on the bundled example (`rasppcurve -xo 7 -min 4`): 22 of 24 curve points
are unchanged; 2 tied-energy points now deterministically report a lower-⟨m⟩
design. The curve golden fixture was regenerated from the fixed Python 3 code.

## About the documentation's example energies

The upstream `schema-tools-doc.html` shows `E(13111111)=4`, `E(13121231)=29`,
etc. The code — both the original Python 2 and this port — produces
`20, 107, 62, 67` for the shipped `1G68.pdb` contact map (and `23, 99, 65, 72`
for `1BTL.pdb`). These doc numbers are **stale**: they are not reproduced by the
current code with either shipped structure, and predate the standard SCHEMA
"disruption" energy the code implements (a contact is disruptive when the
chimera's residue pair occurs in no parent). The tests lock the correct,
code-consistent values; treat the 2013 doc numbers as illustrative only.

## Regression tests

```bash
pytest              # fast suite (~2 s)
pytest -m slow      # end-to-end RASPP curve (~1 min)
pytest -m ""        # everything
```

Golden fixtures in `tests/golden/` were captured from the **original Python 2.7**
code (except the RASPP curve, regenerated after the determinism fix). Tests run
the tools via `subprocess` from the repo root, matching real usage. Both
`pytest` and `python -m pytest` work.

## Second fix: rename `pdb.py` -> `pdbfile.py`

The package shipped a top-level module named `pdb.py` (its PDB-structure parser),
which shadows Python's standard-library `pdb` debugger. This broke
`python -m pytest` (pytest imports the stdlib `pdb`) and prevented clean use as a
library. It is now `pdbfile.py`, with `import pdb`/`pdb.X` updated to
`pdbfile` in `schema.py`, `schemacontacts.py`, `schemaenergy.py`,
`schemarandom.py`, `rasppcurve.py`, and `pdbseq.py`. The `-pdb` command-line flag
is unchanged.

## Packaging & CI

- `pyproject.toml` (setuptools, flat `py-modules`, `requires-python>=3.9`, no
  runtime dependencies) makes the project `pip install`-able and exposes console
  commands `schema-contacts`, `schema-energy`, `schema-rasppcurve`,
  `schema-random`, `schema-pdbseq` (the CLI scripts gained `if __name__ ==
  '__main__'` guards so they import cleanly for these entry points; running them
  as `python <script>.py ...` still works). Pytest config lives in the
  `[tool.pytest.ini_options]` table.
- `.github/workflows/ci.yml` runs the full suite on Python 3.9–3.13 and builds
  the wheel/sdist, verifying the console entry points install.

## Known follow-ups (out of scope for this pass)

- `schemarandom.py` uses the `random` module; Python 2 and 3 produce different
  streams for the same seed, so its output is *not* expected to match Py2. Lock a
  Py3-only golden if reproducibility there matters.
```
