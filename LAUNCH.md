# Launch checklist

- [ ] Install from a fresh environment with `python -m pip install '.[test]'`.
- [ ] Run the documented within-budget demo and confirm exit 0 plus its exact output.
- [ ] Run the documented violations demo and confirm exit 1 plus its exact output.
- [ ] Run the documented invalid demo and confirm exit 2, exact invalid JSON on stdout, and empty stderr.
- [ ] Run `python -m pytest -q`; confirm no tests are skipped.
- [ ] Confirm Ubuntu and Windows jobs pass on Python 3.10 and 3.13.
- [ ] Review the synthetic-fixture scope and limitations in README.md.
- [ ] Tag `v0.1.0` only after this checklist and the pull request are reviewed and approved.
