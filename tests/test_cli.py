import json
import subprocess
import sys
from pathlib import Path

import pytest

from span_time_gate.cli import InvalidInput, evaluate


@pytest.mark.parametrize("budget,duration,status", [(0, 0, "within_budget"), (5, 5, "within_budget"), (5, 6, "violations")])
def test_budget_edges(budget, duration, status):
    result = evaluate(f'{{"start_ms":0,"end_ms":{duration}}}', json.dumps({"max_duration_ms": budget}))
    assert result["status"] == status


def test_reversed_is_only_reversed():
    result = evaluate('{"start_ms":9,"end_ms":2}', '{"max_duration_ms":0}')
    assert result["findings"] == [{"line": 1, "kind": "reversed"}]


def test_large_integer_precision_and_bound():
    n = 10**30
    assert evaluate(f'{{"start_ms":0,"end_ms":{n}}}', f'{{"max_duration_ms":{n}}}')['status'] == 'within_budget'
    with pytest.raises(InvalidInput):
        evaluate(f'{{"start_ms":0,"end_ms":{n + 1}}}', '{"max_duration_ms":0}')


@pytest.mark.parametrize("text", [
    '{"max_duration_ms":true}', '{"max_duration_ms":-1}', '{"max_duration_ms":1.0}',
    '{"max_duration_ms":1,"x":2}', '{"max_duration_ms":1,"max_duration_ms":1}',
    '{"max_duration_ms":NaN}', '[]', '',
])
def test_bad_policy(text):
    with pytest.raises(InvalidInput):
        evaluate('', text)


@pytest.mark.parametrize("row", [
    '{"start_ms":false,"end_ms":0}', '{"start_ms":0,"end_ms":-1}',
    '{"start_ms":0.0,"end_ms":0}', '{"start_ms":0,"end_ms":0,"x":1}',
    '{"start_ms":0,"start_ms":0,"end_ms":0}', '{"start_ms":0}', '{"start_ms":Infinity,"end_ms":0}',
])
def test_bad_rows(row):
    with pytest.raises(InvalidInput):
        evaluate(row, '{"max_duration_ms":0}')


def test_empty_file_and_line_endings():
    assert evaluate('', '{"max_duration_ms":0}') == {"status": "within_budget", "record_count": 0, "findings": []}
    rows = '{"start_ms":0,"end_ms":2}\r{"start_ms":0,"end_ms":0}\r\n{"start_ms":4,"end_ms":1}'
    out = evaluate(rows, '{"max_duration_ms":1}')
    assert out["findings"] == [{"line": 1, "kind": "too_long"}, {"line": 3, "kind": "reversed"}]


@pytest.mark.parametrize("text", ['\n', '{bad}', '{"start_ms":0,"end_ms":0}\n\n'])
def test_malformed_jsonl(text):
    with pytest.raises(InvalidInput):
        evaluate(text, '{"max_duration_ms":0}')


def test_unicode_line_separator_is_not_jsonl_delimiter():
    with pytest.raises(InvalidInput):
        evaluate('{"start_ms":0,"end_ms":0}\u2028{"start_ms":0,"end_ms":0}', '{"max_duration_ms":0}')


def test_invalid_output_does_not_echo_input(tmp_path):
    spans = tmp_path / 'private-spans.jsonl'
    policy = tmp_path / 'private-policy.json'
    spans.write_bytes(b'{"start_ms":0,"end_ms":0}\nSECRET_MARKER')
    policy.write_text('{"max_duration_ms":0}', encoding='utf-8')
    proc = subprocess.run([sys.executable, '-m', 'span_time_gate.cli', str(spans), str(policy)], capture_output=True, text=True)
    assert proc.returncode == 2
    assert proc.stdout == '{"status":"invalid_input"}\n'
    assert proc.stderr == ''
    assert 'SECRET_MARKER' not in proc.stdout + proc.stderr
    assert str(spans) not in proc.stdout + proc.stderr


def test_invalid_utf8_is_rejected(tmp_path):
    spans = tmp_path / 'spans.jsonl'
    policy = tmp_path / 'policy.json'
    spans.write_bytes(b'\xff')
    policy.write_text('{"max_duration_ms":0}', encoding='utf-8')
    proc = subprocess.run([sys.executable, '-m', 'span_time_gate.cli', str(spans), str(policy)], capture_output=True, text=True)
    assert proc.returncode == 2
    assert proc.stdout == '{\"status\":\"invalid_input\"}\n'
    assert proc.stderr == ''


@pytest.mark.parametrize("arguments", [
    [], ["PRIVATE_PATH_MARKER"],
    ["PRIVATE_PATH_MARKER", "PRIVATE_POLICY_MARKER", "PRIVATE_EXTRA_MARKER"],
    ["PRIVATE_PATH_MARKER", "PRIVATE_POLICY_MARKER", "--PRIVATE_UNKNOWN_MARKER"],
    ["--PRIVATE_UNKNOWN_MARKER=PRIVATE_VALUE_MARKER"],
])
def test_invalid_arguments_are_quiet(arguments):
    import sysconfig
    command = Path(sysconfig.get_path("scripts")) / ("span-time-gate.exe" if sys.platform == "win32" else "span-time-gate")
    proc = subprocess.run([str(command), *arguments], capture_output=True, text=True)
    assert proc.returncode == 2
    assert proc.stdout == '{"status":"invalid_input"}\n'
    assert proc.stderr == ''
    assert 'PRIVATE_' not in proc.stdout + proc.stderr


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_remains_successful(flag):
    import sysconfig
    command = Path(sysconfig.get_path("scripts")) / ("span-time-gate.exe" if sys.platform == "win32" else "span-time-gate")
    proc = subprocess.run([str(command), flag], capture_output=True, text=True)
    assert proc.returncode == 0
    assert 'usage:' in proc.stdout
    assert proc.stderr == ''
