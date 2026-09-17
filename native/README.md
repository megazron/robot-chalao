# Robot Chalao — native C++ core

This is the **native foundation** of the Robot Chalao Hinglish robot language: a
lexer, recursive-descent parser, and tree-walking interpreter written in
portable C++17 with **no external libraries** — the whole thing is the standard
library and a single compiled `chalao` binary. Just as Linux stands on C, Robot
Chalao stands on this C++ core.

It ships a **simulation backend**, so every `.rc` program runs with zero ROS
installed: each robot command prints a clear Hinglish `[nakli]` (dry-run) line
and returns a plausible value. Its output is byte-for-byte identical to the
Python reference interpreter.

## Build

```bash
cd native
make            # produces ./chalao   (g++ -std=c++17, stdlib only)
```

## Run

```bash
./chalao run ../examples/01_arm_pick_place.rc     # run a program (simulation)
./chalao repl                                     # interactive prompt
./chalao --version
```

## What it supports

The full language surface: `maano`, `dikhao`, `agar/toh/warna/khatam`,
`jab tak … karo`, `har … mein karo`, `kaam … wapas` (with recursion and
closures), `koshish … galti hone par`, `ruko_loop`; numbers, strings, `sach`/
`jhooth`, `aur`/`ya`/`nahi`, lists, dicts, `.` member access, arithmetic and
comparison; typed constructors `pose(...)`, `twist(...)`, `joints(...)`; and the
robot commands (`robot jodo`, `jao`, `pakdo`/`chhodo`, `aage chalo`, `ghumo`,
`yahan jao`, `object dhundo`, `TF pucho`, `udaan bharo`, `band karo`, the
`robot "name" …` multi-robot selector, and more). Errors are Hinglish with a
line number, e.g. `Bhai, line 12: 'khatam' bhool gaye (block not closed)`.

## Layout

```
native/
├── include/
│   ├── value.hpp     runtime values + formatting (matches the reference)
│   ├── ast.hpp       AST nodes + the Hinglish error type
│   ├── lexer.hpp     source text -> tokens
│   ├── parser.hpp    tokens -> AST (recursive descent)
│   └── interp.hpp    tree-walking interpreter + simulation backend
├── src/main.cpp      CLI (run / repl / --version)
├── tests/            feature tests (*.rc + *.expected) and run_tests.sh
└── Makefile          `make`, `make test`
```

## Test

```bash
make test          # builds, checks feature output, runs every example, checks errors
```
