"""Command-line interface for span-time-gate."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MAX_VALUE = 10**30


class InvalidInput(Exception):
    """Raised when an input file violates the frozen schema."""


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise InvalidInput


def _load_json(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (ValueError, RecursionError):
        raise InvalidInput from None


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= MAX_VALUE


def _read(path: str) -> str:
    try:
        return Path(path).read_bytes().decode("utf-8", errors="strict")
    except (OSError, UnicodeError, ValueError):
        raise InvalidInput from None


def evaluate(spans_text: str, policy_text: str) -> dict[str, Any]:
    policy = _load_json(policy_text)
    if not isinstance(policy, dict) or set(policy) != {"max_duration_ms"}:
        raise InvalidInput
    budget = policy["max_duration_ms"]
    if not _integer(budget):
        raise InvalidInput

    findings: list[dict[str, Any]] = []
    record_count = 0
    if spans_text:
        # Accept only the contract line endings, without treating Unicode separators as newlines.
        lines = re.split(r"\r\n|\r|\n", spans_text)
        if lines and lines[-1] == "":
            lines.pop()  # A single final line terminator is conventional JSONL.
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                raise InvalidInput
            row = _load_json(line)
            if not isinstance(row, dict) or set(row) != {"start_ms", "end_ms"}:
                raise InvalidInput
            start = row["start_ms"]
            end = row["end_ms"]
            if not _integer(start) or not _integer(end):
                raise InvalidInput
            record_count += 1
            if end < start:
                findings.append({"line": line_number, "kind": "reversed"})
            elif end - start > budget:
                findings.append({"line": line_number, "kind": "too_long"})
    return {
        "status": "violations" if findings else "within_budget",
        "record_count": record_count,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate normalized span times against a duration budget.")
    parser.add_argument("spans_jsonl")
    parser.add_argument("policy_json")
    args = parser.parse_args()

    try:
        result = evaluate(_read(args.spans_jsonl), _read(args.policy_json))
        code = 1 if result["status"] == "violations" else 0
    except InvalidInput:
        result = {"status": "invalid_input"}
        code = 2
    sys.stdout.write(json.dumps(result, separators=(",", ":"), ensure_ascii=True) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
