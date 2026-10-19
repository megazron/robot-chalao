# Contributing to Robot Chalao

New backends, keywords, examples and fixes are welcome.

## Setup

```bash
git clone https://github.com/megazron/robot-chalao
cd robot-chalao
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
make -C native            # optional: the native C++ core
```

## Before you open a pull request

```bash
ruff check src tests
python -m pytest -q       # includes Python/native parity if native/chalao is built
make -C native test       # native feature tests
make -C native san && bash native/tests/run_tests.sh   # sanitizer build
```

If you have ROS 2 Jazzy sourced, `tests/test_ros_live.py` also runs a real
(non-simulated) program against live ROS 2.

## The two cores must agree

Robot Chalao has a Python reference (`src/robot_chalao`) and a native C++17 core
(`native/`). Every language change goes into **both**, and they must print the same
bytes. To add a feature:

1. Implement it in the Python lexer/parser/interpreter and the `sim` backend.
2. Implement it in `native/include/*.hpp`.
3. Add `native/tests/t_<feature>.rc` and its `.expected` output. The parity tests run
   that file through the Python interpreter as well.
4. If it is a robot command, add the real ROS 2 implementation to the right backend
   in `src/robot_chalao/backends/`, plus a `CAPABILITY` entry in `base.py`.
5. Document it in `docs/GRAMMAR.md` and add a line to `CHANGELOG.md`.

zronOS vendors the native core. After a release, sync it with
`tools/sync-chalao.sh <tag>` in the zronos repo.

## Releases

Bump `__version__` in `src/robot_chalao/__init__.py` and `native/src/main.cpp`,
update `vscode-extension/package.json` and `CHANGELOG.md`, then push a `vX.Y.Z` tag.
The release workflow tests everything and publishes the wheel, sdist, static native
binary and `.vsix` to GitHub Releases.
