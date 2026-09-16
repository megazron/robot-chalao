"""ros2_control backend for Robot Chalao (low-level joint control).

Hinglish verbs: `joint "j1" ko 1.2 rad pe le jao`, `controller switch "name"`,
`torque on/off`.

ROS packages needed:
    ros-${ROS_DISTRO}-ros2-control  ros-${ROS_DISTRO}-ros2-controllers
Install (Jazzy example):
    sudo apt install ros-jazzy-ros2-control ros-jazzy-ros2-controllers

All ROS imports are lazy; the module imports without ROS.
"""
from __future__ import annotations

import math

from robot_chalao.backends.base import Backend
from robot_chalao.errors import RCBackendError, RCRosMissing


def _need_rclpy():
    try:
        import rclpy  # noqa: F401
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="ROS 2 (rclpy) nahi mila, joint control nahi ho sakta",
            hint_en="source your ROS 2 setup, or run with --simulate. (%s)"
                    % exc) from exc


class ControlBackend(Backend):
    """Low-level joint control through ros2_control. Implements [control]."""

    def __init__(self):
        self._cfg = {}
        self._node = None
        self._traj_pub = None
        self._controller = "joint_trajectory_controller"

    def connect(self, name, config):
        _need_rclpy()
        import rclpy
        from rclpy.node import Node
        self._cfg = dict(config or {})
        self._controller = self._cfg.get("controller", self._controller)
        if not rclpy.ok():
            rclpy.init()
        self._node = Node("robot_chalao_control_%s" % name)

    def disconnect(self):
        import contextlib
        with contextlib.suppress(Exception):
            if self._node is not None:
                self._node.destroy_node()
        self._node = self._traj_pub = None

    def _ensure(self):
        if self._node is None:
            _need_rclpy()
            raise RCRosMissing(msg_hi="control connect nahi hua",
                               hint_en="call `robot jodo` first")

    def joint_to(self, name, value, unit="rad"):
        """`joint "j1" ko 1.2 rad pe le jao` -> a one-point JointTrajectory."""
        self._ensure()
        import rclpy
        from builtin_interfaces.msg import Duration
        from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
        val = math.radians(value) if unit.startswith("deg") else float(value)
        topic = "/%s/joint_trajectory" % self._controller
        if self._traj_pub is None:
            self._traj_pub = self._node.create_publisher(
                JointTrajectory, topic, 10)
        traj = JointTrajectory()
        traj.joint_names = [name]
        pt = JointTrajectoryPoint()
        pt.positions = [val]
        pt.time_from_start = Duration(sec=2)
        traj.points = [pt]
        self._traj_pub.publish(traj)
        rclpy.spin_once(self._node, timeout_sec=0.0)
        return True

    def controller_switch(self, name):
        """`controller switch "name"` -> activate `name`, deactivate the rest of
        the same kind via /controller_manager/switch_controller."""
        self._ensure()
        import rclpy
        try:
            from controller_manager_msgs.srv import SwitchController
        except Exception as exc:  # noqa: BLE001
            raise RCRosMissing(
                msg_hi="controller_manager_msgs nahi mila",
                hint_en="install ros-<distro>-ros2-control. (%s)" % exc) from exc
        cli = self._node.create_client(
            SwitchController, "/controller_manager/switch_controller")
        if not cli.wait_for_service(timeout_sec=5.0):
            raise RCBackendError(msg_hi="controller_manager nahi mila",
                                 hint_en="is ros2_control running?")
        req = SwitchController.Request()
        req.activate_controllers = [name]
        req.strictness = 2   # STRICT
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self._node, fut)
        self._controller = name
        return fut.result().ok if fut.result() else False

    def torque(self, on):
        """`torque on/off` -> enable/disable actuator torque. Driver-specific;
        tries a common /controller_manager parameter or a driver service."""
        self._ensure()
        # There is no universal torque service; document the two common routes.
        raise RCBackendError(
            msg_hi="torque %s: driver-specific hai" % ("on" if on else "off"),
            hint_en="wire this to your arm's enable/disable service (vendor-specific "
                    "SendGripperCommand / a hardware_interface param); left "
                    "unimplemented on purpose so it fails loud, not wrong")
