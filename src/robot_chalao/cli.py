"""`chalao` command-line: run / repl / transpile / doctor.

  chalao run file.rc [--simulate] [--config chalao.yaml]
  chalao repl [--simulate]
  chalao transpile file.rc [-o out.py]
  chalao doctor

Koi bhi RCError aaye toh use Hinglish mein chhaap kar exit 1 karte hain.
(On any RCError, print it in Hinglish and exit 1.)
"""
from __future__ import annotations

import argparse
import os
import sys

from .config import load_config
from .errors import RCError


def _default_config(explicit):
    if explicit:
        return explicit
    if os.path.exists("chalao.yaml"):
        return "chalao.yaml"
    return None


def cmd_run(args):
    from .interpreter import Interpreter
    from .parser import parse
    path = args.file
    if not os.path.exists(path):
        print("Bhai, file '%s' nahi mili (file not found)" % path, file=sys.stderr)
        return 1
    with open(path) as f:
        src = f.read()
    cfg = load_config(_default_config(args.config))
    prog = parse(src)
    interp = Interpreter(config=cfg, simulate=args.simulate,
                         base_dir=os.path.dirname(os.path.abspath(path)) or ".")
    interp.run(prog)
    return 0


def cmd_transpile(args):
    from .transpiler import transpile
    path = args.file
    if not os.path.exists(path):
        print("Bhai, file '%s' nahi mili" % path, file=sys.stderr)
        return 1
    with open(path) as f:
        py = transpile(f.read())
    if args.out:
        with open(args.out, "w") as f:
            f.write(py)
        print("Likh diya -> %s" % args.out)
    else:
        print(py)
    return 0


def cmd_repl(args):
    from .repl import run_repl
    cfg = load_config(_default_config(args.config))
    return run_repl(simulate=args.simulate or True, config=cfg)


def cmd_doctor(args):
    from .doctor import run_doctor
    return run_doctor()


def build_parser():
    p = argparse.ArgumentParser(
        prog="chalao",
        description="Robot Chalao -- Hinglish mein ROS 2 robot chalao.")
    p.add_argument("--simulate", action="store_true",
                   help="bina ROS ke, nakli (dry-run) mode")
    p.add_argument("--config", help="chalao.yaml ka path")
    sub = p.add_subparsers(dest="cmd")

    r = sub.add_parser("run", help="ek .rc file chalao")
    r.add_argument("file")
    r.add_argument("--simulate", action="store_true")
    r.add_argument("--config")
    r.set_defaults(func=cmd_run)

    t = sub.add_parser("transpile", help=".rc ko Python mein badlo")
    t.add_argument("file")
    t.add_argument("-o", "--out")
    t.set_defaults(func=cmd_transpile)

    rp = sub.add_parser("repl", help="interactive Hinglish shell")
    rp.add_argument("--simulate", action="store_true")
    rp.add_argument("--config")
    rp.set_defaults(func=cmd_repl)

    d = sub.add_parser("doctor", help="ROS/MoveIt/Nav2 install check karo")
    d.set_defaults(func=cmd_doctor)
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0
    # let a top-level --simulate flow into subcommands
    if getattr(args, "simulate", False):
        args.simulate = True
    try:
        return args.func(args)
    except RCError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
