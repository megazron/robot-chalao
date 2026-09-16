"""Robot Chalao ka parser: tokens -> AST (recursive descent).

Yeh haath se likha gaya parser hai (koi library nahi). Har Hinglish robot hukum
ko ek `RobotCommand(method, args, selector)` mein badalta hai, jahan `method`
bilkul ek Backend method ka naam hai (CONTRACT.md dekho). Control-flow keywords
(agar/jab tak/har/kaam/koshish) apne blocks banate hain jo `khatam` par band
hote hain. Galtiyan Hinglish mein aati hain, line number ke saath.

(Hand-written recursive-descent parser. Robot phrases become RobotCommand nodes
whose `method` is exactly a Backend method. Errors are Hinglish with a line.)
"""
from __future__ import annotations

from . import ast_nodes as A
from .errors import RCParseError
from .lexer import TokenType, tokenize

# time units accepted after ruko / har / ghumo / height etc.
_TIME_UNITS = {"second", "seconds", "minute", "minutes", "ms"}
_ANGLE_UNITS = {"degree", "degrees", "rad", "radian", "radians"}
_DIST_UNITS = {"meter", "meters", "metre", "cm", "mm"}

# leading words that may open a robot command when used as an EXPRESSION
# (queries that return a value, e.g. `maano p = kahan hai`)
_QUERY_LEAD = {"kahan", "joints", "battery", "TF", "object", "IK", "FK",
               "camera", "lidar", "depth", "imu", "dabav", "obstacle",
               "AprilTag", "ArUco", "param"}


