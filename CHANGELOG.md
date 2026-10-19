# Changelog

All notable changes to Robot Chalao. Versions follow [Semantic Versioning](https://semver.org).

## [1.0.1] - 2026-10-19

### Added
- Browser playground at https://megazron.github.io/robot-chalao/ (Pyodide), deployed from `site/` on every push to main.

### Fixed
- Timed base moves (`aage chalo`, `ghumo`, ...) could start publishing before DDS had
  matched the base controller, so the robot drove short or not at all. They now wait up
  to 3 s for a `cmd_vel` subscriber and fail with a clear message if none appears.

## [1.0.0] - 2026-10-19

First stable release. The language, both interpreters and the CLI are now covered
by compatibility guarantees: programs that run on 1.0 keep running on 1.x.

### Added
- `chalao init [dir]` scaffolds a project (`chalao.yaml` + `main.rc`).
- `chalao check FILE...` checks the grammar without running anything (CI-friendly exit code).
- `chalao --version`; `chalao file.rc` as shorthand for `chalao run file.rc`.
- Errors show the file, line number and the offending source line.
- Runtime commands shared with zronOS: `frame` (static TF), `sehat` (diagnostics on
  `/diagnostics`), `sewa do` (serve a function), and `sewa bulao` as a value.
- Scientific-notation numbers (`2.25e-05`, `1E6`).
- MoveIt 2 config from `chalao.yaml`: `moveit_config_package`, `moveit_robot_name`,
  `moveit_mappings`, so a script can drive a MoveIt robot without a custom launch file.
- `chalao repl --real` for a live REPL (the REPL stays simulated by default).
- Python/native parity tests: every native feature test and every example must print
  the same bytes from both cores.
- Live ROS 2 integration test (runs in a `ros:jazzy` container in CI).
- Release artifacts: wheel, sdist, static native binary, VS Code extension (`.vsix`).

### Fixed
- Real (non-`--simulate`) runs: the ROS backends were never registered, so every
  real run failed with "unknown backend 'raw'".
- Real runs: only the connection backend was connected; arm, base and perception
  commands failed with "connect nahi hua". Every backend now connects on first use
  and every backend is disconnected at the end.
- Robots left connected when a program ends (or fails, or gets Ctrl-C) are now
  disconnected, so mobile bases receive their stop command.
- MoveIt: `speed` was never applied to plans; `planner` called a method that does not
  exist; failed trajectory executions were reported as success; the first move could
  be rejected before MoveIt had a joint state; reading joints right after a move could
  return the pre-move state; `get_node()` does not exist on Jazzy's `MoveItPy`; the
  process segfaulted on exit (moveit_py teardown bug).
- MoveIt: joints given by name are set by name, not by position.
- Numbers inside lists, dicts and simulator lines printed as `1.0` in Python but `1`
  in the native core; both now print `1`.
- REPL: blocks closed with the `bas` alias never ended; Ctrl-C now drops a half-typed
  block instead of quitting.
- A top-level `chalao --simulate run x.rc` ignored `--simulate`.
- "unexpected token '\n'" now reads "unexpected end of line".

## [0.1.0] - 2026-09-16

Initial release: lexer, parser, interpreter, transpiler to rclpy, `--simulate`
backend, MoveIt 2 / Nav2 / perception / raw / ros2_control / Gazebo / MAVROS
backends, Hinglish errors, `chalao doctor`, VS Code syntax highlighting.

[1.0.1]: https://github.com/megazron/robot-chalao/releases/tag/v1.0.1
[1.0.0]: https://github.com/megazron/robot-chalao/releases/tag/v1.0.0
[0.1.0]: https://github.com/megazron/robot-chalao/commits/main
