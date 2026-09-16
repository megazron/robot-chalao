import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from robot_chalao import ast_nodes as A               # noqa: E402
from robot_chalao.errors import RCParseError           # noqa: E402
from robot_chalao.parser import parse                  # noqa: E402


def only(src):
    prog = parse(src + "\n")
    assert len(prog.body) == 1
    return prog.body[0]


def test_let():
    n = only("maano x = 5")
    assert isinstance(n, A.Let) and n.name == "x"


def test_if_else():
    n = only("agar x > 3 toh\n dikhao 1\nwarna\n dikhao 2\nkhatam")
    assert isinstance(n, A.If) and n.then and n.orelse


def test_while():
    n = only("jab tak x < 5 karo\n dikhao x\nkhatam")
    assert isinstance(n, A.While)


def test_foreach():
    n = only("har cup cups mein karo\n dikhao cup\nkhatam")
    assert isinstance(n, A.ForEach) and n.var == "cup"


def test_func_and_return():
    n = only("kaam add(a, b)\n wapas a + b\nkhatam")
    assert isinstance(n, A.FuncDef) and n.params == ["a", "b"]


def test_try():
    n = only("koshish\n dikhao 1\ngalti hone par e\n dikhao e\nkhatam")
    assert isinstance(n, A.Try) and n.err_name == "e"


def test_timer_vs_foreach_disambiguation():
    t = only("har 0.1 second mein\n dikhao 1\nkhatam")
    assert isinstance(t, A.Timer) and t.unit == "second"


def _cmd(src):
    n = only(src)
    return n


def test_arm_pose_command():
    n = _cmd("jao pick")
    assert isinstance(n, A.RobotCommand) and n.method == "arm_pose"
    assert "pose" in n.args


def test_arm_home_command():
    assert _cmd("ghar jao").method == "arm_home"


def test_gripper_close_open():
    assert _cmd("pakdo").args["close"].value is True
    assert _cmd("chhodo").args["close"].value is False


def test_cartesian_tuple():
    n = _cmd("seedha jao (0.4, 0.1, 0.4)")
    assert n.method == "arm_cartesian" and set(n.args) == {"x", "y", "z"}


def test_base_move_and_rotate():
    assert _cmd("aage chalo 1 meter").method == "base_move"
    assert _cmd("peeche chalo 2 meter").args["backward"].value is True
    assert _cmd("ghumo 90 degree").method == "base_rotate"


def test_nav_to():
    n = _cmd("yahan jao (1, 2, 0)")
    assert n.method == "nav_to" and set(n.args) == {"x", "y", "theta"}


def test_find_object():
    n = _cmd('object dhundo "red cup"')
    assert n.method == "find_object" and n.args["description"].value == "red cup"


def test_tf_query():
    n = _cmd('TF pucho "base" se "tool"')
    assert n.method == "tf"


def test_publish():
    n = _cmd('bolo "/t" 5')
    assert n.method == "publish" and n.args["topic"].value == "/t"


def test_connect_disconnect():
    assert _cmd('robot jodo "ur5"').method == "connect"
    assert _cmd("robot chhodo").method == "disconnect"


def test_selector():
    n = _cmd('robot "left_arm" jao pick')
    assert n.method == "arm_pose" and n.selector == "left_arm"


def test_estop_and_drone():
    assert _cmd("band karo").method == "estop"
    assert _cmd("udaan bharo").method == "takeoff"
    assert _cmd("height 2 meter").method == "set_height"


def test_joint_to_control():
    n = _cmd('joint "j1" ko 1.2 rad pe le jao')
    assert n.method == "joint_to" and n.args["unit"].value == "rad"


def test_typed_ctors_in_expr():
    n = only("maano p = pose(1, 2, 3)")
    assert isinstance(n.expr, A.TypedCtor) and n.expr.kind == "pose"


def test_multiline_list():
    n = only("maano p = [\n pose(1,1,0),\n pose(2,2,0)\n]")
    assert isinstance(n.expr, A.ListLit) and len(n.expr.items) == 2


def test_missing_khatam_is_hinglish():
    with pytest.raises(RCParseError) as e:
        parse("agar x toh\n dikhao 1\n")
    assert "khatam" in str(e.value)


def test_query_as_expression():
    n = only("maano p = kahan hai")
    assert isinstance(n.expr, A.RobotCommand) and n.expr.method == "get_pose"
