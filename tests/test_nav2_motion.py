"""Exercise failure paths at the publisher boundary without moving hardware."""
import pytest
from robot_chalao.backends.nav2 import Nav2Backend
from robot_chalao.errors import RCBackendError

@pytest.mark.parametrize('error', [KeyboardInterrupt(), RuntimeError('transport lost')])
def test_interrupted_drive_attempts_stop_and_preserves_error(monkeypatch, error):
    backend = Nav2Backend()
    commands = []
    backend._twist = lambda v, w: commands.append((v, w))
    monkeypatch.setattr('robot_chalao.backends.nav2.time.monotonic', lambda: 0.)
    def fail(_):
        raise error
    monkeypatch.setattr('robot_chalao.backends.nav2.time.sleep', fail)
    with pytest.raises(type(error)) as caught:
        backend._drive_for(.2, 0., 1.)
    assert caught.value is error
    assert commands == [(.2, 0.), (0., 0.)]


def test_failed_stop_does_not_mask_drive_error(monkeypatch):
    backend = Nav2Backend()
    original = RuntimeError('publish failed')
    calls = []
    def publish(v, w):
        calls.append((v, w))
        raise original if v else ValueError('stop failed too')
    backend._twist = publish
    monkeypatch.setattr('robot_chalao.backends.nav2.time.monotonic', lambda: 0.)
    with pytest.raises(RuntimeError) as caught:
        backend._drive_for(.2, 0., 1.)
    assert caught.value is original
    assert calls[-1] == (0., 0.)


def test_disconnect_stops_before_destroy_and_is_idempotent():
    backend = Nav2Backend()
    events = []
    class Node:
        def destroy_node(self): events.append('destroy')
    backend._node = Node()
    backend._pub = object()
    backend._twist = lambda v, w: events.append((v, w))
    backend.disconnect()
    backend.disconnect()
    assert events == [(0., 0.), 'destroy']


@pytest.mark.parametrize('value', [-1., 0., float('nan'), float('inf')])
def test_invalid_speed_limit_keeps_previous_limit(value):
    backend = Nav2Backend()
    with pytest.raises(RCBackendError): backend.set_speed_limit(value)
    assert backend._speed_lin == backend.DEFAULT_LIN


@pytest.mark.parametrize('command', [(float('nan'), 0, 1), (0, float('inf'), 1), (.2, 0, -1), (.2, 0, float('inf'))])
def test_invalid_drive_never_publishes(command):
    backend = Nav2Backend()
    backend._twist = lambda *_: pytest.fail('invalid command was published')
    with pytest.raises(RCBackendError): backend._drive_for(*command)


def test_completed_drive_sends_stop(monkeypatch):
    backend = Nav2Backend()
    commands = []
    ticks = iter([0., 0., 1.])
    backend._twist = lambda v, w: commands.append((v, w))
    monkeypatch.setattr('robot_chalao.backends.nav2.time.monotonic', lambda: next(ticks))
    monkeypatch.setattr('robot_chalao.backends.nav2.time.sleep', lambda _: None)
    backend._drive_for(.2, 0., .5)
    assert commands == [(.2, 0.), (0., 0.)]


def test_timed_drive_waits_for_a_cmd_vel_listener(monkeypatch):
    class Pub:
        n = 0
        def get_subscription_count(self):
            Pub.n += 1
            return 1 if Pub.n > 3 else 0   # controller shows up a bit late
    backend = Nav2Backend()
    backend._pub = Pub()
    sent = []
    backend._twist = lambda v, w: sent.append((v, w, Pub.n))
    backend._drive_for(0.2, 0.0, 0.0)
    assert sent and all(n > 3 for *_, n in sent)


def test_timed_drive_errors_when_nobody_listens():
    class Pub:
        def get_subscription_count(self):
            return 0
    backend = Nav2Backend()
    backend._pub = Pub()
    backend._twist = lambda *_: pytest.fail("must not publish into the void")
    with pytest.raises(RCBackendError):
        backend._wait_for_listener(timeout=0.2)
