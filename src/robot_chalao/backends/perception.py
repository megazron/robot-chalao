"""Perception backend for Robot Chalao.

Maps the Hinglish sensing verbs (`camera dekho`, `photo lo`, `object dhundo`,
`lidar padho`, `AprilTag dhundo`, `TF pucho`, ...) onto ROS 2 sensor topics,
OpenCV, an optional object detector, and tf2.

ROS / pip packages needed:
    ros-${ROS_DISTRO}-cv-bridge  ros-${ROS_DISTRO}-tf2-ros
    python3-opencv  (cv2, includes aruco);  pip install ultralytics  (optional YOLO)
    ros-${ROS_DISTRO}-apriltag-ros  (optional, for AprilTag)
Install (Jazzy example):
    sudo apt install ros-jazzy-cv-bridge ros-jazzy-tf2-ros python3-opencv

All heavy imports are lazy, so the module imports fine without ROS.

Object detection is a PLUGIN HOOK: set `PerceptionBackend.detector` to any
callable `(bgr_image, description) -> Detection|None` to swap in your own model.
The default tries YOLO (ultralytics) and falls back to an OpenCV colour blob.
"""
from __future__ import annotations

import time

from robot_chalao.backends.base import Backend
from robot_chalao.errors import RCBackendError, RCRosMissing
from robot_chalao.types import Detection, Image, Pose


def _need_rclpy():
    try:
        import rclpy  # noqa: F401
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="ROS 2 (rclpy) nahi mila, sensor nahi padh sakte",
            hint_en="source your ROS 2 setup, or run with --simulate. (%s)"
                    % exc) from exc


def _need_cv():
    try:
        import cv2  # noqa: F401
        return
    except Exception as exc:  # noqa: BLE001
        raise RCRosMissing(
            msg_hi="OpenCV (cv2) nahi mila",
            hint_en="sudo apt install python3-opencv. (%s)" % exc) from exc


