# Roadmap — Robot Chalao

Honest status: the language, interpreter, transpiler, simulator and per-capability
backends are the shipped core. The items below are planned, not done.

## 1. Multi-robot fleets
The language already carries a `robot "name"` selector, so a single script can talk
to several robots. A fleet layer would add a `bede` (fleet) block that binds a group
of robots, broadcasts a command to all of them, and waits on a barrier
(`sab intezaar karo`). Approach: one interpreter, one backend set per robot, a shared
executor, and per-robot namespaces already supported by `namespace`. Status: selector
works today; the fleet block and barrier are not implemented.

## 2. Behaviour trees in Hinglish
Sequences, fallbacks and parallels expressed in Hinglish (`kram` = sequence,
`vikalp` = fallback, `saath saath` = parallel), compiled to a BehaviorTree.CPP XML
or py_trees. This gives reactive, resumable behaviour that a plain script cannot.
Approach: a second front-end that reuses the lexer and emits a tree instead of a
linear program; leaf nodes are the existing robot commands. Status: designed, not
built.

## 3. LLM and voice commands
A `bolo ke karo "..."` command that sends a natural-language Hinglish sentence to an
LLM, which returns a `.rc` snippet that is shown to the operator, checked against the
safety limits (`workspace limit`, `speed limit`), and only then run. Voice would add
a speech-to-text front-end publishing to the same path. Approach: keep the model out
of the control loop; it writes code a human approves, it does not drive the arm
directly. Status: not built; the safety gate it depends on exists.

## 4. Web IDE
A browser editor with the VS Code grammar reused, a `--simulate` runner compiled to
the browser (the core is pure Python, so Pyodide is the likely path), and a live
3-D view. Approach: run the interpreter in-browser against the sim backend, stream
the Hinglish dry-run lines to a console pane. Status: not built; the zero-dependency,
ROS-free simulator makes it feasible.
