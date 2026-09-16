"""Robot Chalao -> Python (rclpy + moveit_py + nav2_simple_commander).

Yeh transpiler ek `.rc` program ko padhne-yogya Python mein badalta hai, taaki
advanced user dekh sakein ki neeche ROS 2 mein kya ho raha hai. Generated code
hamesha valid Python hota hai (bina ROS ke bhi `compile()` ho jaata hai);
imports guard kiye gaye hain, aur ek chhota `Bot` driver har istemaal kiye
method ka asli-jaisa body deta hai (ya ek saaf TODO).

(Transpiles a .rc program into readable Python. The output always compiles even
without ROS installed; imports are guarded and a small Bot driver carries real
ROS bodies for common methods.)
"""
from __future__ import annotations

from . import ast_nodes as A

_HEADER = '''"""Auto-generated from a Robot Chalao (.rc) program.

Ise haath se edit karne ke bajaye .rc file badlein aur dobara transpile karein.
Yeh Python rclpy + moveit_py + nav2_simple_commander use karta hai. Jahan ROS
install nahi, wahan yeh import-guard ke saath bhi chal/padha ja sakta hai.
"""
from dataclasses import dataclass, field

try:
    import rclpy
    from rclpy.node import Node
    HAVE_ROS = True
except Exception:
    HAVE_ROS = False

try:
    from moveit.planning import MoveItPy            # noqa: F401
    HAVE_MOVEIT = True
except Exception:
    HAVE_MOVEIT = False

try:
    from nav2_simple_commander.robot_navigator import BasicNavigator  # noqa: F401
    HAVE_NAV2 = True
except Exception:
    HAVE_NAV2 = False


@dataclass
class Pose:
    x: float = 0.0; y: float = 0.0; z: float = 0.0
    roll: float = 0.0; pitch: float = 0.0; yaw: float = 0.0


@dataclass
class Twist:
    vx: float = 0.0; wz: float = 0.0


@dataclass
class Joints:
    values: list = field(default_factory=list)
'''

# Real-ish bodies for common backend methods. Others get a clear TODO.
_BODIES = {
    "connect": [
        "if HAVE_ROS and not rclpy.ok():",
        "    rclpy.init()",
        "self.node = Node('robot_chalao') if HAVE_ROS else None",
        "self.robot_name = name",
        "# MoveItPy / BasicNavigator yahan config ke hisaab se banayein",
        "print('connected to', name)",
    ],
    "disconnect": [
        "if HAVE_ROS and rclpy.ok():",
        "    rclpy.shutdown()",
        "print('disconnected')",
    ],
    "arm_home": [
        "# moveit_py: named target 'home' pe le jao",
        "self.arm.set_start_state_to_current_state()",
        "self.arm.set_goal_state(configuration_name='home')",
        "self._plan_and_execute(self.arm)",
    ],
    "arm_pose": [
        "# moveit_py: ee_link ko pose pe le jao",
        "from geometry_msgs.msg import PoseStamped",
        "ps = PoseStamped(); ps.header.frame_id = self.base_link",
        "ps.pose.position.x, ps.pose.position.y, ps.pose.position.z = pose.x, pose.y, pose.z",
        "self.arm.set_start_state_to_current_state()",
        "self.arm.set_goal_state(pose_stamped_msg=ps, pose_link=self.ee_link)",
        "self._plan_and_execute(self.arm)",
    ],
    "arm_cartesian": [
        "# straight-line Cartesian move to (x, y, z) via compute_cartesian_path",
        "self._cartesian_to(x, y, z)",
    ],
    "gripper": [
        "# gripper action/topic: close=True => pakdo, False => chhodo",
        "self._gripper(close)",
    ],
    "set_speed": [
        "self.max_velocity_scaling = scale",
        "print('speed scaling', scale)",
    ],
    "nav_to": [
        "# nav2_simple_commander se goal pose",
        "from geometry_msgs.msg import PoseStamped",
        "goal = PoseStamped(); goal.header.frame_id = 'map'",
        "goal.pose.position.x, goal.pose.position.y = x, y",
        "self.navigator.goToPose(goal)",
        "while not self.navigator.isTaskComplete():",
        "    pass",
    ],
    "base_twist": [
        "from geometry_msgs.msg import Twist as RosTwist",
        "msg = RosTwist(); msg.linear.x = float(v); msg.angular.z = float(w)",
        "self.cmd_vel_pub.publish(msg)",
    ],
    "base_stop": [
        "from geometry_msgs.msg import Twist as RosTwist",
        "self.cmd_vel_pub.publish(RosTwist())",
    ],
    "publish": [
        "# raw publish: apne node par ek publisher banao aur bhejo",
        "self._publish(topic, value)",
    ],
    "find_object": [
        "# perception plugin (OpenCV/YOLO) se object dhoondo",
        "return self._find_object(description)",
    ],
    "estop": [
        "# e-stop: sabhi active goals cancel karo aur zero velocity bhejo",
        "self._estop()",
    ],
    "takeoff": [
        "# MAVROS: arm + takeoff",
        "self._mavros_takeoff()",
    ],
}


