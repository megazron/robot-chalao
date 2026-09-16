"""MAVROS backend for the drone capability of Robot Chalao.

Hinglish verbs: `udaan bharo` (takeoff), `utro` (land), `height 2 meter`. The
mobile-base verbs (`aage chalo`, `ghumo`) are also mapped to velocity setpoints
so a drone can be driven with the same words as a ground robot.

ROS packages needed:
    ros-${ROS_DISTRO}-mavros  ros-${ROS_DISTRO}-mavros-extras  (+ a PX4/ArduPilot SITL or vehicle)
Install (Jazzy example):
    sudo apt install ros-jazzy-mavros ros-jazzy-mavros-extras

All ROS imports are lazy; the module imports without ROS.
"""
from __future__ import annotations

import math
import time

from robot_chalao.backends.base import Backend
from robot_chalao.errors import RCBackendError, RCRosMissing


def _need_rclpy():
    try:
        import rclpy  # noqa: F401
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="ROS 2 (rclpy) nahi mila, drone nahi ud sakta",
            hint_en="source your ROS 2 setup, or run with --simulate. (%s)"
                    % exc) from exc


def _need_mavros():
    _need_rclpy()
    try:
        from mavros_msgs.srv import CommandBool  # noqa: F401
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="MAVROS (mavros_msgs) nahi mila",
            hint_en="install ros-<distro>-mavros. (%s)" % exc) from exc


class MavrosBackend(Backend):
    """Drone control through MAVROS. Implements [drone] and part of [base]."""

    def __init__(self):
        self._cfg = {}
        self._node = None
        self._sp_pub = None
        self._height = 0.0

    def connect(self, name, config):
        _need_rclpy()
        import rclpy
        from rclpy.node import Node
        self._cfg = dict(config or {})
        if not rclpy.ok():
            rclpy.init()
        self._node = Node("robot_chalao_drone_%s" % name)

    def disconnect(self):
        import contextlib
        with contextlib.suppress(Exception):
            if self._node is not None:
                self._node.destroy_node()
        self._node = self._sp_pub = None

    def _ensure(self):
        if self._node is None:
            _need_rclpy()
            raise RCRosMissing(msg_hi="drone connect nahi hua",
                               hint_en="call `robot jodo` first")

    def _call(self, srv_type, name, **fields):
        import rclpy
        cli = self._node.create_client(srv_type, name)
        if not cli.wait_for_service(timeout_sec=5.0):
            raise RCBackendError(msg_hi="MAVROS service '%s' nahi mila" % name,
                                 hint_en="is mavros running and connected?")
        req = srv_type.Request()
        for k, v in fields.items():
            setattr(req, k, v)
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self._node, fut)
        return fut.result()

    # -------------------------------------------------------------- drone
    def takeoff(self):
        """`udaan bharo` -> GUIDED mode, arm, takeoff to the last set height
        (default 2 m)."""
        _need_mavros()
        self._ensure()
        from mavros_msgs.srv import CommandBool, CommandTOL, SetMode
        self._call(SetMode, "/mavros/set_mode", custom_mode="GUIDED")
        self._call(CommandBool, "/mavros/cmd/arming", value=True)
        h = self._height or 2.0
        self._call(CommandTOL, "/mavros/cmd/takeoff", altitude=float(h))
        return True

    def land(self):
        """`utro` -> AUTO.LAND (PX4) / LAND, then disarm."""
        _need_mavros()
        self._ensure()
        from mavros_msgs.srv import CommandBool, CommandTOL, SetMode
        self._call(SetMode, "/mavros/set_mode", custom_mode="AUTO.LAND")
        self._call(CommandTOL, "/mavros/cmd/land", altitude=0.0)
        time.sleep(1.0)
        self._call(CommandBool, "/mavros/cmd/arming", value=False)
        return True

    def set_height(self, h, unit="meter"):
        """`height 2 meter` -> position setpoint at altitude h, x/y held."""
        _need_mavros()
        self._ensure()
        self._height = _to_meters(h, unit)
        from geometry_msgs.msg import PoseStamped
        if self._sp_pub is None:
            self._sp_pub = self._node.create_publisher(
                PoseStamped, "/mavros/setpoint_position/local", 10)
        import rclpy
        sp = PoseStamped()
        sp.pose.position.z = self._height
        sp.pose.orientation.w = 1.0
        # a setpoint stream is required; publish a short burst
        for _ in range(20):
            self._sp_pub.publish(sp)
            rclpy.spin_once(self._node, timeout_sec=0.0)
            time.sleep(0.05)
        return True

    # --------------------------------------------- base verbs as velocity
    def base_twist(self, v, w):
        """`speed_move v w` on a drone -> body-frame velocity setpoint."""
        _need_mavros()
        self._ensure()
        import rclpy
        from geometry_msgs.msg import TwistStamped
        pub = self._node.create_publisher(
            TwistStamped, "/mavros/setpoint_velocity/cmd_vel", 10)
        msg = TwistStamped()
        msg.twist.linear.x = float(v)
        msg.twist.angular.z = float(w)
        pub.publish(msg)
        rclpy.spin_once(self._node, timeout_sec=0.0)
        return True

    def base_move(self, distance, unit="meter", backward=False):
        d = _to_meters(distance, unit) * (-1.0 if backward else 1.0)
        speed = 0.5
        self.base_twist(speed if d >= 0 else -speed, 0.0)
        time.sleep(abs(d) / speed)
        self.base_twist(0.0, 0.0)
        return True

    def base_rotate(self, angle, unit="degree"):
        rad = math.radians(angle) if unit.startswith("deg") else float(angle)
        w = 0.5
        self.base_twist(0.0, w if rad >= 0 else -w)
        time.sleep(abs(rad) / w)
        self.base_twist(0.0, 0.0)
        return True


def _to_meters(distance, unit):
    u = (unit or "meter").lower()
    if u.startswith("cm"):
        return float(distance) / 100.0
    if u.startswith("mm"):
        return float(distance) / 1000.0
    return float(distance)