class Parser:
    """`Parser(tokens).parse()` ek `Program` deta hai."""

    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0

    # ------------------------------------------------------------- helpers
    def cur(self):
        return self.toks[self.pos]

    def nxt(self, k=1):
        j = self.pos + k
        return self.toks[j] if j < len(self.toks) else self.toks[-1]

    def _line(self):
        return self.cur().line

    def is_kw(self, text):
        t = self.cur()
        return t.type == TokenType.IDENT and t.value == text

    def is_op(self, v):
        t = self.cur()
        return t.type == TokenType.OP and t.value == v

    def eat(self):
        t = self.cur()
        self.pos += 1
        return t

    def eat_kw(self, text, what=None):
        if not self.is_kw(text):
            raise RCParseError(
                msg_hi="yahan '%s' hona chahiye tha" % text,
                hint_en="expected '%s'%s" % (text, (" " + what) if what else ""),
                line=self._line())
        return self.eat().value

    def eat_op(self, v):
        if not self.is_op(v):
            raise RCParseError(
                msg_hi="yahan '%s' hona chahiye tha" % v,
                hint_en="expected '%s'" % v, line=self._line())
        return self.eat().value

    def eat_ident(self):
        t = self.cur()
        if t.type != TokenType.IDENT:
            raise RCParseError(msg_hi="yahan ek naam hona chahiye tha",
                               hint_en="expected an identifier", line=t.line)
        return self.eat().value

    def eat_string(self):
        t = self.cur()
        if t.type != TokenType.STRING:
            raise RCParseError(msg_hi="yahan \"...\" (string) hona chahiye tha",
                               hint_en="expected a string", line=t.line)
        return self.eat().value

    def expect_newline(self):
        t = self.cur()
        if t.type == TokenType.NEWLINE:
            self.eat()
        elif t.type == TokenType.EOF:
            return
        else:
            raise RCParseError(
                msg_hi="ek line par ek hi hukum -- yahan line khatam honi chahiye",
                hint_en="expected end of line", line=t.line)

    def skip_newlines(self):
        while self.cur().type == TokenType.NEWLINE:
            self.eat()

    # ------------------------------------------------------------- entry
    def parse(self):
        body = []
        self.skip_newlines()
        while self.cur().type != TokenType.EOF:
            body.append(self.statement())
            self.skip_newlines()
        return A.Program(body=body)

    def block(self, terminators):
        stmts = []
        while True:
            self.skip_newlines()
            t = self.cur()
            if t.type == TokenType.EOF:
                raise RCParseError(
                    msg_hi="block poora nahi hua; 'khatam' bhool gaye?",
                    hint_en="block not closed with 'khatam'", line=t.line)
            if t.type == TokenType.IDENT and t.value in terminators:
                break
            stmts.append(self.statement())
        return stmts

    # ------------------------------------------------------------- statements
    def statement(self):
        self.skip_newlines()
        t = self.cur()
        if t.type == TokenType.IDENT:
            kw = t.value
            if kw == "maano":
                node = self.let_stmt()
            elif kw == "agar":
                return self._end(self.if_stmt())
            elif kw == "jab":
                return self._end(self.while_stmt())
            elif kw == "har":
                return self._end(self.har_stmt())
            elif kw == "kaam":
                return self._end(self.func_def())
            elif kw == "koshish":
                return self._end(self.try_stmt())
            elif kw == "sun":
                return self._end(self.subscribe_stmt())
            elif kw == "action":
                return self._end(self.action_stmt())
            elif kw == "dikhao":
                node = self.print_stmt()
            elif kw == "wapas":
                node = self.return_stmt()
            elif kw == "import":
                node = self.import_stmt()
            elif kw == "ruko_loop":
                self.eat()
                node = A.Break(line=t.line)
            else:
                node = self.robot_command_stmt()
                if node is None:
                    node = A.ExprStmt(self.expression(), line=t.line)
        else:
            node = A.ExprStmt(self.expression(), line=t.line)
        self.expect_newline()
        return node

    def _end(self, node):
        # compound statements consume up to `khatam`; then the line ends
        self.expect_newline()
        return node

    def let_stmt(self):
        line = self._line()
        self.eat_kw("maano")
        name = self.eat_ident()
        self.eat_op("=")
        expr = self.expression()
        return A.Let(name=name, expr=expr, line=line)

    def print_stmt(self):
        line = self._line()
        self.eat_kw("dikhao")
        exprs = [self.expression()]
        while self.is_op(","):
            self.eat()
            exprs.append(self.expression())
        return A.Print(exprs=exprs, line=line)

    def return_stmt(self):
        line = self._line()
        self.eat_kw("wapas")
        expr = None
        if self.cur().type not in (TokenType.NEWLINE, TokenType.EOF):
            expr = self.expression()
        return A.Return(expr=expr, line=line)

    def import_stmt(self):
        line = self._line()
        self.eat_kw("import")
        return A.Import(path=self.eat_string(), line=line)

    def if_stmt(self):
        line = self._line()
        self.eat_kw("agar")
        cond = self.expression()
        self.eat_kw("toh")
        then = self.block({"warna", "khatam"})
        orelse = []
        if self.is_kw("warna"):
            self.eat()
            orelse = self.block({"khatam"})
        self.eat_kw("khatam")
        return A.If(cond=cond, then=then, orelse=orelse, line=line)

    def while_stmt(self):
        line = self._line()
        self.eat_kw("jab")
        self.eat_kw("tak")
        cond = self.expression()
        self.eat_kw("karo")
        body = self.block({"khatam"})
        self.eat_kw("khatam")
        return A.While(cond=cond, body=body, line=line)

    def har_stmt(self):
        line = self._line()
        self.eat_kw("har")
        # timer form: `har 0.1 second mein ... khatam`
        if self.cur().type == TokenType.NUMBER and \
                self.nxt().type == TokenType.IDENT and \
                self.nxt().value in _TIME_UNITS:
            period = self.factor()
            unit = self.eat_ident()
            self.eat_kw("mein")
            body = self.block({"khatam"})
            self.eat_kw("khatam")
            return A.Timer(period=period, unit=unit, body=body, line=line)
        # for-each: `har <var> <iterable> mein karo ... khatam`
        var = self.eat_ident()
        iterable = self.expression()
        self.eat_kw("mein")
        self.eat_kw("karo")
        body = self.block({"khatam"})
        self.eat_kw("khatam")
        return A.ForEach(var=var, iterable=iterable, body=body, line=line)

    def func_def(self):
        line = self._line()
        self.eat_kw("kaam")
        name = self.eat_ident()
        self.eat_op("(")
        params = []
        if not self.is_op(")"):
            params.append(self.eat_ident())
            while self.is_op(","):
                self.eat()
                params.append(self.eat_ident())
        self.eat_op(")")
        body = self.block({"khatam"})
        self.eat_kw("khatam")
        return A.FuncDef(name=name, params=params, body=body, line=line)

    def try_stmt(self):
        line = self._line()
        self.eat_kw("koshish")
        body = self.block({"galti"})
        self.eat_kw("galti")
        self.eat_kw("hone")
        self.eat_kw("par")
        err_name = None
        if self.cur().type == TokenType.IDENT and self.cur().value != "khatam" \
                and self.nxt().type == TokenType.NEWLINE:
            err_name = self.eat_ident()
        handler = self.block({"khatam"})
        self.eat_kw("khatam")
        return A.Try(body=body, err_name=err_name, handler=handler, line=line)

    def subscribe_stmt(self):
        line = self._line()
        self.eat_kw("sun")
        topic = self.expression()
        # type name may be a bare identifier or a string
        if self.cur().type == TokenType.STRING:
            type_name = self.eat_string()
        else:
            type_name = self.eat_ident()
        self.eat_kw("mein")
        var = self.eat_ident()
        body = self.block({"khatam"})
        self.eat_kw("khatam")
        return A.Subscribe(topic=topic, type_name=type_name, var=var,
                           body=body, line=line)

    def action_stmt(self):
        line = self._line()
        self.eat_kw("action")
        self.eat_kw("bhejo")
        name = self.expression()
        goal = self.expression()
        progress_var = None
        body = []
        if self.is_kw("progress"):
            self.eat()
            self.eat_kw("mein")
            progress_var = self.eat_ident()
            body = self.block({"khatam"})
        else:
            self.skip_newlines()
        self.eat_kw("khatam")
        return A.ActionSend(name=name, goal=goal, progress_var=progress_var,
                            body=body, line=line)

    # ------------------------------------------------------------- robot cmds
    def _tuple(self, n=None):
        """Parse `( e , e , ... )` and return a list of expr nodes."""
        self.eat_op("(")
        items = [self.expression()]
        while self.is_op(","):
            self.eat()
            items.append(self.expression())
        self.eat_op(")")
        if n is not None and len(items) != n:
            raise RCParseError(
                msg_hi="yahan %d cheezein honi chahiye thi, %d mili" % (n, len(items)),
                hint_en="expected %d values in ( )" % n, line=self._line())
        return items

    def _S(self, s, line):
        return A.Str(value=s, line=line)

    def _B(self, b, line):
        return A.Bool(value=b, line=line)

    def _unit_after(self, allowed, default):
        if self.cur().type == TokenType.IDENT and self.cur().value in allowed:
            return self.eat().value
        return default

    def robot_command_stmt(self):
        """Ek robot hukum parse karo, ya None agar yeh robot hukum nahi hai."""
        t = self.cur()
        w = t.value
        line = t.line

        def cmd(method, **args):
            return A.RobotCommand(method=method, args=args, line=line)

        # ---- connection & selector ----
        if w == "robot":
            self.eat()
            if self.is_kw("jodo"):
                self.eat()
                return cmd("connect", name=self._S(self.eat_string(), line))
            if self.is_kw("chhodo"):
                self.eat()
                return cmd("disconnect")
            # selector: robot "name" <verb phrase>
            sel = self.eat_string()
            inner = self.robot_command_stmt()
            if inner is None or not isinstance(inner, A.RobotCommand):
                raise RCParseError(
                    msg_hi="robot \"%s\" ke baad ek hukum hona chahiye" % sel,
                    hint_en="expected a command after a robot selector", line=line)
            inner.selector = sel
            return inner

        if w == "namespace":
            self.eat()
            return cmd("set_namespace", ns=self._S(self.eat_string(), line))

        if w == "param":
            self.eat()
            if self.is_kw("set"):
                self.eat()
                key = self._S(self.eat_string(), line)
                return cmd("param_set", key=key, value=self.expression())
            self.eat_kw("get")
            return cmd("param_get", key=self._S(self.eat_string(), line))

        # ---- arm ----
        if w == "ghar":
            self.eat()
            self.eat_kw("jao")
            return cmd("arm_home")
        if w == "jao":
            self.eat()
            expr = self.expression()
            if isinstance(expr, A.TypedCtor) and expr.kind == "joints":
                return cmd("arm_joints", joints=expr)
            return cmd("arm_pose", pose=expr)
        if w == "named":
            self.eat()
            self.eat_kw("pose")
            return cmd("arm_named", name=self._S(self.eat_string(), line))
        if w == "seedha":
            self.eat()
            self.eat_kw("jao")
            x, y, z = self._tuple(3)
            return cmd("arm_cartesian", x=x, y=y, z=z)
        if w == "pakdo":
            self.eat()
            return cmd("gripper", close=self._B(True, line))
        if w == "chhodo":
            self.eat()
            return cmd("gripper", close=self._B(False, line))
        if w == "speed":
            self.eat()
            if self.is_kw("limit"):
                self.eat()
                return cmd("set_speed_limit", v=self.expression())
            return cmd("set_speed", scale=self.expression())
        if w == "planner":
            self.eat()
            return cmd("set_planner", planner=self._S(self.eat_string(), line))
        if w == "rukawat":
            self.eat()
            if self.is_kw("jodo"):
                self.eat()
                name = self._S(self.eat_string(), line)
                x, y, z = self._tuple(3)
                self.eat_kw("size")
                a, b, c = self._tuple(3)
                pose = A.TypedCtor(kind="pose", args=[x, y, z], line=line)
                size = A.ListLit(items=[a, b, c], line=line)
                return cmd("add_obstacle", name=name, pose=pose, size=size)
            self.eat_kw("hatao")
            return cmd("remove_obstacle", name=self._S(self.eat_string(), line))
        if w == "attach":
            self.eat()
            return cmd("attach", name=self._S(self.eat_string(), line))
        if w == "detach":
            self.eat()
            return cmd("detach", name=self._S(self.eat_string(), line))
        if w == "kahan":
            self.eat()
            self.eat_kw("hai")
            return cmd("get_pose")
        if w == "joints" and self.nxt().type == TokenType.IDENT and \
                self.nxt().value == "kya":
            self.eat()
            self.eat_kw("kya")
            self.eat_kw("hai")
            return cmd("get_joints")
        if w == "IK":
            self.eat()
            self.eat_kw("nikalo")
            return cmd("ik", pose=self.expression())
        if w == "FK":
            self.eat()
            self.eat_kw("nikalo")
            return cmd("fk", joints=self.expression())

        # ---- mobile base ----
        if w == "aage":
            self.eat()
            self.eat_kw("chalo")
            dist = self.expression()
            unit = self._unit_after(_DIST_UNITS, "meter")
            return cmd("base_move", distance=dist, unit=self._S(unit, line),
                       backward=self._B(False, line))
        if w == "peeche":
            self.eat()
            self.eat_kw("chalo")
            dist = self.expression()
            unit = self._unit_after(_DIST_UNITS, "meter")
            return cmd("base_move", distance=dist, unit=self._S(unit, line),
                       backward=self._B(True, line))
        if w == "ghumo":
            self.eat()
            ang = self.expression()
            unit = self._unit_after(_ANGLE_UNITS, "degree")
            return cmd("base_rotate", angle=ang, unit=self._S(unit, line))
        if w == "speed_move":
            self.eat()
            v = self.expression()
            wv = self.expression()
            return cmd("base_twist", v=v, w=wv)
        if w == "ruk":
            self.eat()
            self.eat_kw("jao")
            return cmd("base_stop")
        if w == "map":
            self.eat()
            if self.is_kw("load"):
                self.eat()
                return cmd("map_load", path=self._S(self.eat_string(), line))
            if self.is_kw("save"):
                self.eat()
                return cmd("map_save", name=self._S(self.eat_string(), line))
            self.eat_kw("banao")
            return cmd("slam_start")
        if w == "localize":
            self.eat()
            if self.is_op("("):
                x, y, th = self._tuple(3)
                pose = A.TypedCtor(kind="pose", args=[x, y, th], line=line)
                return cmd("localize", pose=pose)
            return cmd("localize")
        if w == "yahan":
            self.eat()
            self.eat_kw("jao")
            x, y, th = self._tuple(3)
            return cmd("nav_to", x=x, y=y, theta=th)
        if w == "waypoints":
            self.eat()
            self.eat_kw("follow")
            return cmd("follow_waypoints", points=self.expression())
        if w == "obstacle":
            self.eat()
            self.eat_kw("nazdeek")
            self.eat_kw("hai")
            if self.is_op("?"):
                self.eat()
            return cmd("obstacle_near")

        # ---- perception ----
        if w == "camera":
            self.eat()
            self.eat_kw("dekho")
            return cmd("camera_view", topic=self._S(self.eat_string(), line))
        if w == "photo":
            self.eat()
            self.eat_kw("lo")
            return cmd("photo", topic=self._S("", line),
                       path=self._S(self.eat_string(), line))
        if w == "object":
            self.eat()
            self.eat_kw("dhundo")
            return cmd("find_object",
                       description=self._S(self.eat_string(), line))
        if w in ("lidar", "depth", "imu", "dabav"):
            self.eat()
            self.eat_kw("padho")
            return cmd({"lidar": "read_lidar", "depth": "read_depth",
                        "imu": "read_imu", "dabav": "read_ft"}[w])
        if w == "battery":
            self.eat()
            self.eat_kw("kitni")
            self.eat_kw("hai")
            return cmd("battery")
        if w == "AprilTag":
            self.eat()
            self.eat_kw("dhundo")
            return cmd("find_apriltag")
        if w == "ArUco":
            self.eat()
            self.eat_kw("dhundo")
            return cmd("find_aruco")
        if w == "TF":
            self.eat()
            self.eat_kw("pucho")
            frm = self._S(self.eat_string(), line)
            self.eat_kw("se")
            to = self._S(self.eat_string(), line)
            return cmd("tf", from_frame=frm, to_frame=to)

        # ---- raw ROS 2 ----
        if w == "bolo":
            self.eat()
            topic = self._S(self.eat_string(), line)
            return cmd("publish", topic=topic, value=self.expression())
        if w == "sewa":
            self.eat()
            self.eat_kw("bulao")
            name = self._S(self.eat_string(), line)
            if self.cur().type in (TokenType.NEWLINE, TokenType.EOF):
                args = A.DictLit(pairs=[], line=line)
            else:
                args = self.expression()
            return cmd("call_service", name=name, args=args)
        if w == "nodes":
            self.eat()
            self.eat_kw("dikhao")
            return cmd("list_nodes")
        if w == "topics":
            self.eat()
            self.eat_kw("dikhao")
            return cmd("list_topics")
        if w == "record":
            self.eat()
            if self.is_kw("shuru"):
                self.eat()
                return cmd("record_start", bag=self._S(self.eat_string(), line))
            self.eat_kw("band")
            return cmd("record_stop")
        if w == "launch":
            self.eat()
            pkg = self._S(self.eat_string(), line)
            return cmd("launch", package=pkg,
                       launch_file=self._S(self.eat_string(), line))
        if w == "urdf":
            self.eat()
            self.eat_kw("load")
            return cmd("urdf_load", path=self._S(self.eat_string(), line))

        # ---- ros2_control ----
        if w == "joint":
            self.eat()
            name = self._S(self.eat_string(), line)
            self.eat_kw("ko")
            value = self.expression()
            unit = self._unit_after(_ANGLE_UNITS, "rad")
            self.eat_kw("pe")
            self.eat_kw("le")
            self.eat_kw("jao")
            return cmd("joint_to", name=name, value=value, unit=self._S(unit, line))
        if w == "controller":
            self.eat()
            self.eat_kw("switch")
            return cmd("controller_switch",
                       name=self._S(self.eat_string(), line))
        if w == "torque":
            self.eat()
            on = self.eat_ident()
            return cmd("torque", on=self._B(on == "on", line))

        # ---- simulation ----
        if w == "simulation":
            self.eat()
            if self.is_kw("shuru"):
                self.eat()
                self.eat_kw("gazebo")
                return cmd("sim_start", world=self._S(self.eat_string(), line))
            self.eat_kw("band")
            return cmd("sim_stop")
        if w == "spawn":
            self.eat()
            model = self._S(self.eat_string(), line)
            x, y, z = self._tuple(3)
            return cmd("spawn", model=model, x=x, y=y, z=z)
        if w == "rviz":
            self.eat()
            self.eat_kw("kholo")
            return cmd("rviz_open")

        # ---- safety & timing ----
        if w == "band":
            self.eat()
            self.eat_kw("karo")
            return cmd("estop")
        if w == "workspace":
            self.eat()
            self.eat_kw("limit")
            items = self._tuple()
            return cmd("set_workspace_limit",
                       bounds=A.ListLit(items=items, line=line))
        if w == "ruko":
            self.eat()
            secs = self.expression()
            self._unit_after(_TIME_UNITS, "second")
            return A.ExprStmt(A.Call(name="_ruko", args=[secs], line=line), line=line)
        if w == "deadline":
            self.eat()
            secs = self.expression()
            self._unit_after(_TIME_UNITS, "second")
            return A.ExprStmt(A.Call(name="_deadline", args=[secs], line=line),
                              line=line)

        # ---- drone ----
        if w == "udaan":
            self.eat()
            self.eat_kw("bharo")
            return cmd("takeoff")
        if w == "utro":
            self.eat()
            return cmd("land")
        if w == "height":
            self.eat()
            h = self.expression()
            unit = self._unit_after(_DIST_UNITS, "meter")
            return cmd("set_height", h=h, unit=self._S(unit, line))

        return None

    # ------------------------------------------------------------- expressions
    def expression(self):
        return self.or_expr()

    def or_expr(self):
        node = self.and_expr()
        while self.is_kw("ya"):
            line = self._line()
            self.eat()
            node = A.BinOp(op="ya", left=node, right=self.and_expr(), line=line)
        return node

    def and_expr(self):
        node = self.not_expr()
        while self.is_kw("aur"):
            line = self._line()
            self.eat()
            node = A.BinOp(op="aur", left=node, right=self.not_expr(), line=line)
        return node

    def not_expr(self):
        if self.is_kw("nahi"):
            line = self._line()
            self.eat()
            return A.UnaryOp(op="nahi", operand=self.not_expr(), line=line)
        return self.compare()

    def compare(self):
        node = self.sum()
        while self.cur().type == TokenType.OP and \
                self.cur().value in ("==", "!=", "<", ">", "<=", ">="):
            line = self._line()
            op = self.eat().value
            node = A.BinOp(op=op, left=node, right=self.sum(), line=line)
        return node

    def sum(self):
        node = self.term()
        while self.cur().type == TokenType.OP and self.cur().value in ("+", "-"):
            line = self._line()
            op = self.eat().value
            node = A.BinOp(op=op, left=node, right=self.term(), line=line)
        return node

    def term(self):
        node = self.factor()
        while self.cur().type == TokenType.OP and self.cur().value in ("*", "/", "%"):
            line = self._line()
            op = self.eat().value
            node = A.BinOp(op=op, left=node, right=self.factor(), line=line)
        return node

    def factor(self):
        t = self.cur()
        line = t.line

        # unary minus
        if self.is_op("-"):
            self.eat()
            return A.UnaryOp(op="-", operand=self.factor(), line=line)

        if t.type == TokenType.NUMBER:
            self.eat()
            return A.Num(value=float(t.value), line=line)

        if t.type == TokenType.STRING:
            self.eat()
            return A.Str(value=t.value, line=line)

        if self.is_op("("):
            self.eat()
            node = self.expression()
            self.eat_op(")")
            return self._postfix(node)

        if self.is_op("["):
            return self._postfix(self.list_lit())

        if self.is_op("{"):
            return self._postfix(self.dict_lit())

        if t.type == TokenType.IDENT:
            w = t.value
            if w in ("sach", "jhooth"):
                self.eat()
                return A.Bool(value=(w == "sach"), line=line)
            # typed constructors
            if w in ("pose", "twist", "joints") and self.nxt().type == TokenType.OP \
                    and self.nxt().value == "(":
                self.eat()
                args = self._tuple()
                return self._postfix(A.TypedCtor(kind=w, args=args, line=line))
            # robot query used as an expression value
            if w in _QUERY_LEAD:
                cmd = self.robot_command_stmt()
                if isinstance(cmd, A.RobotCommand):
                    return cmd
            # function call
            if self.nxt().type == TokenType.OP and self.nxt().value == "(":
                self.eat()
                self.eat_op("(")
                args = []
                if not self.is_op(")"):
                    args.append(self.expression())
                    while self.is_op(","):
                        self.eat()
                        args.append(self.expression())
                self.eat_op(")")
                return self._postfix(A.Call(name=w, args=args, line=line))
            # plain identifier
            self.eat()
            return self._postfix(A.Ident(name=w, line=line))

        raise RCParseError(msg_hi="yeh samajh nahi aaya",
                           hint_en="unexpected token %r" % t.value, line=line)

    def _postfix(self, node):
        while self.is_op("."):
            line = self._line()
            self.eat()
            attr = self.eat_ident()
            node = A.Member(obj=node, attr=attr, line=line)
        return node

    def list_lit(self):
        line = self._line()
        self.eat_op("[")
        items = []
        if not self.is_op("]"):
            items.append(self.expression())
            while self.is_op(","):
                self.eat()
                if self.is_op("]"):
                    break
                items.append(self.expression())
        self.eat_op("]")
        return A.ListLit(items=items, line=line)

    def dict_lit(self):
        line = self._line()
        self.eat_op("{")
        pairs = []
        if not self.is_op("}"):
            k = self.expression()
            self.eat_op(":")
            v = self.expression()
            pairs.append((k, v))
            while self.is_op(","):
                self.eat()
                if self.is_op("}"):
                    break
                k = self.expression()
                self.eat_op(":")
                v = self.expression()
                pairs.append((k, v))
        self.eat_op("}")
        return A.DictLit(pairs=pairs, line=line)


def parse(src: str):
    """Source string -> Program AST."""
    return Parser(tokenize(src)).parse()
