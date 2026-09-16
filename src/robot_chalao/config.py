"""chalao.yaml padhne wala. Har robot ka config ek `RobotConfig` mein aata hai.

Yeh batata hai: robot ka type, MoveIt planning group, end-effector link,
gripper topic, cmd_vel topic, named poses, speed limit, workspace bounds,
camera topics, aur kaunsi capability kaunse backend se chalti hai.

(Loads chalao.yaml into RobotConfig objects: type, planning group, ee link,
gripper/cmd_vel topics, named poses, limits, cameras, backend routing.)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .errors import RCRuntimeError

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

# sensible default backend per capability when the config does not say
DEFAULT_BACKENDS = {
    "arm": "moveit", "base": "nav2", "perception": "perception",
    "raw": "raw", "control": "control", "sim": "gazebo", "drone": "mavros",
    "connection": "raw", "safety": "raw",
}


@dataclass
class RobotConfig:
    name: str
    type: str = "arm"
    planning_group: str = "manipulator"
    ee_link: str = "tool0"
    base_link: str = "base_link"
    gripper: dict = field(default_factory=dict)
    named_poses: dict = field(default_factory=dict)
    speed_limit: float = 0.5
    workspace: dict = field(default_factory=dict)
    cameras: dict = field(default_factory=dict)
    cmd_vel: str = "/cmd_vel"
    backends: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)  # everything else, kept as-is

    def backend_for(self, capability: str) -> str:
        """Is capability ke liye kaunsa backend? Config -> default."""
        return self.backends.get(capability, DEFAULT_BACKENDS.get(capability, "raw"))


def _to_config(name: str, d: dict) -> RobotConfig:
    known = {
        "type", "planning_group", "ee_link", "base_link", "gripper",
        "named_poses", "speed_limit", "workspace", "cameras", "cmd_vel",
        "backends",
    }
    kwargs = {k: d[k] for k in known if k in d}
    extra = {k: v for k, v in d.items() if k not in known}
    return RobotConfig(name=name, raw=extra, **kwargs)


def load_config(path: str | None) -> dict:
    """chalao.yaml -> {robot_name: RobotConfig}. Missing/blank -> {}.

    `default_robot` config ke andar ho toh usse `__default__` key mein bhi
    daal dete hain taaki interpreter aasani se dhoondh le."""
    if not path or not os.path.exists(path):
        return {}
    if yaml is None:  # pragma: no cover
        raise RCRuntimeError(msg_hi="PyYAML nahi mila",
                             hint_en="pip install pyyaml")
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    robots = {}
    for name, d in (data.get("robots") or {}).items():
        robots[name] = _to_config(name, d or {})
    default = data.get("default_robot")
    if default:
        robots["__default__"] = default
    return robots
