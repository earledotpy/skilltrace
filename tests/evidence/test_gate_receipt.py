"""Gate-run receipt seam tests (issue #202).

One module owns schema constants, build, validate, and for_share;
submit and portfolio are thin adapters. Tests hit the seam directly:
build / validate / for_share plus the CRLF normalization contract.
"""

from __future__ import annotations

import hashlib

import pytest


def _mod():
    from skilltrace.evidence import gate_receipt

    return gate_receipt


def _fake_root(tmp_path):
    (tmp_path / "evidence" / "math").mkdir(parents=True)
    checker = tmp_path / "evidence" / "math" / "check_set_001.py"
    checker.write_text("print('ok')", encoding="utf-8")
    return tmp_path


def test_build_captures_argv_inputs_exit_class_and_hashes(tmp_path):
    gr = _mod()
    root = _fake_root(tmp_path)
    receipt = gr.build(
        "python evidence/math/check_set_001.py",
        "evidence/math/set_001.md",
        0,
        "all checks passed\n",
        "",
        root,
        lambda p: p.is_file(),
    )
    assert receipt["command_argv"] == ["python", "evidence/math/check_set_001.py"]
    assert receipt["inputs"] == [
        "evidence/math/set_001.md",
        "evidence/math/check_set_001.py",
    ]
    assert receipt["exit_class"] == "passed"
    assert receipt["exit_code"] == 0
    assert receipt["stdout_hash"].startswith("sha256:")
    assert "stderr_hash" not in receipt
    assert "tool" not in receipt and "version" not in receipt


def test_build_failed_exit_class_and_silent_run_has_no_hashes(tmp_path):
    gr = _mod()
    receipt = gr.build("false", "evidence/a.md", 1, "", "", None, None)
    assert receipt["exit_class"] == "failed"
    assert "stdout_hash" not in receipt
    assert "stderr_hash" not in receipt


def test_build_normalizes_crlf_before_hashing(tmp_path):
    """CRLF and LF captures hash identically (builder/runner contract)."""
    gr = _mod()
    crlf = gr.build("false", "evidence/a.md", 0, "line one\r\nline two\r\n", "", None, None)
    lf = gr.build("false", "evidence/a.md", 0, "line one\nline two\n", "", None, None)
    assert crlf["stdout_hash"] == lf["stdout_hash"]
    expected = "sha256:" + hashlib.sha256("line one\nline two\n".encode("utf-8")).hexdigest()
    assert lf["stdout_hash"] == expected


def test_normalize_stream_is_single_place(tmp_path):
    gr = _mod()
    assert gr.normalize_stream("a\r\nb\n") == "a\nb\n"
    # The runner and the hasher share this funnel: normalizing twice is stable.
    assert gr.normalize_stream(gr.normalize_stream("a\r\nb\n")) == "a\nb\n"


def test_validate_round_trips_built_receipt(tmp_path):
    gr = _mod()
    root = _fake_root(tmp_path)
    built = gr.build(
        "python evidence/math/check_set_001.py",
        "evidence/math/set_001.md",
        0,
        "ok\n",
        "",
        root,
        lambda p: p.is_file(),
    )
    validated = gr.validate(built)
    assert validated == built
    assert validated is not built


def test_validate_absent_is_none():
    gr = _mod()
    assert gr.validate(None) is None


def test_validate_rejects_unknown_keys_empty_argv_and_bad_hash():
    from skilltrace.evidence._schema import EvidenceLoadError

    gr = _mod()
    good = {
        "command_argv": ["python", "check.py"],
        "inputs": ["evidence/a.md"],
        "exit_class": "passed",
    }
    with pytest.raises(EvidenceLoadError):
        gr.validate({**good, "bogus": 1})
    with pytest.raises(EvidenceLoadError):
        gr.validate({**good, "command_argv": []})
    with pytest.raises(EvidenceLoadError):
        gr.validate({**good, "exit_class": "timeout"})
    with pytest.raises(EvidenceLoadError):
        gr.validate({**good, "stdout_hash": "abc123"})
    with pytest.raises(EvidenceLoadError):
        gr.validate({**good, "tool": "pytest"})


def test_for_share_drops_whole_receipt_without_paths():
    gr = _mod()
    receipt = {
        "command_argv": ["python", "check.py"],
        "inputs": ["evidence/a.md"],
        "exit_class": "passed",
        "exit_code": 0,
        "stdout_hash": "sha256:" + "a" * 64,
    }
    assert gr.for_share(receipt, include_paths=False) is None
    assert gr.for_share(None, include_paths=False) is None
    shared = gr.for_share(receipt, include_paths=True)
    assert shared == receipt
    assert shared is not receipt
