"""`chalao` command-line: run / check / repl / transpile / init / doctor.

  chalao run file.rc [--simulate] [--config chalao.yaml]
  chalao check file.rc [more.rc ...]
  chalao repl [--real]
  chalao transpile file.rc [-o out.py]
  chalao init [dir]
  chalao doctor

Koi bhi RCError aaye toh use Hinglish mein, file aur line ke saath, chhaap kar
exit 1 karte hain. (On any RCError, print it with the file and source line and
exit 1.)
"""
from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .config import load_config
from .errors import RCError


def _default_config(explicit, script=None):
    """--config, else ./chalao.yaml, else chalao.yaml next to the script."""
    if explicit:
        return explicit
    if os.path.exists("chalao.yaml"):
        return "chalao.yaml"
    if script:
        beside = os.path.join(os.path.dirname(os.path.abspath(script)), "chalao.yaml")
        if os.path.exists(beside):
            return beside
    return None


def format_error(err, path=None, src=None):
    """RCError -> message, plus `--> file:line` and the offending source line."""
    out = str(err)
    if err.line is None or path is None:
        return out
    out += "\n  --> %s:%d" % (path, err.line)
    lines = (src or "").split("\n")
    if 1 <= err.line <= len(lines) and lines[err.line - 1].strip():
        out += "\n  %4d | %s" % (err.line, lines[err.line - 1].rstrip())
    return out


def _read(path):
    if not os.path.isfile(path):
        print("Bhai, file '%s' nahi mili (file not found)" % path, file=sys.stderr)
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def cmd_run(args):
    from .interpreter import Interpreter
    from .parser import parse
    src = _read(args.file)
    if src is None:
        return 1
    interp = None
    try:
        cfg = load_config(_default_config(args.config, args.file))
        prog = parse(src)
        interp = Interpreter(config=cfg, simulate=args.simulate,
                             base_dir=os.path.dirname(os.path.abspath(args.file)) or ".")
        interp.run(prog)
        interp.close()
    except RCError as e:
        print(format_error(e, args.file, src), file=sys.stderr)
        _close_quietly(interp)
        return 1
    except KeyboardInterrupt:
        print("\nRuk gaya (Ctrl-C) -- program band kiya", file=sys.stderr)
        _close_quietly(interp)
        return 130
    return 0


def _close_quietly(interp):
    """On failure, still disconnect (stops bases) without masking the error."""
    if interp is None:
        return
    try:
        interp.close()
    except Exception as exc:  # noqa: BLE001
        print("(disconnect bhi fail hua: %s)" % exc, file=sys.stderr)


def cmd_check(args):
    from .parser import parse
    bad = 0
    for path in args.files:
        src = _read(path)
        if src is None:
            bad += 1
            continue
        try:
            parse(src)
            print("theek  %s" % path)
        except RCError as e:
            bad += 1
            print(format_error(e, path, src), file=sys.stderr)
    return 1 if bad else 0


def cmd_transpile(args):
    from .transpiler import transpile
    src = _read(args.file)
    if src is None:
        return 1
    try:
        py = transpile(src)
    except RCError as e:
        print(format_error(e, args.file, src), file=sys.stderr)
        return 1
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(py)
        print("Likh diya -> %s" % args.out)
    else:
        print(py)
    return 0


def cmd_repl(args):
    from .repl import run_repl
    cfg = load_config(_default_config(args.config))
    return run_repl(simulate=not args.real, config=cfg)


def cmd_doctor(args):
    from .doctor import run_doctor
    return run_doctor()


_INIT_CONFIG = """\
# Robot Chalao config -- har robot ka setup yahan.
default_robot: mera_arm

robots:
  mera_arm:
    type: arm
    planning_group: manipulator
    ee_link: tool0
    base_link: base_link
    gripper: {action: "/gripper_controller/gripper_cmd"}
    named_poses:
      home: [0.0, -1.57, 0.0, -1.57, 0.0, 0.0]
    speed_limit: 0.5
    workspace: {xmin: -0.8, xmax: 0.8, ymin: -0.8, ymax: 0.8, zmin: 0.0, zmax: 1.2}
    backends: {arm: moveit, perception: perception, raw: raw}
"""

