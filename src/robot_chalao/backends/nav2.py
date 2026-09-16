"""Nav2 + cmd_vel backend for the mobile-base capability of Robot Chalao.

Maps the Hinglish base verbs (`aage chalo`, `ghumo`, `yahan jao`, `waypoints
follow`, `map banao`, ...) onto Nav2 through `nav2_simple_commander`, and the
open-loop verbs onto a `/cmd_vel` publisher.

ROS packages needed:
    ros-${ROS_DISTRO}-navigation2  ros-${ROS_DISTRO}-nav2-simple-commander
    ros-${ROS_DISTRO}-slam-toolbox  ros-${ROS_DISTRO}-nav2-map-server
Install (Jazzy example):
    sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-simple-commander \
                     ros-jazzy-slam-toolbox

All ROS imports are lazy, so this module imports on a machine with no ROS.
"""
from __future__ import annotations

import math
import subprocess
import time

from robot_chalao.backends.base import Backend
from robot_chalao.errors import RCBackendError, RCRosMissing
from robot_chalao.types import Pose


def _need_rclpy():
    try:
        import rclpy  # noqa: F401
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="ROS 2 (rclpy) nahi mila, gaadi nahi chal sakti",
            hint_en="source your ROS 2 setup, or run with --simulate. (%s)"
                    % exc) from exc


def _need_nav2():
    _need_rclpy()
    try:
        from nav2_simple_commander.robot_navigator import BasicNavigator  # noqa
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="Nav2 (nav2_simple_commander) nahi mila",
            hint_en="install ros-<distro>-nav2-simple-commander. (%s)"
                    % exc) from exc


