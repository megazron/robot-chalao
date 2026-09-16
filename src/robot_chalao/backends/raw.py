"""Raw ROS 2 backend for Robot Chalao.

The escape hatch: `sun` (subscribe), `bolo` (publish), `sewa bulao` (service),
`action bhejo` (action), `nodes/topics dikhao`, `record shuru/band`, `launch`,
`urdf load`. This is how an advanced user drops down to bare rclpy while staying
in the Hinglish language.

ROS packages needed: a sourced ROS 2 (rclpy) plus whatever message/service/action
packages the topics you touch belong to; `ros2 bag` for recording.

All ROS imports are lazy; the module imports without ROS.
"""
from __future__ import annotations

import importlib
import subprocess
import time

from robot_chalao.backends.base import Backend
from robot_chalao.errors import RCBackendError, RCRosMissing


def _need_rclpy():
    try:
        import rclpy  # noqa: F401
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="ROS 2 (rclpy) nahi mila",
            hint_en="source your ROS 2 setup, or run with --simulate. (%s)"
                    % exc) from exc


def _import_type(type_name, kind="msg"):
    """Resolve 'pkg/msg/Type', 'pkg/Type' or 'pkg.msg.Type' to the class."""
    parts = type_name.replace(".", "/").split("/")
    if len(parts) == 2:
        pkg, name = parts[0], parts[1]
        sub = kind
    elif len(parts) == 3:
        pkg, sub, name = parts
    else:
        raise RCBackendError(
            msg_hi="type '%s' samajh nahi aaya" % type_name,
            hint_en="use 'pkg/msg/Type', e.g. 'std_msgs/msg/String'")
    try:
        mod = importlib.import_module("%s.%s" % (pkg, sub))
        return getattr(mod, name)
    except Exception as exc:  # noqa: BLE001
        raise RCBackendError(
            msg_hi="type '%s' load nahi hua" % type_name,
            hint_en="is the message package installed and sourced? (%s)"
                    % exc) from exc


