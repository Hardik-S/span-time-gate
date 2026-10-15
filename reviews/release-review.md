# Independent release review: issue #3 / PR #2

**Decision: PASS**
**Reviewed commit:** `196050b628d2f8aae02a7c47ad82a9f17a216e9c`
**Review date:** 2026-10-15 (America/Toronto)
**Scope:** `CONTRACT.md`, PR #2 implementation, user-facing docs/examples, fresh-install behavior, tests, and latest CI for the reviewed SHA. No implementation, merge, tag, release, or outreach actions were taken.

## Contract findings

The reviewed implementation matches the frozen contract:

- Policy and rows require exactly their specified keys; booleans, floats, negative values, duplicate keys, non-finite constants, malformed JSON, invalid UTF-8, blank lines, and oversized integers are rejected.
- Nonnegative integers through `10^30` are accepted without float conversion. Equality with the duration budget is valid; only durations strictly greater than the budget are `too_long`.
- Reversed spans produce only a `reversed` finding. Findings retain input order and line numbers.
- CR, LF, and CRLF are supported; an empty spans file is valid. Both input files are read and validated before a result is emitted.
- Invalid input returns exactly `{"status":"invalid_input"}` on stdout, empty stderr, and exit 2. Normal results use the documented status, count, findings, and exit codes.
- README scope and limitations accurately describe synthetic normalized same-clock millisecond fixtures, memory proportional to input, and excluded clock-skew, distributed-truth, containment, benchmark, provider-adapter, runtime, and provenance claims. The launch checklist matches observed results.

## Verification evidence

- Fresh isolated virtual environment, Python 3.13.1: `python -m pip install --disable-pip-version-check '.[test]'` — PASS; package wheel built and installed successfully.
- Fresh-install test command: `python -m pytest -q` — **27 passed**, no skips (`0.76s`).
- Installed CLI README demos:
  - `span-time-gate examples/within-budget.jsonl examples/within-budget-policy.json` — exact documented JSON, exit 0.
  - `span-time-gate examples/violations.jsonl examples/violations-policy.json` — exact documented JSON, exit 1.
  - `span-time-gate examples/invalid.jsonl examples/invalid-policy.json` — exact invalid JSON, empty stderr, exit 2.
- Eight direct adversarial CLI checks — all PASS: inclusive `10^30`; reject `10^30 + 1`; duplicate-key, boolean, and non-finite JSON rejection; Unicode line-separator rejection; CR and CRLF acceptance; malformed suffix no-echo (including no path or private marker in output).
- Latest PR CI run for this SHA: [run 38791411319](https://github.com/Hardik-S/span-time-gate/actions/runs/38791411319) — **4/4 jobs passed**: Ubuntu and Windows on Python 3.10 and 3.13. Latest push CI for the same SHA, [run 38791385990](https://github.com/Hardik-S/span-time-gate/actions/runs/38791385990), also passed all four jobs.
- Target SHA and branch were confirmed as PR #2 head `feat/strict-span-time-gate`; `origin` points to `Hardik-S/span-time-gate`.

## Commands used

```powershell
python -m venv $reviewVenv
& (Join-Path $reviewVenv 'Scripts\python.exe') -m pip install --disable-pip-version-check '.[test]'
& (Join-Path $reviewVenv 'Scripts\python.exe') -m pytest -q
& (Join-Path $reviewVenv 'Scripts\span-time-gate.exe') examples/within-budget.jsonl examples/within-budget-policy.json
& (Join-Path $reviewVenv 'Scripts\span-time-gate.exe') examples/violations.jsonl examples/violations-policy.json
& (Join-Path $reviewVenv 'Scripts\span-time-gate.exe') examples/invalid.jsonl examples/invalid-policy.json
```

The adversarial cases were run against the installed entry point with temporary fixtures outside the repository.

## Limits and remaining release gates

This review establishes behavior on the local Windows host with Python 3.13.1 and CI coverage on the four listed matrix jobs; it is not an independent run on Python 3.10. It does not validate third-party downstream environments, performance at arbitrary input sizes, clock correctness, tracing integrations, or any runtime/provenance claims beyond the explicit fixture scope. The repository launch checklist still makes tagging `v0.1.0` contingent on pull-request review and approval; this review itself does not merge or release the project.
