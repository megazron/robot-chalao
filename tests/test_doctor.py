import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from robot_chalao.doctor import run_doctor              # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_doctor_returns_zero(capsys):
    assert run_doctor() == 0
    out = capsys.readouterr().out
    assert "doctor" in out.lower()


def test_doctor_cli_exit_zero():
    r = subprocess.run([sys.executable, "-m", "robot_chalao.cli", "doctor"],
                       cwd=ROOT, env=dict(os.environ, PYTHONPATH="src"),
                       capture_output=True, text=True)
    assert r.returncode == 0