class RawBackend(Backend):
    """Generic rclpy access. Implements the [raw] capability."""

    def __init__(self):
        self._node = None
        self._pubs = {}
        self._subs = []
        self._recorder = None
        self._launched = []

    def connect(self, name, config):
        _need_rclpy()
        import rclpy
        from rclpy.node import Node
        if not rclpy.ok():
            rclpy.init()
        self._node = Node("robot_chalao_raw_%s" % name)

    def disconnect(self):
        import contextlib
        self.record_stop()
        for p in self._launched:
            with contextlib.suppress(Exception):
                p.terminate()
        with contextlib.suppress(Exception):
            if self._node is not None:
                self._node.destroy_node()
        self._node = None

    def _ensure(self):
        if self._node is None:
            _need_rclpy()
            raise RCRosMissing(msg_hi="raw connect nahi hua",
                               hint_en="call `robot jodo` first")

    # ------------------------------------------------------------- pub / sub
    def subscribe(self, topic, type_name, callback):
        """`sun "topic" type mein msg ... khatam` -> register a callback that
        the interpreter's block wraps. Non-blocking; spins in the run loop."""
        self._ensure()
        msg_cls = _import_type(type_name, "msg")
        sub = self._node.create_subscription(msg_cls, topic, callback, 10)
        self._subs.append(sub)
        return sub

    def publish(self, topic, value, type_name=None):
        """`bolo "topic" value` -> publish. `value` may be a ready message, a
        Robot Chalao Twist/Pose (converted), or a scalar for std_msgs."""
        self._ensure()
        msg, msg_cls = _coerce_message(value, type_name)
        pub = self._pubs.get(topic)
        if pub is None:
            pub = self._node.create_publisher(msg_cls, topic, 10)
            self._pubs[topic] = pub
        pub.publish(msg)
        import rclpy
        rclpy.spin_once(self._node, timeout_sec=0.0)
        return True

    def call_service(self, name, args):
        """`sewa bulao "service" args` -> a blocking service call. `args` is a
        dict of request fields; the service type is inferred from the graph."""
        self._ensure()
        import rclpy
        srv_type = self._service_type(name)
        cli = self._node.create_client(srv_type, name)
        if not cli.wait_for_service(timeout_sec=5.0):
            raise RCBackendError(msg_hi="service '%s' nahi mila" % name,
                                 hint_en="check `ros2 service list`")
        req = srv_type.Request()
        for k, v in (args or {}).items():
            setattr(req, k, v)
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self._node, fut)
        return fut.result()

    def send_action(self, name, goal, progress_cb=None):
        """`action bhejo "name" goal ... progress mein fb ... khatam`."""
        self._ensure()
        import rclpy
        from rclpy.action import ActionClient
        act_type = self._action_type(name)
        client = ActionClient(self._node, act_type, name)
        if not client.wait_for_server(timeout_sec=5.0):
            raise RCBackendError(msg_hi="action server '%s' nahi mila" % name,
                                 hint_en="check `ros2 action list`")
        goal_msg = goal if not isinstance(goal, dict) else _fill(act_type.Goal(), goal)

        def _fb(feedback):
            if progress_cb:
                progress_cb(feedback.feedback)
        send_fut = client.send_goal_async(goal_msg, feedback_callback=_fb)
        rclpy.spin_until_future_complete(self._node, send_fut)
        handle = send_fut.result()
        if not handle.accepted:
            raise RCBackendError(msg_hi="action goal reject ho gaya",
                                 hint_en="server rejected the goal")
        res_fut = handle.get_result_async()
        rclpy.spin_until_future_complete(self._node, res_fut)
        return res_fut.result().result

    # ------------------------------------------------------------- graph
    def list_nodes(self):
        """`nodes dikhao` -> list of node names."""
        self._ensure()
        return sorted("%s%s" % (ns if ns != "/" else "/", n)
                      for n, ns in self._node.get_node_names_and_namespaces())

    def list_topics(self):
        """`topics dikhao` -> list of (topic, [types])."""
        self._ensure()
        return sorted(self._node.get_topic_names_and_types())

    # ------------------------------------------------------------- rosbag
    def record_start(self, bag):
        """`record shuru "bag"` -> `ros2 bag record -a -o <bag>`."""
        _need_rclpy()
        if self._recorder is not None:
            raise RCBackendError(msg_hi="recording pehle se chal rahi hai",
                                 hint_en="call `record band` first")
        try:
            self._recorder = subprocess.Popen(
                ["ros2", "bag", "record", "-a", "-o", bag])
        except FileNotFoundError as exc:
            raise RCRosMissing(msg_hi="ros2 command nahi mila",
                               hint_en="source your ROS 2 setup") from exc
        return True

    def record_stop(self):
        """`record band` -> stop the recorder."""
        if self._recorder is not None:
            self._recorder.send_signal(2)   # SIGINT for a clean bag
            try:
                self._recorder.wait(timeout=10)
            except Exception:  # noqa: BLE001
                self._recorder.terminate()
            self._recorder = None
        return True

    # ------------------------------------------------------------- misc
    def launch(self, package, launch_file):
        """`launch "package" "file.launch.py"` -> `ros2 launch pkg file`."""
        _need_rclpy()
        try:
            p = subprocess.Popen(["ros2", "launch", package, launch_file])
        except FileNotFoundError as exc:
            raise RCRosMissing(msg_hi="ros2 command nahi mila",
                               hint_en="source your ROS 2 setup") from exc
        self._launched.append(p)
        return True

    def urdf_load(self, path):
        """`urdf load "robot.urdf"` -> read the file and set robot_description."""
        self._ensure()
        with open(path) as f:
            urdf = f.read()
        try:
            from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
            pv = ParameterValue(type=ParameterType.PARAMETER_STRING,
                                string_value=urdf)
            self._node.declare_parameter("robot_description", urdf)
            _ = Parameter(name="robot_description", value=pv)
        except Exception:  # noqa: BLE001
            pass
        return urdf

    # ------------------------------------------------------------- helpers
    def _service_type(self, name):
        for n, types in self._node.get_service_names_and_types():
            if n == name and types:
                return _import_type(types[0], "srv")
        raise RCBackendError(msg_hi="service '%s' ka type nahi mila" % name,
                             hint_en="is the service advertised right now?")

    def _action_type(self, name):
        # action types are not directly in the topic graph; expect fully qualified
        raise_hint = ("pass the action type via config, or use the moveit/nav2 "
                      "verbs which know their action types")
        try:
            from rclpy.action import get_action_names_and_types
            for n, types in get_action_names_and_types(self._node):
                if n == name and types:
                    return _import_type(types[0], "action")
        except Exception:  # noqa: BLE001
            pass
        raise RCBackendError(msg_hi="action '%s' ka type nahi mila" % name,
                             hint_en=raise_hint)


def _coerce_message(value, type_name):
    """Turn a Robot Chalao value into a ROS message + its class."""
    from robot_chalao.types import Pose, Twist
    if type_name:
        cls = _import_type(type_name, "msg")
        if hasattr(value, "__dict__") and not isinstance(value, (Pose, Twist)):
            return value, cls          # already a ROS message
        return _fill(cls(), value if isinstance(value, dict) else {}), cls
    if isinstance(value, Twist):
        from geometry_msgs.msg import Twist as RosTwist
        m = RosTwist()
        m.linear.x, m.linear.y, m.linear.z = value.vx, value.vy, value.vz
        m.angular.x, m.angular.y, m.angular.z = value.wx, value.wy, value.wz
        return m, RosTwist
    if isinstance(value, Pose):
        from geometry_msgs.msg import Pose as RosPose
        m = RosPose()
        m.position.x, m.position.y, m.position.z = value.x, value.y, value.z
        m.orientation.w = 1.0
        return m, RosPose
    if isinstance(value, str):
        from std_msgs.msg import String
        return String(data=value), String
    if isinstance(value, bool):
        from std_msgs.msg import Bool
        return Bool(data=value), Bool
    if isinstance(value, (int, float)):
        from std_msgs.msg import Float64
        return Float64(data=float(value)), Float64
    raise RCBackendError(
        msg_hi="is value ka type publish nahi kar sakte",
        hint_en="give a type_name, or use a Twist/Pose/str/number")


def _fill(msg, fields):
    for k, v in (fields or {}).items():
        setattr(msg, k, v)
    return msg