class PerceptionBackend(Backend):
    """Sensors and perception. Only the [perception] capability is implemented."""

    #: plugin hook: (bgr, description) -> Detection|None. Overridable per instance.
    detector = None

    def __init__(self):
        self._cfg = {}
        self._node = None
        self._cameras = {}
        self._tf_buffer = None
        self._tf_listener = None

    def connect(self, name, config):
        _need_rclpy()
        import rclpy
        from rclpy.node import Node
        self._cfg = dict(config or {})
        self._cameras = dict(self._cfg.get("cameras", {}) or {})
        if not rclpy.ok():
            rclpy.init()
        self._node = Node("robot_chalao_perception_%s" % name)

    def disconnect(self):
        import contextlib
        with contextlib.suppress(Exception):
            if self._node is not None:
                self._node.destroy_node()
        self._node = self._tf_buffer = self._tf_listener = None

    def _ensure(self):
        if self._node is None:
            _need_rclpy()
            raise RCRosMissing(msg_hi="perception connect nahi hua",
                               hint_en="call `robot jodo` first")

    # ---------------------------------------------------------- one message
    def _one(self, msg_type, topic, timeout=5.0):
        """Block for a single message on `topic`, or raise."""
        self._ensure()
        import rclpy
        box = {}

        def _cb(m):
            box["msg"] = m
        sub = self._node.create_subscription(msg_type, topic, _cb, 10)
        end = time.monotonic() + timeout
        while "msg" not in box and time.monotonic() < end:
            rclpy.spin_once(self._node, timeout_sec=0.1)
        self._node.destroy_subscription(sub)
        if "msg" not in box:
            raise RCBackendError(
                msg_hi="%s pe koi message nahi aaya" % topic,
                hint_en="is the sensor publishing? check `ros2 topic hz`")
        return box["msg"]

    def _resolve_topic(self, topic):
        # allow a camera nickname from config, else the raw topic string
        return self._cameras.get(topic, topic)

    def _to_cv(self, img_msg):
        _need_cv()
        from cv_bridge import CvBridge
        return CvBridge().imgmsg_to_cv2(img_msg, desired_encoding="bgr8")

    # ---------------------------------------------------------- camera
    def camera_view(self, topic):
        """`camera dekho "/topic"` -> one Image."""
        self._ensure()
        from sensor_msgs.msg import Image as RosImage
        t = self._resolve_topic(topic)
        m = self._one(RosImage, t)
        return Image(width=m.width, height=m.height, encoding=m.encoding,
                     data=bytes(m.data), topic=t)

    def photo(self, topic, path):
        """`photo lo "file.png"` -> grab a frame and write it to disk."""
        self._ensure()
        _need_cv()
        import cv2
        from sensor_msgs.msg import Image as RosImage
        t = self._resolve_topic(topic)
        m = self._one(RosImage, t)
        cv2.imwrite(path, self._to_cv(m))
        return path

    def find_object(self, description):
        """`object dhundo "red cup"` -> a Detection via the detector plugin."""
        self._ensure()
        _need_cv()
        from sensor_msgs.msg import Image as RosImage
        topic = self._resolve_topic(self._cameras.get("main", "/camera/image_raw"))
        m = self._one(RosImage, topic)
        bgr = self._to_cv(m)
        det = (self.detector or _default_detector)(bgr, description)
        if det is None:
            raise RCBackendError(
                msg_hi="'%s' nahi mila frame mein" % description,
                hint_en="object not detected; try another view or a real model")
        return det

    # ---------------------------------------------------------- raw sensors
    def read_lidar(self):
        """`lidar padho` -> one LaserScan (returned as-is)."""
        self._ensure()
        from sensor_msgs.msg import LaserScan
        return self._one(LaserScan, "/scan")

    def read_depth(self):
        """`depth padho` -> one depth Image."""
        self._ensure()
        from sensor_msgs.msg import Image as RosImage
        m = self._one(RosImage, self._resolve_topic(
            self._cameras.get("depth", "/camera/depth/image_rect_raw")))
        return Image(width=m.width, height=m.height, encoding=m.encoding,
                     data=bytes(m.data), topic="depth")

    def read_imu(self):
        """`imu padho` -> one Imu."""
        self._ensure()
        from sensor_msgs.msg import Imu
        return self._one(Imu, "/imu")

    def read_ft(self):
        """`dabav padho` -> one WrenchStamped (force/torque)."""
        self._ensure()
        from geometry_msgs.msg import WrenchStamped
        return self._one(WrenchStamped, "/ft_sensor")

    def battery(self):
        """`battery kitni hai` -> percentage (0-100)."""
        self._ensure()
        from sensor_msgs.msg import BatteryState
        m = self._one(BatteryState, "/battery_state")
        pct = m.percentage
        return pct * 100.0 if pct is not None and pct <= 1.0 else float(pct)

    # ---------------------------------------------------------- markers
    def find_apriltag(self):
        """`AprilTag dhundo` -> list of Detection from an AprilTag topic."""
        self._ensure()
        try:
            from apriltag_msgs.msg import AprilTagDetectionArray
        except Exception as exc:  # noqa: BLE001
            raise RCRosMissing(
                msg_hi="apriltag_msgs nahi mila",
                hint_en="sudo apt install ros-<distro>-apriltag-msgs. (%s)"
                        % exc) from exc
        arr = self._one(AprilTagDetectionArray, "/detections")
        out = []
        for d in arr.detections:
            c = d.centre if hasattr(d, "centre") else None
            pose = Pose(x=c.x if c else 0.0, y=c.y if c else 0.0)
            out.append(Detection(label="tag_%s" % d.id, pose=pose, confidence=1.0))
        return out

    def find_aruco(self):
        """`ArUco dhundo` -> list of Detection using cv2.aruco on one frame."""
        self._ensure()
        _need_cv()
        import cv2
        from sensor_msgs.msg import Image as RosImage
        m = self._one(RosImage, self._resolve_topic(
            self._cameras.get("main", "/camera/image_raw")))
        gray = cv2.cvtColor(self._to_cv(m), cv2.COLOR_BGR2GRAY)
        aruco = cv2.aruco
        adict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        corners, ids, _ = aruco.ArucoDetector(adict).detectMarkers(gray)
        out = []
        if ids is not None:
            for i, cid in enumerate(ids.flatten()):
                c = corners[i][0].mean(axis=0)
                out.append(Detection(label="aruco_%d" % int(cid),
                                     pose=Pose(x=float(c[0]), y=float(c[1])),
                                     confidence=1.0))
        return out

    # ---------------------------------------------------------- tf
    def tf(self, from_frame, to_frame):
        """`TF pucho "base" se "tool"` -> the transform as a Pose."""
        self._ensure()
        import rclpy
        try:
            from tf2_ros import Buffer, TransformListener
        except Exception as exc:  # noqa: BLE001
            raise RCRosMissing(msg_hi="tf2_ros nahi mila",
                               hint_en="install ros-<distro>-tf2-ros. (%s)"
                                       % exc) from exc
        if self._tf_buffer is None:
            self._tf_buffer = Buffer()
            self._tf_listener = TransformListener(self._tf_buffer, self._node)
        end = time.monotonic() + 3.0
        while time.monotonic() < end:
            rclpy.spin_once(self._node, timeout_sec=0.1)
            try:
                from rclpy.time import Time
                t = self._tf_buffer.lookup_transform(
                    from_frame, to_frame, Time())
                tr, rot = t.transform.translation, t.transform.rotation
                import math
                roll = math.atan2(2 * (rot.w * rot.x + rot.y * rot.z),
                                  1 - 2 * (rot.x ** 2 + rot.y ** 2))
                pitch = math.asin(max(-1, min(1, 2 * (rot.w * rot.y - rot.z * rot.x))))
                yaw = math.atan2(2 * (rot.w * rot.z + rot.x * rot.y),
                                 1 - 2 * (rot.y ** 2 + rot.z ** 2))
                return Pose(x=tr.x, y=tr.y, z=tr.z, roll=roll, pitch=pitch, yaw=yaw)
            except Exception:  # noqa: BLE001
                continue
        raise RCBackendError(
            msg_hi="TF '%s' se '%s' nahi mila" % (from_frame, to_frame),
            hint_en="is the transform being broadcast?")


