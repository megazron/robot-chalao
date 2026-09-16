"""Robot Chalao ka interpreter: AST ko chalata hai (tree-walking).

Variables, functions (kaam/wapas, closures ke saath), agar/jab tak/har,
koshish/galti, aur har robot hukum ko sahi backend tak pahunchata hai. `--simulate`
mein har capability SimBackend par jaati hai, toh bina ROS ke poora program
chalta hai. `band karo` (e-stop) chalte timers/actions ko rok deta hai.

(Tree-walking interpreter. Scopes + closures, control flow, and RobotCommand
dispatch to the right backend. In simulate mode everything routes to SimBackend.)
"""
from __future__ import annotations

import os
import time

from . import ast_nodes as A
from .backends import CAPABILITY, get_backend
from .backends.sim import SimBackend
from .config import RobotConfig
from .errors import RCError, RCNameError, RCRuntimeError, RCTypeError
from .types import Joints, Pose, Twist

# how many times a `har N second mein` timer fires in simulate (so it ends)
SIM_TIMER_TICKS = 3


class _Return(Exception):
    def __init__(self, value):
        self.value = value


class _Break(Exception):
    pass


class _EStop(Exception):
    """band karo -- chalti hui timer/action loop ko todne ke liye."""


class Env:
    """Ek scope. Parent chain se lexical scoping milta hai."""

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name, line=None):
        e = self
        while e is not None:
            if name in e.vars:
                return e.vars[name]
            e = e.parent
        raise RCNameError(msg_hi="'%s' naam ki koi cheez nahi bani" % name,
                          hint_en="undefined name %r" % name, line=line)

    def set(self, name, value):
        self.vars[name] = value

    def assign(self, name, value):
        e = self
        while e is not None:
            if name in e.vars:
                e.vars[name] = value
                return
            e = e.parent
        self.vars[name] = value


class RobotContext:
    """Ek jude hue robot ka backend-set (capability -> backend instance)."""

    def __init__(self, name, config, simulate):
        self.name = name
        self.config = config
        self.simulate = simulate
        self._sim = SimBackend() if simulate else None
        self._cache = {}

    def backend(self, capability):
        if self.simulate:
            return self._sim
        bname = (self.config.backend_for(capability)
                 if self.config else "raw")
        if bname not in self._cache:
            self._cache[bname] = get_backend(bname)
        return self._cache[bname]


