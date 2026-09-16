import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from robot_chalao.transpiler import transpile          # noqa: E402

EX = os.path.join(os.path.dirname(__file__), "..", "examples")


def _compiles(src):
    py = transpile(src)
    compile(py, "<gen>", "exec")
    return py


def test_simple_program_compiles():
    _compiles('robot jodo "ur5"\nghar jao\nrobot chhodo\n')


def test_control_flow_translates():
    py = _compiles("agar 1 > 0 toh\n dikhao 1\nwarna\n dikhao 2\nkhatam\n")
    assert "if (1 > 0):" in py and "else:" in py


def test_foreach_translates():
    py = _compiles("har n [1, 2] mein karo\n dikhao n\nkhatam\n")
    assert "for n in [1, 2]:" in py


def test_function_translates():
    py = _compiles("kaam add(a, b)\n wapas a + b\nkhatam\n")
    assert "def add(a, b):" in py


def test_robot_command_becomes_bot_call():
    py = _compiles("jao pose(0.4, 0.1, 0.2)\n")
    assert "bot.arm_pose(" in py and "Pose(0.4, 0.1, 0.2)" in py


def test_and_or_not_translate():
    py = _compiles("agar sach aur nahi jhooth toh\n dikhao 1\nkhatam\n")
    assert " and " in py and "not " in py


def test_header_mentions_ros_libs():
    py = transpile("ghar jao\n")
    assert "rclpy" in py and "moveit" in py and "nav2" in py


def test_all_examples_transpile_and_compile():
    for fn in sorted(os.listdir(EX)):
        if fn.endswith(".rc"):
            with open(os.path.join(EX, fn)) as f:
                _compiles(f.read())