def _default_detector(bgr, description):
    """Fallback object detector. Tries YOLO (ultralytics) first, then an OpenCV
    colour blob keyed off a colour word in the description. Returns image-frame
    pixel coordinates in the Pose (x,y); a real deployment supplies a plugin
    that returns metric 3-D poses."""
    try:
        from ultralytics import YOLO
        import numpy as np  # noqa: F401
        model = getattr(_default_detector, "_yolo", None)
        if model is None:
            model = YOLO("yolov8n.pt")
            _default_detector._yolo = model
        res = model(bgr, verbose=False)[0]
        want = description.lower().split()[-1]
        for b in res.boxes:
            label = res.names[int(b.cls)].lower()
            if want in label:
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                return Detection(label=label,
                                 pose=Pose(x=(x1 + x2) / 2, y=(y1 + y2) / 2),
                                 confidence=float(b.conf))
    except Exception:  # noqa: BLE001
        pass
    return _colour_blob(bgr, description)


def _colour_blob(bgr, description):
    import cv2
    import numpy as np
    ranges = {
        "red": [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (180, 255, 255))],
        "green": [((36, 80, 70), (86, 255, 255))],
        "blue": [((94, 80, 70), (126, 255, 255))],
        "yellow": [((20, 100, 100), (33, 255, 255))],
    }
    colour = next((c for c in ranges if c in description.lower()), None)
    if colour is None:
        return None
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = None
    for lo, hi in ranges[colour]:
        m = cv2.inRange(hsv, np.array(lo), np.array(hi))
        mask = m if mask is None else (mask | m)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    mmt = cv2.moments(c)
    if mmt["m00"] == 0:
        return None
    cx, cy = mmt["m10"] / mmt["m00"], mmt["m01"] / mmt["m00"]
    return Detection(label=description, pose=Pose(x=cx, y=cy), confidence=0.6)
