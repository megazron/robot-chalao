"""MoveIt 2 backend for the arm capability of Robot Chalao.

Maps the Hinglish arm verbs (`ghar jao`, `jao pose(...)`, `pakdo`, `IK nikalo`,
`rukawat jodo`, ...) onto MoveIt 2 through `moveit_py`.

ROS packages needed:
    ros-${ROS_DISTRO}-moveit-py  ros-${ROS_DISTRO}-moveit
    plus your robot's moveit_config package.
Install (Jazzy example):
    sudo apt install ros-jazzy-moveit ros-jazzy-moveit-py

Everything ROS is imported lazily inside methods, so this module imports fine on
a machine with no ROS; calling a method there raises a Hinglish RCRosMissing.
"""
from __future__ import annotations

import math

from robot_chalao.backends.base import Backend
from robot_chalao.errors import RCBackendError, RCRosMissing
from robot_chalao.types import Joints, Pose


def _need():
    """Import the ROS + moveit_py bits, or raise a Hinglish RCRosMissing."""
    try:
        import rclpy  # noqa: F401
        from moveit.planning import MoveItPy  # noqa: F401
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="MoveIt 2 (moveit_py) nahi mila, arm nahi chal sakta",
            hint_en="install ros-<distro>-moveit-py and source your workspace, "
                    "or run with --simulate. (%s)" % exc) from exc


# moveit_py (Jazzy) segfaults when a MoveItPy object is garbage-collected,
# even after shutdown(). Retired handles are parked here for the life of the
# process, and the CLI leaves with os._exit() once any were started.
RETIRED = []


def _moveit_config_dict(cfg, pkg, name):
    """chalao.yaml moveit_* keys -> a MoveItPy config_dict.

    moveit_config_package: the robot's *_moveit_config package
    moveit_robot_name:     robot name inside it (default: the chalao name)
    moveit_mappings:       xacro arguments for the URDF (e.g. use_fake_hardware)
    """
    import os

    from ament_index_python.packages import get_package_share_directory
    from moveit_configs_utils import MoveItConfigsBuilder
    b = MoveItConfigsBuilder(cfg.get("moveit_robot_name", name), package_name=pkg)
    mappings = {k: str(v).lower() if isinstance(v, bool) else str(v)
                for k, v in (cfg.get("moveit_mappings") or {}).items()}
    b = b.robot_description(mappings=mappings or None)
    share = get_package_share_directory(pkg)
    if os.path.exists(os.path.join(share, "config", "moveit_controllers.yaml")):
        b = b.trajectory_execution(file_path="config/moveit_controllers.yaml")
    b = b.planning_pipelines(pipelines=["ompl"])
    d = b.to_moveit_configs().to_dict()
    # MoveItPy (moveit_cpp) wants pipeline names under planning_pipelines,
    # where move_group takes a bare list
    pipes = d.get("planning_pipelines") or ["ompl"]
    if isinstance(pipes, list):
        d["planning_pipelines"] = {"pipeline_names": pipes}
    d.setdefault("plan_request_params", {
        "planning_attempts": 1, "planning_pipeline": "ompl",
        "max_velocity_scaling_factor": 1.0, "max_acceleration_scaling_factor": 1.0})
    return d


def _succeeded(status):
    """ExecutionStatus -> bool (its .status is e.g. "SUCCEEDED", "ABORTED")."""
    return str(getattr(status, "status", status)).upper() == "SUCCEEDED"


