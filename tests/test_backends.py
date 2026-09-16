"""Tests for the real ROS 2 backends, all runnable with ZERO ROS installed.

Every ROS-facing method must be (a) present with the contract signature, (b)
raise a Hinglish RCRosMissing when called without ROS rather than a raw
ImportError, and (c) leave capabilities it does not implement inheriting the
base RCBackendError. The backend classes must also import on a ROS-free machine.

The suite import-guards `backends.base`: if the core team's base.py is not in
place yet, the whole module skips with a clear reason and passes once it lands.
"""
import inspect
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# The backends subclass Backend; if base.py is not written yet, skip cleanly.
base = pytest.importorskip(
    "robot_chalao.backends.base",
    reason="core team's backends/base.py not present yet; skips until it lands")
Backend = base.Backend

from robot_chalao.errors import RCBackendError, RCRosMissing  # noqa: E402
from robot_chalao.types import Joints, Pose                    # noqa: E402

from robot_chalao.backends.control import ControlBackend       # noqa: E402
from robot_chalao.backends.gazebo import GazeboBackend         # noqa: E402
from robot_chalao.backends.mavros import MavrosBackend         # noqa: E402
from robot_chalao.backends.moveit import MoveItBackend         # noqa: E402
from robot_chalao.backends.nav2 import Nav2Backend             # noqa: E402
from robot_chalao.backends.perception import PerceptionBackend  # noqa: E402
from robot_chalao.backends.raw import RawBackend               # noqa: E402

ALL = [MoveItBackend, Nav2Backend, PerceptionBackend, RawBackend,
       ControlBackend, GazeboBackend, MavrosBackend]

# capability -> (backend class, list of method names it must implement)
CAP_METHODS = {
    "arm": (MoveItBackend, [
        "arm_home", "arm_pose", "arm_joints", "arm_cartesian", "arm_named",
        "gripper", "set_speed", "set_planner", "add_obstacle", "remove_obstacle",
        "attach", "detach", "get_pose", "get_joints", "ik", "fk"]),
    "base": (Nav2Backend, [
        "base_move", "base_rotate", "base_twist", "base_stop", "map_load",
        "localize", "nav_to", "follow_waypoints", "slam_start", "map_save",
        "obstacle_near"]),
    "perception": (PerceptionBackend, [
        "camera_view", "photo", "find_object", "read_lidar", "read_depth",
        "read_imu", "read_ft", "battery", "find_apriltag", "find_aruco", "tf"]),
    "raw": (RawBackend, [
        "subscribe", "publish", "call_service", "send_action", "list_nodes",
        "list_topics", "record_start", "record_stop", "launch", "urdf_load"]),
    "control": (ControlBackend, ["joint_to", "controller_switch", "torque"]),
    "sim": (GazeboBackend, ["sim_start", "spawn", "sim_stop", "rviz_open"]),
    "drone": (MavrosBackend, ["takeoff", "land", "set_height"]),
}


@pytest.mark.parametrize("cls", ALL)
def test_is_backend_subclass(cls):
    assert issubclass(cls, Backend)
    assert isinstance(cls(), Backend)


@pytest.mark.parametrize("cap,pair", list(CAP_METHODS.items()))
def test_capability_methods_present(cap, pair):
    cls, methods = pair
    obj = cls()
    for m in methods:
        assert hasattr(obj, m), "%s missing %s" % (cls.__name__, m)
        assert callable(getattr(obj, m))


def _defined_here(cls, method):
    """True if `method` is overridden on `cls` itself, not inherited from base."""
    return method in cls.__dict__


@pytest.mark.parametrize("cap,pair", list(CAP_METHODS.items()))
def test_backend_overrides_only_its_capability(cap, pair):
    cls, methods = pair
    # Every method the backend claims for its capability is defined on the class
    # (or, for mavros, on the class too since it borrows base verbs).
    for m in methods:
        assert _defined_here(cls, m) or m in ("set_speed_limit",), \
            "%s.%s should be overridden, not inherited" % (cls.__name__, m)


def test_unimplemented_capability_raises_base_error():
    # Nav2 does not do arm work; calling an arm method hits the base default.
    nav = Nav2Backend()
    with pytest.raises(RCBackendError):
        nav.arm_home()
    # ...and MoveIt does not navigate.
    arm = MoveItBackend()
    with pytest.raises(RCBackendError):
        arm.nav_to(1.0, 2.0, 0.0)


def test_calling_without_ros_raises_ros_missing_not_importerror():
    # With no ROS on this machine, each ROS-facing call must surface as the
    # Hinglish RCRosMissing, never a bare ImportError/ModuleNotFoundError.
    cases = [
        (MoveItBackend(), "arm_pose", (Pose(x=0.4, y=0.0, z=0.3),)),
        (MoveItBackend(), "get_pose", ()),
        (Nav2Backend(), "nav_to", (1.0, 2.0, 0.0)),
        (PerceptionBackend(), "read_lidar", ()),
        (PerceptionBackend(), "tf", ("base", "tool")),
        (RawBackend(), "list_nodes", ()),
        (ControlBackend(), "joint_to", ("j1", 1.2)),
        (MavrosBackend(), "takeoff", ()),
    ]
    for obj, method, args in cases:
        with pytest.raises(RCRosMissing):
            getattr(obj, method)(*args)


def test_ros_missing_message_is_hinglish():
    try:
        Nav2Backend().nav_to(0.0, 0.0, 0.0)
    except RCRosMissing as e:
        assert str(e).startswith("Bhai,")
        assert e.hint_en   # every ROS-missing error carries an English hint
    else:
        pytest.fail("expected RCRosMissing")


def test_connect_reads_config():
    # connect() should ingest config without ROS being required to construct;
    # since connect() itself needs ROS, assert it fails Hinglish, not raw.
    with pytest.raises(RCRosMissing):
        MoveItBackend().connect("ur5", {"planning_group": "manipulator"})


def test_moveit_gripper_close_flag_signature():
    # `pakdo`/`chhodo` map to gripper(close: bool); the signature must accept it.
    sig = inspect.signature(MoveItBackend.gripper)
    assert "close" in sig.parameters


def test_base_move_has_unit_and_backward():
    sig = inspect.signature(Nav2Backend.base_move)
    assert sig.parameters["unit"].default == "meter"
    assert sig.parameters["backward"].default is False


def test_gazebo_is_subprocess_based_no_ros_import_at_module_load():
    # Gazebo backend construction must not need ROS at all.
    g = GazeboBackend()
    g.connect("sim", {})   # no-op, no ROS
    assert isinstance(g, Backend)


def test_perception_detector_is_a_plugin_hook():
    # The object detector is swappable per instance.
    p = PerceptionBackend()
    assert hasattr(PerceptionBackend, "detector")
    sentinel = lambda bgr, desc: None   # noqa: E731
    p.detector = sentinel
    assert p.detector is sentinel


def test_raw_type_resolver_rejects_bad_type():
    from robot_chalao.backends.raw import _import_type
    with pytest.raises(RCBackendError):
        _import_type("not_a_valid_type_string_with_no_slash")


def test_mavros_also_offers_base_verbs():
    # A drone can be driven with the mobile-base words.
    m = MavrosBackend()
    for verb in ("base_move", "base_rotate", "base_twist"):
        assert _defined_here(MavrosBackend, verb)
