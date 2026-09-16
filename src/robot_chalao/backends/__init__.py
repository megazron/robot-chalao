"""Backend registry.

`register(name, cls)` naam se ek backend class jodta hai; `get_backend(name)`
ek naya instance banata hai. `sim` hamesha available hai. Asli backends
(moveit/nav2/perception/raw/control/gazebo/mavros) lazily import hote hain --
agar unka module abhi likha nahi gaya ya ROS nahi hai, tab bhi yeh package
import ho jaata hai; woh backend method CALL par hi RCRosMissing uthata hai.

(Name -> backend class registry. `sim` is always present. Real backends import
lazily so a missing module never breaks import; they raise only when called.)
"""
from __future__ import annotations

from ..errors import RCBackendError
from .base import CAPABILITY, Backend
from .sim import SimBackend

BACKENDS: dict[str, type] = {}


def register(name: str, cls: type) -> None:
    """Ek backend class ko naam se register karo."""
    BACKENDS[name] = cls


def get_backend(name: str) -> Backend:
    """Naam se ek naya backend instance banao. Anjaan naam -> Hinglish error."""
    if name not in BACKENDS:
        raise RCBackendError(
            msg_hi="'%s' naam ka koi backend nahi mila" % name,
            hint_en="unknown backend %r; known: %s"
                    % (name, ", ".join(sorted(BACKENDS))))
    return BACKENDS[name]()


register("sim", SimBackend)

# Real backends live in sibling modules written by the backends team. Import
# them best-effort; each registers itself. A missing file must NOT break us.
for _mod in ("moveit", "nav2", "perception", "raw", "control", "gazebo", "mavros"):
    try:  # pragma: no cover - depends on which backend files exist
        __import__("robot_chalao.backends." + _mod)
    except Exception:  # noqa: BLE001 - absence is expected and fine
        pass

__all__ = ["BACKENDS", "CAPABILITY", "Backend", "SimBackend",
           "register", "get_backend"]