_INIT_MAIN = """\
# pehla program -- chalao run main.rc --simulate
robot jodo "mera_arm"
speed 0.4
ghar jao
rakh pick = pose(0.4, 0.1, 0.2, 0, 3.14, 0)
jao pick
pakdo
seedha jao (0.4, 0.1, 0.4)
chhodo
ghar jao
bol "kaam ho gaya"
robot chhodo
"""


def cmd_init(args):
    target = args.dir
    os.makedirs(target, exist_ok=True)
    files = {"chalao.yaml": _INIT_CONFIG, "main.rc": _INIT_MAIN}
    clash = [n for n in files if os.path.exists(os.path.join(target, n))]
    if clash:
        print("Bhai, '%s' pehle se hai -- kuch nahi badla (already exists)"
              % os.path.join(target, clash[0]), file=sys.stderr)
        return 1
    for name, text in files.items():
        with open(os.path.join(target, name), "w", encoding="utf-8") as f:
            f.write(text)
    where = "" if target == "." else "cd %s && " % target
    print("Bana diya: %s/chalao.yaml, %s/main.rc" % (target, target))
    print("Ab chalao:  %schalao run main.rc --simulate" % where)
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="chalao",
        description="Robot Chalao -- Hinglish mein ROS 2 robot chalao.")
    p.add_argument("--version", action="version",
                   version="chalao %s" % __version__)
    p.add_argument("--simulate", action="store_true",
                   help="bina ROS ke, nakli (dry-run) mode")
    p.add_argument("--config", help="chalao.yaml ka path")
    sub = p.add_subparsers(dest="cmd")

    r = sub.add_parser("run", help="ek .rc file chalao")
    r.add_argument("file")
    # SUPPRESS keeps a top-level `chalao --simulate run x.rc` working
    r.add_argument("--simulate", action="store_true", default=argparse.SUPPRESS,
                   help="bina ROS ke, nakli (dry-run) mode")
    r.add_argument("--config", default=argparse.SUPPRESS, help="chalao.yaml ka path")
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("check", help=".rc file(s) ka grammar check, bina chalaye")
    c.add_argument("files", nargs="+")
    c.set_defaults(func=cmd_check)

    t = sub.add_parser("transpile", help=".rc ko Python mein badlo")
    t.add_argument("file")
    t.add_argument("-o", "--out")
    t.set_defaults(func=cmd_transpile)

    rp = sub.add_parser("repl", help="interactive Hinglish shell (nakli by default)")
    rp.add_argument("--real", action="store_true",
                    help="asli ROS 2 backends use karo (needs sourced ROS 2)")
    rp.add_argument("--simulate", action="store_true", default=argparse.SUPPRESS,
                    help=argparse.SUPPRESS)
    rp.add_argument("--config", default=argparse.SUPPRESS, help="chalao.yaml ka path")
    rp.set_defaults(func=cmd_repl)

    i = sub.add_parser("init", help="naya project: chalao.yaml + main.rc")
    i.add_argument("dir", nargs="?", default=".")
    i.set_defaults(func=cmd_init)

    d = sub.add_parser("doctor", help="ROS/MoveIt/Nav2 install check karo")
    d.set_defaults(func=cmd_doctor)
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # `chalao file.rc` is shorthand for `chalao run file.rc`
    if argv and argv[0].endswith(".rc"):
        argv.insert(0, "run")
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0
    rc = 1
    try:
        rc = args.func(args)
    except RCError as e:
        print(str(e), file=sys.stderr)
    except BaseException:
        if _moveit_started():
            import traceback
            traceback.print_exc()
            _hard_exit(1)
        raise
    if _moveit_started():
        _hard_exit(rc)
    return rc


def _moveit_started():
    mod = sys.modules.get("robot_chalao.backends.moveit")
    return mod is not None and bool(mod.RETIRED)


def _hard_exit(rc):
    """MoveItPy crashes when collected; leave without collecting it."""
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(rc)


if __name__ == "__main__":
    sys.exit(main())
