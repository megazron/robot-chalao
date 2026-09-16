"""`chalao doctor`: aapka ROS 2 setup theek hai ya nahi, Hinglish mein bataata hai.

Yeh check karta hai ki rclpy, moveit_py, nav2, tf2, aur OpenCV import hote hain
ya nahi, aur har ek ke liye ek chhota fix bhi deta hai. Yeh hamesha exit 0 karta
hai -- yeh ek report hai, koi galti nahi.

(Prints a Hinglish health report of the ROS 2 / MoveIt / Nav2 / OpenCV install
with a one-line fix each. Always exits 0.)
"""
from __future__ import annotations

import importlib

_CHECKS = [
    ("rclpy", "ROS 2 core", "source /opt/ros/<distro>/setup.bash"),
    ("moveit", "MoveIt 2 (moveit_py)", "sudo apt install ros-<distro>-moveit-py"),
    ("nav2_simple_commander", "Nav2 commander",
     "sudo apt install ros-<distro>-nav2-simple-commander"),
    ("tf2_ros", "TF2", "sudo apt install ros-<distro>-tf2-ros"),
    ("cv2", "OpenCV (perception)", "pip install opencv-python"),
    ("yaml", "PyYAML (config)", "pip install pyyaml"),
]


def _has(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def run_doctor():
    """Report chhaapta hai, return exit code (hamesha 0)."""
    print("Robot Chalao doctor -- aapka setup check kar raha hoon\n")
    ok = 0
    for mod, label, fix in _CHECKS:
        if _has(mod):
            print("  [theek]  %-22s mil gaya" % label)
            ok += 1
        else:
            print("  [gayab]  %-22s nahi mila  ->  %s" % (label, fix))
    print()
    total = len(_CHECKS)
    if ok == total:
        print("Sab kuch mil gaya (%d/%d). Robot chalane ke liye taiyaar!" % (ok, total))
    elif ok == 0:
        print("Kuch bhi nahi mila (0/%d). Koi baat nahi -- "
              "'chalao run file.rc --simulate' bina ROS ke chalta hai." % total)
    else:
        print("%d/%d mila. Jo gayab hai woh upar diye fix se laga sakte ho; "
              "ya --simulate use karo." % (ok, total))
    return 0
