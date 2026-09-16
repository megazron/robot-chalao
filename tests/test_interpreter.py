import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from robot_chalao.errors import RCError, RCNameError    # noqa: E402
from robot_chalao.interpreter import Interpreter         # noqa: E402
from robot_chalao.parser import parse                    # noqa: E402


def run(src, capsys=None):
    interp = Interpreter(simulate=True)
    interp.run(parse(src + "\n"))
    return interp


def out(capsys):
    return capsys.readouterr().out


def test_arithmetic_and_print(capsys):
    run("dikhao 2 + 3 * 4")
    assert out(capsys).strip() == "14"


def test_variables(capsys):
    run("maano x = 5\nmaano y = x + 1\ndikhao y")
    assert out(capsys).strip() == "6"


def test_bool_display(capsys):
    run("dikhao sach, jhooth")
    assert out(capsys).strip() == "sach jhooth"


def test_if_true_branch(capsys):
    run("agar 5 > 3 toh\n dikhao \"haan\"\nwarna\n dikhao \"nahi\"\nkhatam")
    assert out(capsys).strip() == "haan"


def test_while_loop(capsys):
    run("maano i = 0\njab tak i < 3 karo\n dikhao i\n maano i = i + 1\nkhatam")
    assert out(capsys).strip().split("\n") == ["0", "1", "2"]


def test_foreach(capsys):
    run("har n [1, 2, 3] mein karo\n dikhao n\nkhatam")
    assert out(capsys).strip().split("\n") == ["1", "2", "3"]


def test_function_and_return(capsys):
    run("kaam sq(x)\n wapas x * x\nkhatam\ndikhao sq(4)")
    assert out(capsys).strip() == "16"


def test_recursion(capsys):
    src = ("kaam fac(n)\n agar n <= 1 toh\n  wapas 1\n khatam\n"
           " wapas n * fac(n - 1)\nkhatam\ndikhao fac(5)")
    run(src)
    assert out(capsys).strip() == "120"


def test_try_except_catches(capsys):
    run("koshish\n dikhao 1 / 0\ngalti hone par e\n dikhao \"bach gaye\"\nkhatam")
    assert "bach gaye" in out(capsys)


def test_undefined_name():
    with pytest.raises(RCNameError):
        run("dikhao nahibana")


def test_pose_member_access(capsys):
    run("maano p = pose(0.4, 0.1, 0.2)\ndikhao p.x")
    assert out(capsys).strip() == "0.4"


def test_full_program_simulate(capsys):
    run('robot jodo "ur5"\nghar jao\npakdo\nchhodo\nrobot chhodo')
    o = out(capsys)
    assert "se jud gaye" in o and "ghar" in o and "gripper" in o


def test_estop_runs(capsys):
    run('robot jodo "ur5"\nband karo')
    assert "BAND KARO" in out(capsys)


def test_timer_bounded_ticks(capsys):
    run("har 0.1 second mein\n dikhao \"tick\"\nkhatam")
    assert out(capsys).count("tick") == 3  # SIM_TIMER_TICKS


def test_subscribe_runs_callback_once(capsys):
    run('sun "/scan" LaserScan mein msg\n dikhao "aaya"\nkhatam')
    assert "aaya" in out(capsys)


def test_query_assignment(capsys):
    run('robot jodo "ur5"\nmaano b = battery kitni hai\ndikhao b')
    assert "87" in out(capsys)


def test_break_in_loop(capsys):
    run("maano i = 0\njab tak i < 10 karo\n agar i == 2 toh\n  ruko_loop\n khatam\n"
        " dikhao i\n maano i = i + 1\nkhatam")
    assert out(capsys).strip().split("\n") == ["0", "1"]


def test_real_mode_requires_connect():
    interp = Interpreter(simulate=False)
    with pytest.raises(RCError):
        interp.run(parse("ghar jao\n"))
