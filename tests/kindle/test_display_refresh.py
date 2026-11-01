from pathlib import Path
import os
import subprocess
import tempfile


REPO = Path(__file__).resolve().parents[2]
LIBRARY = REPO / "kindle/HAKiosk/display-refresh.sh"


def run_case(interval, calls, expected_calls, expected_disabled=0):
    with tempfile.TemporaryDirectory(prefix="kindle-display-refresh-") as tmp:
        root = Path(tmp)
        (root / "display-refresh-seconds.txt").write_text(interval)
        mock = root / "eips"
        log = root / "calls"
        mock.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$CALL_LOG\"\n"
            "[ \"${EIPS_FAIL:-0}\" = 0 ]\n"
        )
        mock.chmod(0o755)
        script = (
            f"ROOT={root!s}\nEIPS_COMMAND={mock!s}\n"
            f". {LIBRARY!s}\n"
            "display_refresh_init 100\n"
            + "\n".join(f"display_refresh_tick {now} {touch}; STATUS=$?" for now, touch in calls)
            + "\nprintf 'disabled=%s last=%s\\n' \"$DISPLAY_REFRESH_DISABLED\" \"$DISPLAY_REFRESH_LAST\"\n"
        )
        env = dict(os.environ, CALL_LOG=str(log), EIPS_FAIL="1" if expected_disabled == 2 else "0")
        result = subprocess.run(["sh", "-c", script], env=env, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        actual = log.read_text().splitlines() if log.exists() else []
        assert actual == ["-s w=758,h=1024 -f"] * expected_calls, (actual, result.stdout, result.stderr)
        assert f"disabled={1 if expected_disabled else 0}" in result.stdout, result.stdout
        if expected_disabled == 2:
            assert "eips command failed" in result.stderr, result.stderr


def test_before_due_does_not_refresh():
    run_case("300\n", [(399, 300)], 0)


def test_touch_defers_overdue_refresh_until_idle():
    run_case("300\n", [(400, 398), (401, 396)], 1)


def test_success_uses_full_pw1_refresh_and_advances_clock():
    run_case("60\n", [(160, 155), (219, 200)], 1)


def test_failure_disables_refresh_for_session():
    run_case("60\n", [(160, 150), (300, 200)], 1, expected_disabled=2)


def test_zero_and_invalid_intervals_disable_refresh():
    run_case("0\n", [(1000, 0)], 0, expected_disabled=1)
    run_case("59\n", [(1000, 0)], 0, expected_disabled=1)
    run_case("not-a-number\n", [(1000, 0)], 0, expected_disabled=1)

if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_") and callable(test):
            test();print(name+": passed")
