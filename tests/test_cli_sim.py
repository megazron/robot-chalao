import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
ENV = dict(os.environ, PYTHONPATH="src")


def _run(args):
    return subprocess.run([sys.executable, "-m", "robot_chalao.cli"] + args,
                          cwd=ROOT, env=ENV, capture_output=True, text=True)


def test_run_canonical_simulate():
    r = _run(["run", "examples/01_arm_pick_place.rc", "--simulate",
              "--config", "examples/chalao.yaml"])
    assert r.returncode == 0
    assert "[nakli]" in r.stdout and "jud gaye" in r.stdout


def test_all_examples_run_simulate():
    for fn in sorted(os.listdir(os.path.join(ROOT, "examples"))):
        if fn.endswith(".rc"):
            r = _run(["run", "examples/" + fn, "--simulate",
                      "--config", "examples/chalao.yaml"])
            assert r.returncode == 0, fn + ": " + r.stderr


def test_missing_file_hinglish():
    r = _run(["run", "nope.rc", "--simulate"])
    assert r.returncode == 1 and "Bhai" in r.stdout + r.stderr


def test_syntax_error_hinglish_exit_1(tmp_path):
    f = tmp_path / "bad.rc"
    f.write_text("agar x toh\n dikhao 1\n")  # no khatam
    r = _run(["run", str(f), "--simulate"])
    assert r.returncode == 1 and "Bhai" in r.stderr


def test_transpile_to_stdout():
    r = _run(["transpile", "examples/01_arm_pick_place.rc"])
    assert r.returncode == 0 and "def main():" in r.stdout


def test_help_runs():
    r = _run([])
    assert r.returncode == 0 and "chalao" in r.stdout.lower()
