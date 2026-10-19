"""The Python reference and the native C++ core must print the same bytes.

Every native feature test (native/tests/t_*.rc + .expected) is also run
through the Python interpreter. If the native binary is built
(make -C native), every example is run through both and compared too.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NATIVE_TESTS = sorted((ROOT / "native" / "tests").glob("t_*.rc"))
EXAMPLES = sorted((ROOT / "examples").glob("*.rc"))
NATIVE_BIN = ROOT / "native" / "chalao"


def _py_run(path):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-m", "robot_chalao.cli", "run",
                        path.name, "--simulate"], cwd=path.parent, env=env,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


@pytest.mark.parametrize("rc", NATIVE_TESTS, ids=lambda p: p.name)
def test_python_matches_expected(rc):
    code, out = _py_run(rc)
    assert code == 0, out
    assert out.rstrip("\n") == rc.with_suffix(".expected").read_text().rstrip("\n")


@pytest.mark.skipif(not NATIVE_BIN.exists(), reason="native core not built")
@pytest.mark.parametrize("rc", EXAMPLES, ids=lambda p: p.name)
def test_native_matches_python_on_examples(rc):
    _, py_out = _py_run(rc)
    nat = subprocess.run([str(NATIVE_BIN), "run", rc.name], cwd=rc.parent,
                         capture_output=True, text=True)
    assert nat.stdout + nat.stderr == py_out
