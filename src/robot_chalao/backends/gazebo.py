"""Gazebo / simulation backend for Robot Chalao.

Hinglish verbs: `simulation shuru gazebo "world"`, `spawn "model" (x,y,z)`,
`simulation band`, `rviz kholo`.

Uses subprocess to drive the Gazebo (Ignition/`gz sim`) and RViz binaries and
the ros_gz spawn entry point, so it needs a working ROS 2 + Gazebo install but
imports fine without one.

ROS packages needed:
    ros-${ROS_DISTRO}-ros-gz  ros-${ROS_DISTRO}-rviz2  gz-sim (Harmonic/Fortress)
Install (Jazzy example):
    sudo apt install ros-jazzy-ros-gz ros-jazzy-rviz2
"""
from __future__ import annotations

import shutil
import subprocess

from robot_chalao.backends.base import Backend
from robot_chalao.errors import RCBackendError, RCRosMissing


def _binary(name, hint):
    path = shutil.which(name)
    if not path:
        raise RCRosMissing(
            msg_hi="'%s' command nahi mila" % name,
            hint_en=hint)
    return path


class GazeboBackend(Backend):
    """Simulation control via subprocess. Implements the [sim] capability."""

    def __init__(self):
        self._cfg = {}
        self._sim_proc = None
        self._rviz_proc = None

    def connect(self, name, config):
        # Nothing to hold open until a sim is started.
        self._cfg = dict(config or {})

    def disconnect(self):
        self.sim_stop()
        if self._rviz_proc is not None:
            try:
                self._rviz_proc.terminate()
            except Exception:  # noqa: BLE001
                pass
            self._rviz_proc = None

    def sim_start(self, world):
        """`simulation shuru gazebo "world"` -> launch gz sim with a world."""
        if self._sim_proc is not None:
            raise RCBackendError(msg_hi="simulation pehle se chal rahi hai",
                                 hint_en="call `simulation band` first")
        gz = _binary("gz", "install Gazebo (gz sim), e.g. sudo apt install gz-harmonic")
        self._sim_proc = subprocess.Popen([gz, "sim", world])
        return True

    def spawn(self, model, x, y, z):
        """`spawn "model" (x,y,z)` -> ros_gz create entry point."""
        _binary("ros2", "source your ROS 2 setup")
        cmd = ["ros2", "run", "ros_gz_sim", "create",
               "-name", model, "-file", model,
               "-x", str(x), "-y", str(y), "-z", str(z)]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            raise RCBackendError(
                msg_hi="'%s' spawn nahi hua" % model,
                hint_en="is ros_gz_sim installed and the model path valid? (%s)"
                        % exc) from exc
        return True

    def sim_stop(self):
        """`simulation band` -> kill the sim process."""
        if self._sim_proc is not None:
            try:
                self._sim_proc.terminate()
                self._sim_proc.wait(timeout=10)
            except Exception:  # noqa: BLE001
                self._sim_proc.kill()
            self._sim_proc = None
        return True

    def rviz_open(self):
        """`rviz kholo` -> launch rviz2."""
        rviz = _binary("rviz2", "install ros-<distro>-rviz2")
        self._rviz_proc = subprocess.Popen([rviz])
        return True