class Interpreter:
    """`Interpreter(config, simulate).run(program)`."""

    def __init__(self, config=None, simulate=False, base_dir="."):
        self.config = config or {}
        self.simulate = simulate
        self.base_dir = base_dir
        self.globals = Env()
        self.funcs = {}
        self.robots = {}
        self.current = None
        self._imported = set()
        self._deadline = None

    # ------------------------------------------------------------- run
    def run(self, program):
        self.exec_block(program.body, self.globals)

    def exec_block(self, stmts, env):
        for st in stmts:
            self.exec_stmt(st, env)

    # ------------------------------------------------------------- statements
    def exec_stmt(self, node, env):
        m = getattr(self, "_st_" + type(node).__name__, None)
        if m is None:
            raise RCRuntimeError(msg_hi="yeh statement chal nahi sakta",
                                 hint_en="cannot run %s" % type(node).__name__,
                                 line=getattr(node, "line", None))
        return m(node, env)

    def _st_Let(self, node, env):
        env.assign(node.name, self.eval(node.expr, env))

    def _st_Print(self, node, env):
        parts = [_fmt(self.eval(e, env)) for e in node.exprs]
        print(" ".join(parts))

    def _st_ExprStmt(self, node, env):
        self.eval(node.expr, env)

    def _st_Return(self, node, env):
        raise _Return(self.eval(node.expr, env) if node.expr is not None else None)

    def _st_Break(self, node, env):
        raise _Break()

    def _st_Import(self, node, env):
        path = node.path
        if not os.path.isabs(path):
            path = os.path.join(self.base_dir, path)
        path = os.path.abspath(path)
        if path in self._imported:
            return
        if not os.path.exists(path):
            raise RCRuntimeError(msg_hi="file '%s' nahi mili" % node.path,
                                 hint_en="import target not found", line=node.line)
        self._imported.add(path)
        from .parser import parse
        with open(path) as f:
            prog = parse(f.read())
        self.exec_block(prog.body, self.globals)

    def _st_If(self, node, env):
        if _truthy(self.eval(node.cond, env)):
            self.exec_block(node.then, Env(env))
        elif node.orelse:
            self.exec_block(node.orelse, Env(env))

    def _st_While(self, node, env):
        while _truthy(self.eval(node.cond, env)):
            try:
                self.exec_block(node.body, Env(env))
            except _Break:
                break

    def _st_ForEach(self, node, env):
        seq = self.eval(node.iterable, env)
        try:
            it = iter(seq)
        except TypeError:
            raise RCTypeError(msg_hi="is cheez par 'har' nahi chal sakta",
                              hint_en="value is not iterable", line=node.line)
        for item in it:
            child = Env(env)
            child.set(node.var, item)
            try:
                self.exec_block(node.body, child)
            except _Break:
                break

    def _st_FuncDef(self, node, env):
        self.funcs[node.name] = (node, env)

    def _st_Try(self, node, env):
        try:
            self.exec_block(node.body, Env(env))
        except _Return:
            raise
        except _Break:
            raise
        except RCError as e:
            child = Env(env)
            if node.err_name:
                child.set(node.err_name, str(e))
            self.exec_block(node.handler, child)

    def _st_Timer(self, node, env):
        period = float(self.eval(node.period, env))
        unit = node.unit
        secs = period * (60.0 if unit.startswith("minute")
                         else 0.001 if unit == "ms" else 1.0)
        ticks = SIM_TIMER_TICKS
        if not self.simulate and self._deadline:
            ticks = max(1, int(self._deadline / max(secs, 1e-6)))
        for _ in range(ticks):
            try:
                self.exec_block(node.body, Env(env))
            except _Break:
                break
            except _EStop:
                break
            if not self.simulate:
                time.sleep(secs)

    def _st_Subscribe(self, node, env):
        topic = self.eval(node.topic, env)
        ctx = self._ctx(None, node.line)
        backend = ctx.backend("raw")

        def cb(msg):
            child = Env(env)
            child.set(node.var, msg)
            try:
                self.exec_block(node.body, child)
            except _EStop:
                pass

        backend.subscribe(topic, node.type_name, cb)

    def _st_ActionSend(self, node, env):
        name = self.eval(node.name, env)
        goal = self.eval(node.goal, env)
        ctx = self._ctx(None, node.line)
        backend = ctx.backend("raw")
        cb = None
        if node.progress_var is not None:
            def cb(fb):
                child = Env(env)
                child.set(node.progress_var, fb)
                self.exec_block(node.body, child)
        return backend.send_action(name, goal, cb)

    def _st_RobotCommand(self, node, env):
        return self._run_command(node, env)

    # ------------------------------------------------------------- robot cmds
    def _ctx(self, selector, line):
        if selector is not None:
            if selector not in self.robots:
                if self.simulate:
                    self.robots[selector] = RobotContext(selector, None, True)
                else:
                    raise RCRuntimeError(
                        msg_hi="robot '%s' se pehle jud nahi" % selector,
                        hint_en="use `robot jodo` first", line=line)
            return self.robots[selector]
        if self.current is None:
            if self.simulate:
                self.current = RobotContext("robot", None, True)
                self.robots["robot"] = self.current
            else:
                raise RCRuntimeError(msg_hi="pehle 'robot jodo' karo",
                                     hint_en="connect a robot first", line=line)
        return self.current

    def _run_command(self, node, env):
        method = node.method
        kwargs = {k: self.eval(v, env) for k, v in node.args.items()}
        line = node.line

        if method == "connect":
            return self._connect(kwargs["name"], node.selector, line)
        if method == "disconnect":
            return self._disconnect(node.selector, line)

        ctx = self._ctx(node.selector, line)
        capability = CAPABILITY.get(method, "raw")
        backend = ctx.backend(capability)

        if method == "estop":
            try:
                backend.estop()
            finally:
                pass
            return None

        fn = getattr(backend, method, None)
        if fn is None:
            raise RCRuntimeError(msg_hi="anjaan hukum '%s'" % method,
                                 hint_en="unknown command", line=line)
        return fn(**kwargs)

    def _connect(self, name, selector, line):
        key = selector or name
        cfg = self.config.get(name)
        if cfg is None and not self.simulate:
            raise RCRuntimeError(
                msg_hi="chalao.yaml nahi mila ya robot '%s' ka config missing" % name,
                hint_en="add %r to chalao.yaml, or run with --simulate" % name,
                line=line)
        ctx = RobotContext(key, cfg, self.simulate)
        ctx.backend("connection").connect(name, cfg)
        self.robots[key] = ctx
        if selector is None:
            self.current = ctx
        return None

    def _disconnect(self, selector, line):
        ctx = self._ctx(selector, line)
        ctx.backend("connection").disconnect()
        key = selector or (ctx.name if ctx else None)
        self.robots.pop(key, None)
        if ctx is self.current:
            self.current = None
        return None

    # ------------------------------------------------------------- expressions
    def eval(self, node, env):
        m = getattr(self, "_ev_" + type(node).__name__, None)
        if m is None:
            raise RCRuntimeError(msg_hi="yeh expression samajh nahi aaya",
                                 hint_en="cannot evaluate %s" % type(node).__name__,
                                 line=getattr(node, "line", None))
        return m(node, env)

    def _ev_Num(self, node, env):
        return node.value

    def _ev_Str(self, node, env):
        return node.value

    def _ev_Bool(self, node, env):
        return node.value

    def _ev_Ident(self, node, env):
        return env.get(node.name, node.line)

    def _ev_ListLit(self, node, env):
        return [self.eval(x, env) for x in node.items]

    def _ev_DictLit(self, node, env):
        return {self.eval(k, env): self.eval(v, env) for k, v in node.pairs}

    def _ev_Member(self, node, env):
        obj = self.eval(node.obj, env)
        if isinstance(obj, dict) and node.attr in obj:
            return obj[node.attr]
        if hasattr(obj, node.attr):
            return getattr(obj, node.attr)
        raise RCTypeError(msg_hi="'%s' is cheez mein nahi hai" % node.attr,
                          hint_en="no attribute %r" % node.attr, line=node.line)

    def _ev_UnaryOp(self, node, env):
        v = self.eval(node.operand, env)
        if node.op == "-":
            return -v
        if node.op == "nahi":
            return not _truthy(v)
        raise RCRuntimeError(msg_hi="anjaan operator", hint_en=node.op, line=node.line)

    def _ev_BinOp(self, node, env):
        op = node.op
        if op == "aur":
            return _truthy(self.eval(node.left, env)) and \
                _truthy(self.eval(node.right, env))
        if op == "ya":
            return _truthy(self.eval(node.left, env)) or \
                _truthy(self.eval(node.right, env))
        a = self.eval(node.left, env)
        b = self.eval(node.right, env)
        try:
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            if op == "/":
                if b == 0:
                    raise RCRuntimeError(msg_hi="zero se bhaag nahi kar sakte",
                                         hint_en="division by zero", line=node.line)
                return a / b
            if op == "%":
                return a % b
            if op == "==":
                return a == b
            if op == "!=":
                return a != b
            if op == "<":
                return a < b
            if op == ">":
                return a > b
            if op == "<=":
                return a <= b
            if op == ">=":
                return a >= b
        except RCError:
            raise
        except Exception as e:  # noqa: BLE001
            raise RCTypeError(msg_hi="in do cheezon par '%s' nahi chalta" % op,
                              hint_en=str(e), line=node.line)
        raise RCRuntimeError(msg_hi="anjaan operator '%s'" % op,
                             hint_en="unknown operator", line=node.line)

    def _ev_TypedCtor(self, node, env):
        args = [self.eval(a, env) for a in node.args]
        if node.kind == "pose":
            return Pose(*[float(x) for x in args][:6])
        if node.kind == "twist":
            if len(args) == 2:
                return Twist(vx=float(args[0]), wz=float(args[1]))
            return Twist(*[float(x) for x in args][:6])
        if node.kind == "joints":
            return Joints([float(x) for x in args])
        raise RCTypeError(msg_hi="anjaan type '%s'" % node.kind,
                          hint_en="unknown constructor", line=node.line)

    def _ev_RobotCommand(self, node, env):
        return self._run_command(node, env)

    def _ev_Call(self, node, env):
        name = node.name
        args = [self.eval(a, env) for a in node.args]
        # interpreter builtins
        if name == "_ruko":
            secs = float(args[0]) if args else 0.0
            print("[nakli] ruk raha hoon %.2f second" % secs
                  if self.simulate else "ruk raha hoon %.2f second" % secs)
            if not self.simulate:
                time.sleep(secs)
            return None
        if name == "_deadline":
            self._deadline = float(args[0]) if args else None
            print("[nakli] deadline %.2f second" % (self._deadline or 0))
            return None
        b = _BUILTINS.get(name)
        if b is not None:
            return b(*args)
        # user function
        if name in self.funcs:
            return self._call_user(name, args, node.line)
        raise RCNameError(msg_hi="'%s' naam ka koi kaam nahi bana" % name,
                          hint_en="undefined function %r" % name, line=node.line)

    def _call_user(self, name, args, line):
        fnode, closure = self.funcs[name]
        if len(args) != len(fnode.params):
            raise RCTypeError(
                msg_hi="'%s' ko %d cheezein chahiye, %d di" %
                       (name, len(fnode.params), len(args)),
                hint_en="argument count mismatch", line=line)
        local = Env(closure)
        for p, a in zip(fnode.params, args):
            local.set(p, a)
        try:
            self.exec_block(fnode.body, local)
        except _Return as r:
            return r.value
        return None


# --------------------------------------------------------------- helpers
def _truthy(v):
    if isinstance(v, (list, dict, str)):
        return len(v) > 0
    return bool(v)


def _fmt(v):
    if isinstance(v, bool):
        return "sach" if v else "jhooth"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if v is None:
        return "kuch nahi"
    return str(v)


def _rc_len(x):
    return float(len(x))


def _rc_range(*a):
    a = [int(x) for x in a]
    return list(range(*a))


_BUILTINS = {
    "len": _rc_len,
    "range": _rc_range,
    "abs": lambda x: abs(x),
    "min": lambda *a: min(a[0]) if len(a) == 1 else min(a),
    "max": lambda *a: max(a[0]) if len(a) == 1 else max(a),
    "round": lambda x, n=0: round(x, int(n)),
    "int": lambda x: float(int(x)),
    "str": lambda x: _fmt(x),
    "list": lambda x=None: list(x) if x is not None else [],
}
