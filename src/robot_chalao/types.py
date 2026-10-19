"""Robot Chalao value types.

Yeh woh cheezein hain jo ek `.rc` program ke andar ghoomti hain: ek Pose, ek
Twist, joint values, camera se aayi Image, aur perception ke Detections. Sab
saade dataclasses hain taaki `dikhao` inhe saaf-saaf chhaap sake.

(These are the runtime values a `.rc` program passes around. Plain dataclasses
so `dikhao` can print them cleanly.)
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pose:
    """Ek jagah aur us jagah par muh kis taraf hai (position + orientation).

    Position metres mein, orientation radians mein (roll, pitch, yaw)."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    def __repr__(self) -> str:
        return ("Pose(x=%.3f, y=%.3f, z=%.3f, roll=%.3f, pitch=%.3f, yaw=%.3f)"
                % (self.x, self.y, self.z, self.roll, self.pitch, self.yaw))


@dataclass
class Twist:
    """Chalne ki speed: seedhi (linear) aur ghoomne wali (angular)."""

    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    wx: float = 0.0
    wy: float = 0.0
    wz: float = 0.0

    def __repr__(self) -> str:
        return ("Twist(v=(%.3f, %.3f, %.3f), w=(%.3f, %.3f, %.3f))"
                % (self.vx, self.vy, self.vz, self.wx, self.wy, self.wz))


@dataclass
class Joints:
    """Har joint ka angle (radians). Naam optional hain."""

    values: list = field(default_factory=list)
    names: list | None = None

    def __repr__(self) -> str:
        vals = ", ".join("%.3f" % v for v in self.values)
        if self.names:
            return "Joints(%s)" % ", ".join(
                "%s=%.3f" % (n, v) for n, v in zip(self.names, self.values))
        return "Joints([%s])" % vals


@dataclass
class Image:
    """Camera se aayi ek tasveer. `data` backend-specific hota hai."""

    width: int = 0
    height: int = 0
    encoding: str = ""
    data: object = None
    topic: str | None = None

    def __repr__(self) -> str:
        return ("Image(%dx%d, encoding=%r, topic=%r)"
                % (self.width, self.height, self.encoding, self.topic))


@dataclass
class PointCloud:
    """3D points ka dher (lidar / depth camera se)."""

    points: object = None
    topic: str | None = None

    def __repr__(self) -> str:
        n = len(self.points) if self.points is not None else 0
        return "PointCloud(%d points, topic=%r)" % (n, self.topic)


@dataclass
class Detection:
    """Kuch dhoondha gaya: uska naam, kahan hai, aur kitna pakka (0..1)."""

    label: str = ""
    pose: Pose = field(default_factory=Pose)
    confidence: float = 0.0

    def __repr__(self) -> str:
        return ("Detection(label=%r, %r, confidence=%.2f)"
                % (self.label, self.pose, self.confidence))


def _shortest_g(d: float) -> str:
    """Shortest %g that round-trips -- the native core's number repr."""
    s = ""
    for p in range(1, 18):
        s = "%.*g" % (p, d)
        if float(s) == d:
            break
    return s


def rc_repr(v) -> str:
    """Value -> text the way the native core prints it (sim lines, lists)."""
    if isinstance(v, bool):
        return "True" if v else "False"
    if v is None:
        return "None"
    if isinstance(v, (int, float)):
        return _shortest_g(float(v))
    if isinstance(v, str):
        return "'%s'" % v
    if isinstance(v, (list, tuple)):
        return "[%s]" % ", ".join(rc_repr(x) for x in v)
    if isinstance(v, dict):
        return "{%s}" % ", ".join("'%s': %s" % (k, rc_repr(x)) for k, x in v.items())
    return repr(v)
