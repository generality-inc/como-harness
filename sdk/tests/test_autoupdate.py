"""Auto-update logic: it must be fail-silent, throttled, opt-out-able, and only
fast-forward when genuinely behind. We stub ``_git`` so no real network/process
runs."""

from __future__ import annotations

import pytest

from como import _autoupdate


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    # Redirect the throttle stamp into a temp dir so tests don't touch ~/.config.
    monkeypatch.setattr(_autoupdate, "_STAMP", tmp_path / "update_check")
    monkeypatch.delenv("COMO_NO_UPDATE", raising=False)
    yield


def _fake_git(monkeypatch, *, behind: int, pull_ok: bool = True):
    calls: list[tuple[str, ...]] = []

    class _R:
        def __init__(self, rc: int, out: str = ""):
            self.returncode = rc
            self.stdout = out
            self.stderr = ""

    def fake(root, *args, timeout):
        calls.append(args)
        if args[0] == "fetch":
            return _R(0)
        if args[:1] == ("rev-list",):
            return _R(0, str(behind))
        if args[0] == "pull":
            return _R(0 if pull_ok else 1)
        return _R(0)

    monkeypatch.setattr(_autoupdate, "_git", fake)
    monkeypatch.setattr(_autoupdate, "_clone_root", lambda: __import__("pathlib").Path("/fake/clone"))
    return calls


def test_no_update_env_is_a_noop(monkeypatch):
    monkeypatch.setenv("COMO_NO_UPDATE", "1")
    calls = _fake_git(monkeypatch, behind=5)
    _autoupdate.maybe_autoupdate()
    assert calls == []  # never even fetched


def test_throttled_skips_within_interval(monkeypatch, tmp_path):
    _autoupdate._STAMP.parent.mkdir(parents=True, exist_ok=True)
    _autoupdate._STAMP.touch()  # checked "just now"
    calls = _fake_git(monkeypatch, behind=5)
    _autoupdate.maybe_autoupdate()
    assert calls == []


def test_up_to_date_is_silent(monkeypatch, capsys):
    _fake_git(monkeypatch, behind=0)
    _autoupdate.maybe_autoupdate()
    assert "update" not in capsys.readouterr().err.lower()


def test_behind_notifies_and_pulls(monkeypatch, capsys):
    calls = _fake_git(monkeypatch, behind=3)
    _autoupdate.maybe_autoupdate()
    err = capsys.readouterr().err
    assert "3 update" in err and "updated" in err.lower()
    assert calls[-1] == ("pull", "--ff-only", "--quiet")


def test_behind_but_pull_fails_tells_user_to_run_update(monkeypatch, capsys):
    _fake_git(monkeypatch, behind=2, pull_ok=False)
    _autoupdate.maybe_autoupdate()
    assert "como update" in capsys.readouterr().err


def test_non_clone_install_is_a_noop(monkeypatch, capsys):
    monkeypatch.setattr(_autoupdate, "_clone_root", lambda: None)
    _autoupdate.maybe_autoupdate()
    assert capsys.readouterr().err == ""


def test_force_update_up_to_date_returns_0(monkeypatch, capsys):
    _fake_git(monkeypatch, behind=0)
    assert _autoupdate.force_update() == 0
    assert "up to date" in capsys.readouterr().err.lower()


def test_nothing_writes_to_stdout(monkeypatch, capsys):
    _fake_git(monkeypatch, behind=4)
    _autoupdate.maybe_autoupdate()
    assert capsys.readouterr().out == ""  # JSON channel stays clean
