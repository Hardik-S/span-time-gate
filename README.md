# Span Time Gate

`span-time-gate` is an offline Python 3.10+ command-line check for normalized span timing fixtures. It uses only the Python standard library at runtime.

## Install and run

```console
python -m pip install '.[test]'
span-time-gate examples/within-budget.jsonl examples/within-budget-policy.json
```

A within-budget run exits 0 and prints `{"status":"within_budget","record_count":2,"findings":[]}`. A violation exits 1. Invalid input exits 2 and prints only `{"status":"invalid_input"}` to stdout, with no stderr. The tool validates both complete files before producing any result.

## Demonstrations

With the violation fixture:

```console
span-time-gate examples/violations.jsonl examples/violations-policy.json
```

Expected output: `{"status":"violations","record_count":2,"findings":[{"line":1,"kind":"too_long"},{"line":2,"kind":"reversed"}]}` and exit 1.

With the invalid fixture, which contains a blank JSONL line:

```console
span-time-gate examples/invalid.jsonl examples/invalid-policy.json
```

Expected output: `{"status":"invalid_input"}` and exit 2.

## Input and output

The policy is exactly `{"max_duration_ms":N}`. Each nonempty JSONL line is exactly `{"start_ms":N,"end_ms":N}`. Values are nonnegative JSON integers (never booleans), at most `10^30`. Duplicate keys, floats, non-finite constants, unknown/missing fields, blank lines, malformed JSON, invalid UTF-8, and oversized integers are rejected. LF, CRLF, and CR line endings are accepted; an empty spans file is valid.

A row is `reversed` when its end precedes its start. Otherwise it is `too_long` only when its duration is strictly greater than the budget, so equality is within budget. Reversed rows receive only the reversed finding. Findings are ordered by input line. Invalid results intentionally disclose no paths, values, source text, hashes, or exceptions; record counts and finding line numbers are the only source-derived details disclosed on valid input.

This checks synthetic normalized same-clock millisecond fixtures only. It does not correct clock skew, establish distributed timing truth, validate parent containment, benchmark performance, adapt tracing providers, execute agents, or establish provenance. Memory use grows with input size.

## Development

```console
python -m pip install -e '.[test]'
python -m pytest -q
```
