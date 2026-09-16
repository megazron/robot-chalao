"""Backend ka base class -- har capability ka contract.

Interpreter `getattr(backend, method)(**args)` bula kar robot ko chalata hai.
Yahan har method define hai; default mein woh "yeh backend yeh kaam nahi karta"
bolta hai, taaki ek asli backend sirf apne kaam override kare. `SimBackend` sab
override karta hai. Method ki capability neeche `CAPABILITY` map mein hai, jise
interpreter routing ke liye use karta hai.

(Base backend. Every method raises a Hinglish 'not supported' error by default;
real backends override their subset. CAPABILITY routes a method to a backend.)
"""
from __future__ import annotations

from ..errors import RCBackendError

# method name -> capability, so the interpreter can pick the right backend.
CAPABILITY = {
    # connection
    "connect": "connection", "disconnect": "connection",
    "set_namespace": "connection", "param_set": "connection",
    "param_get": "connection",
    # arm
    "arm_home": "arm", "arm_pose": "arm", "arm_joints": "arm",
    "arm_cartesian": "arm", "arm_named": "arm", "gripper": "arm",
    "set_speed": "arm", "set_planner": "arm", "add_obstacle": "arm",
    "remove_obstacle": "arm", "attach": "arm", "detach": "arm",
    "get_pose": "arm", "get_joints": "arm", "ik": "arm", "fk": "arm",
    # base
    "base_move": "base", "base_rotate": "base", "base_twist": "base",
    "base_stop": "base", "map_load": "base", "localize": "base",
    "nav_to": "base", "follow_waypoints": "base", "slam_start": "base",
    "map_save": "base", "obstacle_near": "base",
    # perception
    "camera_view": "perception", "photo": "perception",
    "find_object": "perception", "read_lidar": "perception",
    "read_depth": "perception", "read_imu": "perception",
    "read_ft": "perception", "battery": "perception",
    "find_apriltag": "perception", "find_aruco": "perception",
    "tf": "perception",
    # raw
    "subscribe": "raw", "publish": "raw", "call_service": "raw",
    "send_action": "raw", "list_nodes": "raw", "list_topics": "raw",
    "record_start": "raw", "record_stop": "raw", "launch": "raw",
    "urdf_load": "raw",
    # control
    "joint_to": "control", "controller_switch": "control", "torque": "control",
    # sim
    "sim_start": "sim", "spawn": "sim", "sim_stop": "sim", "rviz_open": "sim",
    # safety
    "estop": "safety", "set_workspace_limit": "safety", "set_speed_limit": "safety",
    # drone
    "takeoff": "drone", "land": "drone", "set_height": "drone",
}


class Backend:
    """Sab backends ka base. Naam bhi rakhta hai (`name`)."""

    name = "base"

    def _no(self, method):
        raise RCBackendError(
            msg_hi="yeh backend '%s' nahi karta" % method,
            hint_en="backend %r does not implement %s()" % (self.name, method))

    # connection
    def connect(self, name, config):
        self._no("connect")

    def disconnect(self):
        self._no("disconnect")

    def set_namespace(self, ns):
        self._no("set_namespace")

    def param_set(self, key, value):
        self._no("param_set")

    def param_get(self, key):
        self._no("param_get")

    # arm
    def arm_home(self):
        self._no("arm_home")

    def arm_pose(self, pose):
        self._no("arm_pose")

    def arm_joints(self, joints):
        self._no("arm_joints")

    def arm_cartesian(self, x, y, z):
        self._no("arm_cartesian")

    def arm_named(self, name):
        self._no("arm_named")

    def gripper(self, close):
        self._no("gripper")

    def set_speed(self, scale):
        self._no("set_speed")

    def set_planner(self, planner):
        self._no("set_planner")

    def add_obstacle(self, name, pose, size):
        self._no("add_obstacle")

    def remove_obstacle(self, name):
        self._no("remove_obstacle")

    def attach(self, name):
        self._no("attach")

    def detach(self, name):
        self._no("detach")

    def get_pose(self):
        self._no("get_pose")

    def get_joints(self):
        self._no("get_joints")

    def ik(self, pose):
        self._no("ik")

    def fk(self, joints):
        self._no("fk")

    # base
    def base_move(self, distance, unit="meter", backward=False):
        self._no("base_move")

    def base_rotate(self, angle, unit="degree"):
        self._no("base_rotate")

    def base_twist(self, v, w):
        self._no("base_twist")

    def base_stop(self):
        self._no("base_stop")

    def map_load(self, path):
        self._no("map_load")

    def localize(self, pose=None):
        self._no("localize")

    def nav_to(self, x, y, theta):
        self._no("nav_to")

    def follow_waypoints(self, points):
        self._no("follow_waypoints")

    def slam_start(self):
        self._no("slam_start")

    def map_save(self, name):
        self._no("map_save")

    def obstacle_near(self):
        self._no("obstacle_near")

    # perception
    def camera_view(self, topic):
        self._no("camera_view")

    def photo(self, topic, path):
        self._no("photo")

    def find_object(self, description):
        self._no("find_object")

    def read_lidar(self):
        self._no("read_lidar")

    def read_depth(self):
        self._no("read_depth")

    def read_imu(self):
        self._no("read_imu")

    def read_ft(self):
        self._no("read_ft")

    def battery(self):
        self._no("battery")

    def find_apriltag(self):
        self._no("find_apriltag")

    def find_aruco(self):
        self._no("find_aruco")

    def tf(self, from_frame, to_frame):
        self._no("tf")

    # raw
    def subscribe(self, topic, type_name, callback):
        self._no("subscribe")

    def publish(self, topic, value, type_name=None):
        self._no("publish")

    def call_service(self, name, args):
        self._no("call_service")

    def send_action(self, name, goal, progress_cb=None):
        self._no("send_action")

    def list_nodes(self):
        self._no("list_nodes")

    def list_topics(self):
        self._no("list_topics")

    def record_start(self, bag):
        self._no("record_start")

    def record_stop(self):
        self._no("record_stop")

    def launch(self, package, launch_file):
        self._no("launch")

    def urdf_load(self, path):
        self._no("urdf_load")

    # control
    def joint_to(self, name, value, unit="rad"):
        self._no("joint_to")

    def controller_switch(self, name):
        self._no("controller_switch")

    def torque(self, on):
        self._no("torque")

    # sim
    def sim_start(self, world):
        self._no("sim_start")

    def spawn(self, model, x, y, z):
        self._no("spawn")

    def sim_stop(self):
        self._no("sim_stop")

    def rviz_open(self):
        self._no("rviz_open")

    # safety
    def estop(self):
        self._no("estop")

    def set_workspace_limit(self, bounds):
        self._no("set_workspace_limit")

    def set_speed_limit(self, v):
        self._no("set_speed_limit")

    # drone
    def takeoff(self):
        self._no("takeoff")

    def land(self):
        self._no("land")

    def set_height(self, h, unit="meter"):
        self._no("set_height")
