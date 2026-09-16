"""SimBackend: nakli (dry-run) backend jise ROS ki zaroorat nahi.

Har method ek saaf Hinglish line chaapta hai aur ek maqool (plausible) value
lautata hai. Isi se `chalao run file.rc --simulate` bina ROS ke chalta hai --
naye programmer pehle yahan apna program aazma sakte hain.

(The dry-run backend. Every method prints a Hinglish line and returns a
plausible stub, so a `.rc` file runs with zero ROS installed.)
"""
from __future__ import annotations

from ..types import Detection, Image, Joints, PointCloud, Pose, Twist
from .base import Backend


def _say(msg):
    print("[nakli] " + msg)


class SimBackend(Backend):
    """Sab kuch nakli. State thoda-bahut yaad rakhta hai taaki output samajhdaar lage."""

    name = "sim"

    def __init__(self):
        self._pose = Pose(0.4, 0.0, 0.3, 0.0, 3.14, 0.0)
        self._joints = Joints([0.0, -1.57, 0.0, -1.57, 0.0, 0.0],
                              ["j1", "j2", "j3", "j4", "j5", "j6"])
        self._speed = 0.3

    # connection
    def connect(self, name, config):
        _say("robot '%s' se jud gaye" % name)

    def disconnect(self):
        _say("robot chhod diya")

    def set_namespace(self, ns):
        _say("namespace set: %s" % ns)

    def param_set(self, key, value):
        _say("param set: %s = %r" % (key, value))

    def param_get(self, key):
        _say("param get: %s" % key)
        return 0.0

    # arm
    def arm_home(self):
        _say("arm ghar (home) ja raha hai")

    def arm_pose(self, pose):
        _say("pose pe ja raha hai: %r" % pose)
        if isinstance(pose, Pose):
            self._pose = pose

    def arm_joints(self, joints):
        _say("joints pe ja raha hai: %r" % joints)
        if isinstance(joints, Joints):
            self._joints = joints

    def arm_cartesian(self, x, y, z):
        _say("seedha (Cartesian) ja raha hai: (%.3f, %.3f, %.3f)" % (x, y, z))
        self._pose = Pose(x, y, z, self._pose.roll, self._pose.pitch, self._pose.yaw)

    def arm_named(self, name):
        _say("named pose '%s' pe ja raha hai" % name)

    def gripper(self, close):
        _say("gripper " + ("band (pakad raha hai)" if close else "khol raha hai"))

    def set_speed(self, scale):
        self._speed = scale
        _say("speed set: %.2f" % scale)

    def set_planner(self, planner):
        _say("planner set: %s" % planner)

    def add_obstacle(self, name, pose, size):
        _say("rukawat '%s' jodi at %r size %r" % (name, pose, size))

    def remove_obstacle(self, name):
        _say("rukawat '%s' hatai" % name)

    def attach(self, name):
        _say("'%s' attach kiya" % name)

    def detach(self, name):
        _say("'%s' detach kiya" % name)

    def get_pose(self):
        _say("abhi yahan hai: %r" % self._pose)
        return self._pose

    def get_joints(self):
        _say("joints abhi: %r" % self._joints)
        return self._joints

    def ik(self, pose):
        _say("IK nikala for %r" % pose)
        return self._joints

    def fk(self, joints):
        _say("FK nikala for %r" % joints)
        return self._pose

    # base
    def base_move(self, distance, unit="meter", backward=False):
        _say("%s chal raha hai %.2f %s" %
             ("peeche" if backward else "aage", distance, unit))

    def base_rotate(self, angle, unit="degree"):
        _say("ghoom raha hai %.1f %s" % (angle, unit))

    def base_twist(self, v, w):
        _say("twist: v=%.2f w=%.2f" % (v, w))
        return Twist(vx=v, wz=w)

    def base_stop(self):
        _say("base ruk gaya")

    def map_load(self, path):
        _say("map load: %s" % path)

    def localize(self, pose=None):
        _say("localize" + (" at %r" % pose if pose else ""))

    def nav_to(self, x, y, theta):
        _say("nav: (%.2f, %.2f, theta=%.2f) pe ja raha hai" % (x, y, theta))

    def follow_waypoints(self, points):
        _say("waypoints follow: %d points" % len(list(points)))

    def slam_start(self):
        _say("SLAM shuru -- map banaya ja raha hai")

    def map_save(self, name):
        _say("map save: %s" % name)

    def obstacle_near(self):
        _say("obstacle check -- saaf raasta")
        return False

    # perception
    def camera_view(self, topic):
        _say("camera dekh raha hai: %s" % topic)
        return Image(640, 480, "rgb8", None, topic)

    def photo(self, topic, path):
        _say("photo li -> %s" % path)

    def find_object(self, description):
        _say("dhoondh raha hai: '%s' ... mil gaya" % description)
        return Detection(description, Pose(0.5, 0.1, 0.2, 0, 3.14, 0), 0.91)

    def read_lidar(self):
        _say("lidar padha")
        return PointCloud([], "/scan")

    def read_depth(self):
        _say("depth padha")
        return Image(640, 480, "16UC1", None, "/depth")

    def read_imu(self):
        _say("imu padha")
        return {"orientation": Pose(), "angular_velocity": (0, 0, 0)}

    def read_ft(self):
        _say("force/torque padha")
        return {"force": (0.0, 0.0, 0.0), "torque": (0.0, 0.0, 0.0)}

    def battery(self):
        _say("battery: 87%")
        return 87.0

    def find_apriltag(self):
        _say("AprilTag dhoondha -- 1 mila")
        return [Detection("tag_0", Pose(0.6, 0.0, 0.4), 0.98)]

    def find_aruco(self):
        _say("ArUco dhoondha -- 1 mila")
        return [Detection("aruco_5", Pose(0.6, 0.0, 0.4), 0.97)]

    def tf(self, from_frame, to_frame):
        _say("TF %s -> %s" % (from_frame, to_frame))
        return Pose(0.1, 0.0, 0.5)

    # raw
    def subscribe(self, topic, type_name, callback):
        _say("sun raha hai %s (%s)" % (topic, type_name))
        # deliver one fake message so the callback body runs at least once
        callback({"topic": topic, "type": type_name, "data": None})

    def publish(self, topic, value, type_name=None):
        _say("bola %s <- %r" % (topic, value))

    def call_service(self, name, args):
        _say("sewa bulai %s args=%r" % (name, args))
        return {"success": True}

    def send_action(self, name, goal, progress_cb=None):
        _say("action bheja %s goal=%r" % (name, goal))
        if progress_cb:
            for pct in (25, 50, 75, 100):
                progress_cb({"progress": pct})
        return {"result": "done"}

    def list_nodes(self):
        _say("nodes: /sim_node")
        return ["/sim_node"]

    def list_topics(self):
        _say("topics: /cmd_vel, /joint_states, /scan")
        return ["/cmd_vel", "/joint_states", "/scan"]

    def record_start(self, bag):
        _say("record shuru -> %s" % bag)

    def record_stop(self):
        _say("record band")

    def launch(self, package, launch_file):
        _say("launch %s %s" % (package, launch_file))

    def urdf_load(self, path):
        _say("urdf load: %s" % path)

    # control
    def joint_to(self, name, value, unit="rad"):
        _say("joint '%s' ko %.3f %s pe le ja raha hai" % (name, value, unit))

    def controller_switch(self, name):
        _say("controller switch: %s" % name)

    def torque(self, on):
        _say("torque " + ("on" if on else "off"))

    # sim
    def sim_start(self, world):
        _say("Gazebo shuru: world '%s'" % world)

    def spawn(self, model, x, y, z):
        _say("spawn '%s' at (%.2f, %.2f, %.2f)" % (model, x, y, z))

    def sim_stop(self):
        _say("simulation band")

    def rviz_open(self):
        _say("RViz khol diya")

    # safety
    def estop(self):
        _say("!! BAND KARO -- sab kuch ruk gaya (e-stop) !!")

    def set_workspace_limit(self, bounds):
        _say("workspace limit set: %r" % (list(bounds),))

    def set_speed_limit(self, v):
        _say("speed limit set: %.2f" % v)

    # drone
    def takeoff(self):
        _say("udaan bhari -- drone upar")

    def land(self):
        _say("utar raha hai (land)")

    def set_height(self, h, unit="meter"):
        _say("height %.2f %s pe ja raha hai" % (h, unit))