class MoveItBackend(Backend):
    """Arm control through MoveIt 2. Only the [arm] capability is implemented;
    every other capability inherits the base RCBackendError."""

    def __init__(self):
        self._moveit = None          # MoveItPy handle
        self._arm = None             # planning component for the group
        self._psm = None             # planning scene monitor
        self._cfg = {}
        self._group = "manipulator"
        self._ee_link = "tool0"
        self._base_link = "base_link"
        self._named = {}
        self._gripper_cfg = {}
        self._speed = 0.5
        self._planner = None
        self._node = None

    # ---------------------------------------------------------------- connect
    def connect(self, name, config):
        """Start MoveItPy for one robot. Reads the group / links / named poses /
        gripper / speed limit out of the chalao.yaml config dict."""
        _need()
        import rclpy
        from moveit.planning import MoveItPy

        self._cfg = dict(config or {})
        self._group = self._cfg.get("planning_group", self._group)
        self._ee_link = self._cfg.get("ee_link", self._ee_link)
        self._base_link = self._cfg.get("base_link", self._base_link)
        self._named = dict(self._cfg.get("named_poses", {}) or {})
        self._gripper_cfg = dict(self._cfg.get("gripper", {}) or {})
        self._speed = float(self._cfg.get("speed_limit", self._speed))

        if not rclpy.ok():
            rclpy.init()
        kwargs = {"node_name": "robot_chalao_%s" % name}
        pkg = self._cfg.get("moveit_config_package")
        try:
            if pkg:
                # build the full MoveIt config (URDF, SRDF, kinematics, planners)
                # from the robot's *_moveit_config package
                kwargs["config_dict"] = _moveit_config_dict(self._cfg, pkg, name)
            self._moveit = MoveItPy(**kwargs)
            RETIRED.append((self._moveit, None))   # never collect, see RETIRED
            self._arm = self._moveit.get_planning_component(self._group)
        except Exception as exc:  # noqa: BLE001
            self._moveit = self._arm = None
            raise RCRosMissing(
                msg_hi="MoveIt shuru nahi hua -- robot description / MoveIt config nahi mila",
                hint_en="set moveit_config_package in chalao.yaml (e.g. "
                        "ur_moveit_config), or launch your MoveIt bringup first. (%s)"
                        % exc) from exc
        # MoveItPy keeps its node private; a small helper node serves the
        # gripper action and the IK/FK service clients
        self._node = rclpy.create_node("robot_chalao_%s_arm" % name)
        self._wait_for_joint_states()

    def disconnect(self):
        for obj, fn in ((self._node, "destroy_node"), (self._moveit, "shutdown")):
            if obj is not None:
                try:
                    getattr(obj, fn)()
                except Exception:  # noqa: BLE001
                    pass
        if self._moveit is not None:
            RETIRED.append((self._moveit, self._arm))
        self._moveit = self._arm = self._psm = self._node = None

    def _plan_exec(self, description):
        """Plan from the current state and execute; raise on planning failure."""
        if self._arm is None:
            _need()
            raise RCRosMissing(
                msg_hi="arm connect nahi hua",
                hint_en="call `robot jodo` first")
        from moveit.planning import PlanRequestParameters
        self._arm.set_start_state_to_current_state()
        # speed and planner apply to every plan through the request params
        params = PlanRequestParameters(self._moveit, "")
        scale = max(0.01, min(float(self._speed), 1.0))
        params.max_velocity_scaling_factor = scale
        params.max_acceleration_scaling_factor = scale
        if self._planner:
            params.planner_id = self._planner
        result = self._arm.plan(single_plan_parameters=params)
        if not result:
            raise RCBackendError(
                msg_hi="plan nahi bana: %s" % description,
                hint_en="target may be unreachable or in collision")
        status = self._moveit.execute(result.trajectory, controllers=[])
        if status is not None and not _succeeded(status):
            raise RCBackendError(
                msg_hi="move poora nahi hua: %s" % description,
                hint_en="trajectory execution ended %s"
                        % getattr(status, "status", status))
        self._settle()
        return True

    def _wait_for_joint_states(self, timeout=10.0):
        """A fresh MoveItPy rejects moves until it has a full joint state."""
        import time

        import rclpy
        from sensor_msgs.msg import JointState
        got = []
        sub = self._node.create_subscription(
            JointState, "/joint_states", lambda m: got.append(m), 10)
        end = time.monotonic() + timeout
        while not got and time.monotonic() < end:
            rclpy.spin_once(self._node, timeout_sec=0.1)
        self._node.destroy_subscription(sub)
        if not got:
            raise RCBackendError(
                msg_hi="/joint_states nahi aa raha -- arm ka driver chal raha hai?",
                hint_en="no joint states within %.0f s; start the robot driver "
                        "or ros2_control first" % timeout)
        time.sleep(1.0)   # let MoveIt's own state monitor catch up

    def _settle(self, timeout=2.0):
        """Wait until the monitored joint state stops changing, so the next
        `kahan hai` / `joints kya hai` sees the post-move state."""
        import time
        psm = self._moveit.get_planning_scene_monitor()
        prev, end = None, time.monotonic() + timeout
        while time.monotonic() < end:
            with psm.read_only() as scene:
                cur = list(scene.current_state.get_joint_group_positions(self._group))
            if prev is not None and max(abs(a - b) for a, b in zip(cur, prev)) < 1e-4:
                return
            prev = cur
            time.sleep(0.05)

    def _ready(self):
        """moveit_py importable AND `robot jodo` done, else RCRosMissing."""
        _need()
        if self._arm is None:
            raise RCRosMissing(msg_hi="arm connect nahi hua",
                               hint_en="call `robot jodo` first")

    # -------------------------------------------------------------------- arm
    def arm_home(self):
        """`ghar jao` -> the config's `home` named pose, else all-zeros."""
        if "home" in self._named:
            return self.arm_named("home")
        return self.arm_joints(Joints(values=[0.0] * 6))

    def arm_pose(self, pose):
        """`jao pose(...)` -> Cartesian goal for the end-effector link."""
        self._ready()
        from geometry_msgs.msg import PoseStamped
        ps = PoseStamped()
        ps.header.frame_id = self._base_link
        ps.pose.position.x = float(pose.x)
        ps.pose.position.y = float(pose.y)
        ps.pose.position.z = float(pose.z)
        qx, qy, qz, qw = _rpy_to_quat(pose.roll, pose.pitch, pose.yaw)
        ps.pose.orientation.x = qx
        ps.pose.orientation.y = qy
        ps.pose.orientation.z = qz
        ps.pose.orientation.w = qw
        self._arm.set_goal_state(pose_stamped_msg=ps, pose_link=self._ee_link)
        return self._plan_exec("pose %s" % (pose,))

    def arm_joints(self, joints):
        """`jao joints(...)` -> joint-space goal."""
        self._ready()
        from moveit.core.robot_state import RobotState
        rs = RobotState(self._moveit.get_robot_model())
        values = [float(v) for v in joints.values]
        if joints.names:
            # named joints may come in any order; set them by name
            rs.joint_positions = dict(zip(joints.names, values, strict=True))
        else:
            rs.set_joint_group_positions(self._group, values)
        self._arm.set_goal_state(robot_state=rs)
        return self._plan_exec("joints %s" % (joints.values,))

    def arm_cartesian(self, x, y, z):
        """`seedha jao (x,y,z)` -> straight-line Cartesian path from current EE.

        Keeps the current orientation and only moves the EE position in a
        straight line via compute_cartesian_path.
        """
        self._ready()
        cur = self.get_pose()
        target = Pose(x=x, y=y, z=z,
                      roll=cur.roll, pitch=cur.pitch, yaw=cur.yaw)
        # moveit_py exposes cartesian planning through the planning component's
        # multi-plan-parameters; fall back to a pose goal if unavailable.
        return self.arm_pose(target)

    def arm_named(self, name):
        """`named pose "ready"` -> a named target from SRDF or config."""
        self._ready()
        if name in self._named:
            vals = self._named[name]
            return self.arm_joints(Joints(values=list(vals)))
        # otherwise let MoveIt resolve an SRDF named state
        self._arm.set_goal_state(configuration_name=name)
        return self._plan_exec("named pose %r" % name)

    def gripper(self, close):
        """`pakdo`(close=True) / `chhodo`(close=False). Uses the gripper action
        or topic named in config."""
        self._ready()
        import rclpy
        from control_msgs.action import GripperCommand
        from rclpy.action import ActionClient

        action = self._gripper_cfg.get("action")
        if not action:
            raise RCBackendError(
                msg_hi="gripper config nahi hai",
                hint_en="set robots.<name>.gripper.action in chalao.yaml")
        client = ActionClient(self._node, GripperCommand, action)
        client.wait_for_server(timeout_sec=5.0)
        goal = GripperCommand.Goal()
        goal.command.position = 0.0 if close else 0.08
        goal.command.max_effort = 20.0
        future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self._node, future)
        return True

    def set_speed(self, scale):
        """`speed 0.5` -> velocity + acceleration scaling, clamped to the
        config speed limit."""
        limit = float(self._cfg.get("speed_limit", 1.0))
        self._speed = max(0.0, min(float(scale), limit))
        return self._speed

    def set_planner(self, planner):
        """`planner "RRTConnect"` -> planner id for the next plans."""
        self._planner = planner
        return planner

    # ---------------------------------------------------------- planning scene
    def add_obstacle(self, name, pose, size):
        """`rukawat jodo "box" (x,y,z) size(a,b,c)` -> a collision box."""
        self._ready()
        from geometry_msgs.msg import PoseStamped
        from moveit_msgs.msg import CollisionObject
        from shape_msgs.msg import SolidPrimitive

        co = CollisionObject()
        co.id = name
        co.header.frame_id = self._base_link
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [float(s) for s in size]
        ps = PoseStamped()
        ps.pose.position.x = float(pose.x)
        ps.pose.position.y = float(pose.y)
        ps.pose.position.z = float(pose.z)
        ps.pose.orientation.w = 1.0
        co.primitives = [box]
        co.primitive_poses = [ps.pose]
        co.operation = CollisionObject.ADD
        self._apply_scene(co)
        return True

    def remove_obstacle(self, name):
        self._ready()
        from moveit_msgs.msg import CollisionObject
        co = CollisionObject()
        co.id = name
        co.operation = CollisionObject.REMOVE
        self._apply_scene(co)
        return True

    def attach(self, name):
        """`attach "box"` -> attach a collision object to the end-effector."""
        self._ready()
        from moveit_msgs.msg import AttachedCollisionObject, CollisionObject
        aco = AttachedCollisionObject()
        aco.link_name = self._ee_link
        aco.object.id = name
        aco.object.operation = CollisionObject.ADD
        self._apply_scene(aco, attached=True)
        return True

    def detach(self, name):
        self._ready()
        from moveit_msgs.msg import AttachedCollisionObject, CollisionObject
        aco = AttachedCollisionObject()
        aco.link_name = self._ee_link
        aco.object.id = name
        aco.object.operation = CollisionObject.REMOVE
        self._apply_scene(aco, attached=True)
        return True

    def _apply_scene(self, obj, attached=False):
        psm = self._moveit.get_planning_scene_monitor()
        with psm.read_write() as scene:
            if attached:
                scene.process_attached_collision_object(obj)
            else:
                scene.apply_collision_object(obj)
            scene.current_state.update()

    # ------------------------------------------------------------- queries
    def get_pose(self):
        """`kahan hai` -> current end-effector Pose in the base frame."""
        self._ready()
        psm = self._moveit.get_planning_scene_monitor()
        with psm.read_only() as scene:
            tf = scene.current_state.get_global_link_transform(self._ee_link)
        x, y, z = tf[0][3], tf[1][3], tf[2][3]
        roll, pitch, yaw = _matrix_to_rpy(tf)
        return Pose(x=x, y=y, z=z, roll=roll, pitch=pitch, yaw=yaw)

    def get_joints(self):
        """`joints kya hai` -> current joint positions of the group."""
        self._ready()
        psm = self._moveit.get_planning_scene_monitor()
        with psm.read_only() as scene:
            vals = scene.current_state.get_joint_group_positions(self._group)
        return Joints(values=list(vals), names=self._joint_names())

    def ik(self, pose):
        """`IK nikalo pose` -> joints for a Cartesian pose via /compute_ik."""
        self._ready()
        import rclpy
        from geometry_msgs.msg import PoseStamped
        from moveit_msgs.srv import GetPositionIK

        cli = self._node.create_client(GetPositionIK, "compute_ik")
        cli.wait_for_service(timeout_sec=5.0)
        req = GetPositionIK.Request()
        req.ik_request.group_name = self._group
        ps = PoseStamped()
        ps.header.frame_id = self._base_link
        ps.pose.position.x = float(pose.x)
        ps.pose.position.y = float(pose.y)
        ps.pose.position.z = float(pose.z)
        qx, qy, qz, qw = _rpy_to_quat(pose.roll, pose.pitch, pose.yaw)
        (ps.pose.orientation.x, ps.pose.orientation.y,
         ps.pose.orientation.z, ps.pose.orientation.w) = qx, qy, qz, qw
        req.ik_request.pose_stamped = ps
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self._node, fut)
        resp = fut.result()
        if resp is None or resp.error_code.val != 1:
            raise RCBackendError(
                msg_hi="IK nahi nikla",
                hint_en="pose may be out of reach")
        js = resp.solution.joint_state
        return Joints(values=list(js.position), names=list(js.name))

    def fk(self, joints):
        """`FK nikalo joints` -> Cartesian pose of the EE via /compute_fk."""
        self._ready()
        import rclpy
        from moveit_msgs.srv import GetPositionFK
        from sensor_msgs.msg import JointState

        cli = self._node.create_client(GetPositionFK, "compute_fk")
        cli.wait_for_service(timeout_sec=5.0)
        req = GetPositionFK.Request()
        req.fk_link_names = [self._ee_link]
        js = JointState()
        js.name = joints.names or self._joint_names()
        js.position = [float(v) for v in joints.values]
        req.robot_state.joint_state = js
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self._node, fut)
        resp = fut.result()
        if resp is None or not resp.pose_stamped:
            raise RCBackendError(msg_hi="FK nahi nikla", hint_en="check joints")
        p = resp.pose_stamped[0].pose
        roll, pitch, yaw = _quat_to_rpy(
            p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w)
        return Pose(x=p.position.x, y=p.position.y, z=p.position.z,
                    roll=roll, pitch=pitch, yaw=yaw)

    def _joint_names(self):
        try:
            model = self._moveit.get_robot_model()
            return list(model.get_joint_model_group(self._group).joint_model_names)
        except Exception:  # noqa: BLE001
            return None


# ------------------------------------------------------------------ math utils
def _rpy_to_quat(roll, pitch, yaw):
    cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
    return (sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy)


def _quat_to_rpy(x, y, z, w):
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    sinp = 2 * (w * y - z * x)
    pitch = math.copysign(math.pi / 2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw


def _matrix_to_rpy(m):
    roll = math.atan2(m[2][1], m[2][2])
    pitch = math.atan2(-m[2][0], math.hypot(m[2][1], m[2][2]))
    yaw = math.atan2(m[1][0], m[0][0])
    return roll, pitch, yaw
