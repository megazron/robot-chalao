"""Assemble the GitHub Pages playground into _site/.

  python -m build --wheel        # first: makes dist/robot_chalao-*.whl
  python site/build.py           # then: _site/ is ready to serve
"""
import glob
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")

TITLES = {
    "01_arm_pick_place.rc": "01 · Arm pick & place",
    "02_mobile_patrol.rc": "02 · Mobile patrol",
    "03_camera_pick.rc": "03 · Camera finds, arm picks",
    "04_slam_map.rc": "04 · SLAM map building",
    "05_drone_square.rc": "05 · Drone flies a square",
    "06_short_pick_place.rc": "06 · Short forms (rakh / bol / bas)",
}

CHEATS = [
    ['robot jodo "ur5"', "connect to a robot from chalao.yaml"],
    ["ghar jao", "arm goes to its home pose"],
    ["jao pose(0.4, 0.1, 0.2, 0, 3.14, 0)", "move the gripper to a pose"],
    ["seedha jao (0.4, 0.1, 0.4)", "straight-line Cartesian move"],
    ["pakdo", "close the gripper"],
    ["chhodo", "open the gripper"],
    ["dikhao kahan hai", "print the current end-effector pose"],
    ["aage chalo 1 meter", "drive the base forward"],
    ["ghumo 90 degree", "turn in place"],
    ["yahan jao (2, 1, 0)", "Nav2 goal: x, y, theta"],
    ['maano cup = object dhundo "red cup"', "find an object with the camera"],
    ["agar battery kitni hai < 20 toh\n  bol \"charge chahiye\"\nbas", "if / else on a sensor"],
    ["har i [1, 2, 3] mein karo\n  dikhao i\nkhatam", "for-each loop"],
    ["kaam double(x)\n  wapas x * 2\nkhatam\ndikhao double(21)", "define and call a function"],
    ['frame "camera" "base_link" (0.1, 0, 0.3, 0, 0, 0)', "publish a static TF frame"],
    ['sehat warning "battery kam hai"', "report health on /diagnostics"],
    ['bolo "/chatter" "namaste"', "publish on a raw ROS 2 topic"],
    ["band karo", "emergency stop"],
]


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "examples"))
    for f in ("index.html", "app.js", "worker.js"):
        shutil.copy(os.path.join(ROOT, "site", f), OUT)
    examples = []
    for path in sorted(glob.glob(os.path.join(ROOT, "examples", "*.rc"))):
        name = os.path.basename(path)
        shutil.copy(path, os.path.join(OUT, "examples", name))
        examples.append({"file": name, "title": TITLES.get(name, name)})
    shutil.copy(os.path.join(ROOT, "examples", "chalao.yaml"), os.path.join(OUT, "examples"))
    wheels = sorted(glob.glob(os.path.join(ROOT, "dist", "robot_chalao-*-py3-none-any.whl")))
    if not wheels:
        raise SystemExit("no wheel in dist/ -- run: python -m build --wheel")
    wheel = os.path.basename(wheels[-1])
    shutil.copy(wheels[-1], OUT)
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump({"wheel": wheel, "examples": examples, "cheats": CHEATS}, f, indent=1)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print("built _site/ with", wheel, "and", len(examples), "examples")


if __name__ == "__main__":
    main()
