"""Live ROS 2 check: a real (non-simulated) .rc run publishes what it says.

Skipped unless rclpy is importable (CI runs it in a ros:jazzy container).
A listener node records /cmd_vel, /diagnostics, /tf_static and a raw topic
while `chalao run` drives a mobile robot config for real.
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

rclpy = pytest.importorskip("rclpy")
pytest.importorskip("diagnostic_msgs.msg")
pytest.importorskip("tf2_ros")

ROOT = Path(__file__).resolve().parent.parent

PROGRAM = """\
robot jodo "bot"
aage chalo 0.2 meter
sehat warning "battery kam"
frame "camera" "base_link" (0.1, 0, 0.3, 0, 0, 0)
bolo "/chalao_test" "namaste"
robot chhodo
"""

CONFIG = """\
robots:
  bot:
    type: mobile
    cmd_vel: /cmd_vel
    backends: {base: nav2, perception: perception, raw: raw}
"""


def test_real_run_publishes(tmp_path):
    from diagnostic_msgs.msg import DiagnosticArray
    from geometry_msgs.msg import Twist
    from rclpy.qos import DurabilityPolicy, QoSProfile
    from std_msgs.msg import String
    from tf2_msgs.msg import TFMessage

    (tmp_path / "prog.rc").write_text(PROGRAM)
    (tmp_path / "chalao.yaml").write_text(CONFIG)

    rclpy.init()
    node = rclpy.create_node("chalao_live_listener")
    seen = {"cmd": [], "diag": [], "tf": [], "raw": []}
    node.create_subscription(Twist, "/cmd_vel", seen["cmd"].append, 10)
    node.create_subscription(DiagnosticArray, "/diagnostics", seen["diag"].append, 10)
    node.create_subscription(
        TFMessage, "/tf_static", seen["tf"].append,
        QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL))
    node.create_subscription(String, "/chalao_test", seen["raw"].append, 10)
    stop = threading.Event()

    def spin():
        while not stop.is_set():
            rclpy.spin_once(node, timeout_sec=0.05)

    t = threading.Thread(target=spin, daemon=True)
    t.start()
    time.sleep(1.0)   # discovery
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        r = subprocess.run([sys.executable, "-m", "robot_chalao.cli", "run", "prog.rc"],
                           cwd=tmp_path, env=env, capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 0, r.stderr
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not all(seen.values()):
            time.sleep(0.1)
    finally:
        stop.set()
        t.join()
        node.destroy_node()
        rclpy.shutdown()

    assert any(abs(m.linear.x - 0.2) < 1e-6 for m in seen["cmd"]), "no forward cmd_vel"
    assert seen["cmd"][-1].linear.x == 0.0, "last cmd_vel was not a stop"
    st = seen["diag"][0].status[0]
    assert st.message == "battery kam" and st.level == b"\x01"
    tfs = [tr for m in seen["tf"] for tr in m.transforms]
    assert any(tr.child_frame_id == "camera" and tr.header.frame_id == "base_link"
               and abs(tr.transform.translation.z - 0.3) < 1e-9 for tr in tfs)
    assert seen["raw"][0].data == "namaste"
