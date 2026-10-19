"""Non-simulated runs: backends are registered, connected and disconnected.

Uses recording fakes in place of the ROS backends, so no ROS is needed.
"""
import pytest

from robot_chalao import backends
from robot_chalao.backends import BACKENDS, Backend, register
from robot_chalao.config import RobotConfig
from robot_chalao.interpreter import Interpreter
from robot_chalao.parser import parse

EVENTS = []


class _Fake(Backend):
    def connect(self, name, config):
        assert isinstance(config, dict)
        EVENTS.append(("connect", self.name, name, config.get("cmd_vel")))

    def disconnect(self):
        EVENTS.append(("disconnect", self.name))

    def base_move(self, distance, unit="meter", backward=False):
        EVENTS.append(("base_move", self.name, distance))

    def battery(self):
        EVENTS.append(("battery", self.name))
        return 80.0


def _fake(nm):
    return type("Fake_" + nm, (_Fake,), {"name": nm})


@pytest.fixture
def fakes():
    saved = dict(BACKENDS)
    for nm in ("raw", "nav2", "perception"):
        register(nm, _fake(nm))
    EVENTS.clear()
    yield
    BACKENDS.clear()
    BACKENDS.update(saved)


def test_real_backends_are_registered():
    for nm in ("moveit", "nav2", "perception", "raw", "control", "gazebo", "mavros"):
        assert nm in backends.BACKENDS


def test_each_backend_connects_before_use_and_all_disconnect(fakes):
    cfg = {"bot": RobotConfig(name="bot", type="mobile", cmd_vel="/bot/cmd_vel",
                              backends={"base": "nav2", "perception": "perception"})}
    prog = parse('robot jodo "bot"\naage chalo 1 meter\n'
                 'maano b = battery kitni hai\nrobot chhodo\n')
    Interpreter(config=cfg, simulate=False).run(prog)
    assert EVENTS[0] == ("connect", "raw", "bot", "/bot/cmd_vel")
    assert EVENTS.index(("connect", "nav2", "bot", "/bot/cmd_vel")) \
        < EVENTS.index(("base_move", "nav2", 1.0))
    assert EVENTS.index(("connect", "perception", "bot", "/bot/cmd_vel")) \
        < EVENTS.index(("battery", "perception"))
    assert {e[1] for e in EVENTS if e[0] == "disconnect"} == {"raw", "nav2", "perception"}


def test_close_disconnects_robots_left_connected(fakes):
    cfg = {"bot": RobotConfig(name="bot", type="mobile",
                              backends={"base": "nav2"})}
    interp = Interpreter(config=cfg, simulate=False)
    interp.run(parse('robot jodo "bot"\naage chalo 1 meter\n'))
    assert not any(e[0] == "disconnect" for e in EVENTS)
    interp.close()
    assert {e[1] for e in EVENTS if e[0] == "disconnect"} == {"raw", "nav2"}
    assert interp.robots == {}