class Nav2Backend(Backend):
    """Mobile base through Nav2 and /cmd_vel. Only the [base] capability is
    implemented; other capabilities inherit the base RCBackendError."""

    DEFAULT_LIN = 0.2       # m/s for open-loop moves
    DEFAULT_ANG = 0.5       # rad/s for open-loop turns

    def __init__(self):
        self._cfg = {}
        self._cmd_vel_topic = "/cmd_vel"
        self._node = None
        self._pub = None
        self._nav = None            # BasicNavigator
        self._speed_lin = self.DEFAULT_LIN
        self._speed_ang = self.DEFAULT_ANG

    # ---------------------------------------------------------------- connect
    def connect(self, name, config):
        _need_rclpy()
        import rclpy
        from geometry_msgs.msg import Twist as RosTwist
        from rclpy.node import Node

        self._cfg = dict(config or {})
        self._cmd_vel_topic = self._cfg.get("cmd_vel", self._cmd_vel_topic)
        if not rclpy.ok():
            rclpy.init()
        self._node = Node("robot_chalao_base_%s" % name)
        self._pub = self._node.create_publisher(RosTwist, self._cmd_vel_topic, 10)

    def disconnect(self):
        import contextlib
        with contextlib.suppress(Exception):
            if self._nav is not None:
                self._nav.lifecycleShutdown()
        with contextlib.suppress(Exception):
            if self._node is not None:
                self._node.destroy_node()
        self._node = self._pub = self._nav = None

    def _ensure_pub(self):
        if self._pub is None:
            _need_rclpy()
            raise RCRosMissing(msg_hi="base connect nahi hua",
                               hint_en="call `robot jodo` first")

    def _twist(self, v, w):
        from geometry_msgs.msg import Twist as RosTwist
        import rclpy
        msg = RosTwist()
        msg.linear.x = float(v)
        msg.angular.z = float(w)
        self._pub.publish(msg)
        rclpy.spin_once(self._node, timeout_sec=0.0)

    # ------------------------------------------------------------- open loop
    def base_move(self, distance, unit="meter", backward=False):
        """`aage chalo 1 meter` / `peeche chalo`. Open-loop timed move on
        /cmd_vel; distance in meters (cm/mm accepted)."""
        self._ensure_pub()
        d = _to_meters(distance, unit)
        sign = -1.0 if backward else 1.0
        speed = self._speed_lin * sign
        duration = abs(d) / self._speed_lin if self._speed_lin else 0.0
        self._drive_for(speed, 0.0, duration)
        return True

    def base_rotate(self, angle, unit="degree"):
        """`ghumo 90 degree`. Open-loop timed rotation on /cmd_vel."""
        self._ensure_pub()
        rad = math.radians(angle) if unit.startswith("deg") else float(angle)
        sign = 1.0 if rad >= 0 else -1.0
        duration = abs(rad) / self._speed_ang if self._speed_ang else 0.0
        self._drive_for(0.0, self._speed_ang * sign, duration)
        return True

    def base_twist(self, v, w):
        """`speed_move v w` -> one raw Twist (held until the next command)."""
        self._ensure_pub()
        self._twist(v, w)
        return True

    def base_stop(self):
        """`ruk jao` -> zero Twist."""
        self._ensure_pub()
        self._twist(0.0, 0.0)
        return True

    def _drive_for(self, v, w, duration):
        end = time.monotonic() + duration
        while time.monotonic() < end:
            self._twist(v, w)
            time.sleep(0.05)
        self._twist(0.0, 0.0)

    # ------------------------------------------------------------- nav2
    def _navigator(self):
        if self._nav is None:
            _need_nav2()
            from nav2_simple_commander.robot_navigator import BasicNavigator
            self._nav = BasicNavigator()
        return self._nav

    def map_load(self, path):
        """`map load "file"` -> hand a map yaml to Nav2 and wait for active."""
        nav = self._navigator()
        nav.changeMap(path)
        nav.waitUntilNav2Active()
        return True

    def localize(self, pose=None):
        """`localize` -> set the AMCL initial pose (defaults to origin)."""
        nav = self._navigator()
        p = pose or Pose()
        nav.setInitialPose(_pose_stamped(p))
        nav.waitUntilNav2Active()
        return True

    def nav_to(self, x, y, theta):
        """`yahan jao (x,y,theta)` -> a single Nav2 goal, blocks to result."""
        nav = self._navigator()
        goal = _pose_stamped(Pose(x=x, y=y, yaw=theta))
        nav.goToPose(goal)
        while not nav.isTaskComplete():
            time.sleep(0.1)
        from nav2_simple_commander.robot_navigator import TaskResult
        if nav.getResult() != TaskResult.SUCCEEDED:
            raise RCBackendError(msg_hi="goal tak nahi pahuncha",
                                 hint_en="navigation failed or was cancelled")
        return True

    def follow_waypoints(self, points):
        """`waypoints follow [...]` -> a list of (x,y,theta) goals in order."""
        nav = self._navigator()
        goals = [_pose_stamped(Pose(x=p[0], y=p[1],
                                    yaw=(p[2] if len(p) > 2 else 0.0)))
                 for p in points]
        nav.followWaypoints(goals)
        while not nav.isTaskComplete():
            time.sleep(0.1)
        return True

    def slam_start(self):
        """`map banao` -> bring up slam_toolbox (async mapping)."""
        _need_rclpy()
        try:
            subprocess.Popen(
                ["ros2", "launch", "slam_toolbox", "online_async_launch.py"])
        except FileNotFoundError as exc:
            raise RCRosMissing(msg_hi="ros2 command nahi mila",
                               hint_en="source your ROS 2 setup") from exc
        return True

    def map_save(self, name):
        """`map save "name"` -> nav2_map_server map_saver_cli."""
        _need_rclpy()
        try:
            subprocess.run(
                ["ros2", "run", "nav2_map_server", "map_saver_cli",
                 "-f", name], check=True)
        except FileNotFoundError as exc:
            raise RCRosMissing(msg_hi="ros2 command nahi mila",
                               hint_en="source your ROS 2 setup") from exc
        return True

    def obstacle_near(self):
        """`obstacle nazdeek hai?` -> True if the nearest /scan return is under
        0.5 m. Reads one LaserScan message."""
        _need_rclpy()
        import rclpy
        from sensor_msgs.msg import LaserScan
        got = {}

        def _cb(msg):
            vals = [r for r in msg.ranges if r and math.isfinite(r) and r > 0.0]
            got["min"] = min(vals) if vals else float("inf")

        sub = self._node.create_subscription(LaserScan, "/scan", _cb, 10)
        end = time.monotonic() + 2.0
        while "min" not in got and time.monotonic() < end:
            rclpy.spin_once(self._node, timeout_sec=0.1)
        self._node.destroy_subscription(sub)
        return got.get("min", float("inf")) < 0.5

    def set_speed_limit(self, v):
        """Shared with the safety verb `speed limit`; caps the open-loop speed."""
        self._speed_lin = min(self._speed_lin, float(v))
        return self._speed_lin


def _to_meters(distance, unit):
    u = (unit or "meter").lower()
    if u.startswith("cm"):
        return float(distance) / 100.0
    if u.startswith("mm"):
        return float(distance) / 1000.0
    return float(distance)


def _pose_stamped(pose):
    from geometry_msgs.msg import PoseStamped
    ps = PoseStamped()
    ps.header.frame_id = "map"
    ps.pose.position.x = float(pose.x)
    ps.pose.position.y = float(pose.y)
    cy, sy = math.cos(pose.yaw * 0.5), math.sin(pose.yaw * 0.5)
    ps.pose.orientation.z = sy
    ps.pose.orientation.w = cy
    return ps