class Transpiler:
    """`Transpiler().transpile(program) -> str` (valid Python)."""

    def transpile(self, program):
        used = set()
        main_lines = []
        for st in program.body:
            main_lines += self._stmt(st, 1, used)
        out = [_HEADER, "", "class Bot:", '    """Generated ROS 2 driver."""', ""]
        out.append("    def __init__(self):")
        out.append("        self.base_link = 'base_link'")
        out.append("        self.ee_link = 'tool0'")
        out.append("        self.max_velocity_scaling = 0.3")
        out.append("")
        for method in sorted(used):
            out += self._method(method)
        # helper stubs referenced above, kept valid + honest
        out += [
            "    def _plan_and_execute(self, group):",
            "        raise NotImplementedError('wire up moveit_py plan+execute')",
            "    def _cartesian_to(self, x, y, z):",
            "        raise NotImplementedError('wire up compute_cartesian_path')",
            "    def _gripper(self, close):",
            "        raise NotImplementedError('wire up your gripper action/topic')",
            "    def _publish(self, topic, value):",
            "        raise NotImplementedError('create a publisher for this topic')",
            "    def _find_object(self, description):",
            "        raise NotImplementedError('plug in OpenCV/YOLO perception')",
            "    def _estop(self):",
            "        raise NotImplementedError('cancel goals + zero velocity')",
            "    def _mavros_takeoff(self):",
            "        raise NotImplementedError('wire up MAVROS arm+takeoff')",
            "",
        ]
        out += ["", "def main():", "    bot = Bot()"]
        out += main_lines or ["    pass"]
        out += ["", "", "if __name__ == '__main__':", "    main()", ""]
        return "\n".join(out)

    # ---- method emitter
    def _method(self, method):
        body = _BODIES.get(method)
        # figure out the parameter names from the sim/base signature style
        sig = _SIGNATURES.get(method, "self, **kwargs")
        lines = ["    def %s(%s):" % (method, sig)]
        if body is None:
            lines.append("        # TODO: %s -- apne robot ke liye implement karein" % method)
            lines.append("        raise NotImplementedError(%r)" % method)
        else:
            for b in body:
                lines.append("        " + b)
        lines.append("")
        return lines

    # ---- statements -> python
    def _stmt(self, node, ind, used):
        pad = "    " * ind
        t = type(node).__name__
        if t == "Let":
            return [pad + "%s = %s" % (node.name, self._expr(node.expr, used))]
        if t == "Print":
            args = ", ".join(self._expr(e, used) for e in node.exprs)
            return [pad + "print(%s)" % args]
        if t == "ExprStmt":
            return [pad + self._expr(node.expr, used)]
        if t == "Return":
            return [pad + "return" + (" " + self._expr(node.expr, used)
                                      if node.expr is not None else "")]
        if t == "Break":
            return [pad + "break"]
        if t == "If":
            out = [pad + "if %s:" % self._expr(node.cond, used)]
            out += self._body(node.then, ind + 1, used)
            if node.orelse:
                out.append(pad + "else:")
                out += self._body(node.orelse, ind + 1, used)
            return out
        if t == "While":
            out = [pad + "while %s:" % self._expr(node.cond, used)]
            out += self._body(node.body, ind + 1, used)
            return out
        if t == "ForEach":
            out = [pad + "for %s in %s:" % (node.var, self._expr(node.iterable, used))]
            out += self._body(node.body, ind + 1, used)
            return out
        if t == "FuncDef":
            out = [pad + "def %s(%s):" % (node.name, ", ".join(node.params))]
            out += self._body(node.body, ind + 1, used)
            return out
        if t == "Try":
            out = [pad + "try:"]
            out += self._body(node.body, ind + 1, used)
            out.append(pad + "except Exception as %s:" % (node.err_name or "_e"))
            out += self._body(node.handler, ind + 1, used)
            return out
        if t == "Timer":
            out = [pad + "for _tick in range(3):  # har %s %s mein (timer)"
                   % (self._expr(node.period, used), node.unit)]
            out += self._body(node.body, ind + 1, used)
            return out
        if t == "Subscribe":
            out = [pad + "def _on_msg(%s):" % node.var]
            out += self._body(node.body, ind + 1, used)
            used.add("subscribe")
            out.append(pad + "bot.subscribe(%s, %r, _on_msg)"
                       % (self._expr(node.topic, used), node.type_name))
            return out
        if t == "ActionSend":
            used.add("send_action")
            cb = "None"
            out = []
            if node.progress_var is not None:
                out.append(pad + "def _on_fb(%s):" % node.progress_var)
                out += self._body(node.body, ind + 1, used)
                cb = "_on_fb"
            out.append(pad + "bot.send_action(%s, %s, %s)"
                       % (self._expr(node.name, used), self._expr(node.goal, used), cb))
            return out
        if t == "Import":
            return [pad + "# import %r -- .rc module (transpile separately)" % node.path]
        if t == "RobotCommand":
            return [pad + self._expr(node, used)]
        return [pad + "pass  # unhandled: " + t]

    def _body(self, stmts, ind, used):
        out = []
        for s in stmts:
            out += self._stmt(s, ind, used)
        return out or ["    " * ind + "pass"]

    # ---- expressions -> python
    def _expr(self, node, used):
        t = type(node).__name__
        if t == "Num":
            v = node.value
            return repr(int(v) if float(v).is_integer() else v)
        if t == "Str":
            return repr(node.value)
        if t == "Bool":
            return "True" if node.value else "False"
        if t == "Ident":
            return node.name
        if t == "ListLit":
            return "[%s]" % ", ".join(self._expr(x, used) for x in node.items)
        if t == "DictLit":
            return "{%s}" % ", ".join(
                "%s: %s" % (self._expr(k, used), self._expr(v, used))
                for k, v in node.pairs)
        if t == "Member":
            return "%s.%s" % (self._expr(node.obj, used), node.attr)
        if t == "UnaryOp":
            if node.op == "nahi":
                return "(not %s)" % self._expr(node.operand, used)
            return "(-%s)" % self._expr(node.operand, used)
        if t == "BinOp":
            op = {"aur": "and", "ya": "or"}.get(node.op, node.op)
            return "(%s %s %s)" % (self._expr(node.left, used), op,
                                   self._expr(node.right, used))
        if t == "TypedCtor":
            kind = node.kind.capitalize()
            return "%s(%s)" % (kind, ", ".join(self._expr(a, used) for a in node.args))
        if t == "Call":
            return "%s(%s)" % (node.name,
                               ", ".join(self._expr(a, used) for a in node.args))
        if t == "RobotCommand":
            used.add(node.method)
            kw = ", ".join("%s=%s" % (k, self._expr(v, used))
                           for k, v in node.args.items())
            sel = "" if node.selector is None else "  # robot=%r" % node.selector
            return "bot.%s(%s)%s" % (node.method, kw, sel)
        return "None  # unhandled expr: " + t


# parameter signatures for generated Bot methods (readability only)
_SIGNATURES = {
    "connect": "self, name",
    "disconnect": "self",
    "arm_home": "self",
    "arm_pose": "self, pose",
    "arm_joints": "self, joints",
    "arm_cartesian": "self, x, y, z",
    "arm_named": "self, name",
    "gripper": "self, close",
    "set_speed": "self, scale",
    "set_planner": "self, planner",
    "nav_to": "self, x, y, theta",
    "base_move": "self, distance, unit='meter', backward=False",
    "base_rotate": "self, angle, unit='degree'",
    "base_twist": "self, v, w",
    "base_stop": "self",
    "publish": "self, topic, value",
    "subscribe": "self, topic, type_name, callback",
    "send_action": "self, name, goal, progress_cb=None",
    "find_object": "self, description",
    "estop": "self",
    "takeoff": "self",
    "land": "self",
    "set_height": "self, h, unit='meter'",
}


def transpile(src: str) -> str:
    """Source string -> Python source string."""
    from .parser import parse
    return Transpiler().transpile(parse(src))
