import asyncio
import json

from channels.mqtt import MqttChannel
from logger.logger import Logger
from state import StateManager


class FakeQueue:
    def __init__(self, items):
        self._items = list(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._items:
            raise StopAsyncIteration
        return self._items.pop(0)


class FakeClient:
    def __init__(self, queue_items=None):
        self.queue = FakeQueue(queue_items or [])
        self.published = []
        self.subscribed = []
        self.up = asyncio.Event()

    async def publish(self, topic, msg, retain, qos):
        self.published.append((topic, msg, retain, qos))

    async def subscribe(self, topic, qos):
        self.subscribed.append((topic, qos))


def make_channel(data):
    state = StateManager(data)
    logger = Logger(state)
    return MqttChannel(state, logger), state


def test_filter_set_patch_keeps_allowed_and_drops_unknown():
    channel, _ = make_channel({})
    patch = {
        "mode": {"current": "rainbow", "on": False, "unknown": 1},
        "leds": {"count": 100, "pin": 5},
        "wifi": {"password": "secret"},
    }

    allowed = channel._filter_set_patch(patch)

    assert allowed == {"mode": {"current": "rainbow", "on": False}, "leds": {"count": 100}}


def test_filter_set_patch_keeps_segmenting():
    channel, _ = make_channel({})
    patch = {"leds": {"count": 100, "segmenting": {"enabled": True, "length": 5}, "pin": 5}}

    allowed = channel._filter_set_patch(patch)

    assert allowed == {"leds": {"count": 100, "segmenting": {"enabled": True, "length": 5}}}


def test_handle_messages_applies_allowed_patch():
    channel, state = make_channel({"mode": {"current": "static", "on": True}})
    channel._client = FakeClient(
        queue_items=[
            (b"controller/led/1/state/update", json.dumps({"mode": {"on": False}}).encode(), False),
        ]
    )

    asyncio.run(channel._handle_messages())

    assert state.mode.on is False
    assert state.mode.current == "static"


def test_handle_messages_applies_partial_segmenting_patch_preserving_sibling_key():
    channel, state = make_channel(
        {"leds": {"count": 100, "segmenting": {"enabled": True, "length": 10}}}
    )
    channel._client = FakeClient(
        queue_items=[
            (
                b"controller/led/1/state/update",
                json.dumps({"leds": {"segmenting": {"length": 5}}}).encode(),
                False,
            ),
        ]
    )

    asyncio.run(channel._handle_messages())

    assert state.get("leds", "segmenting") == {"enabled": True, "length": 5}


def test_handle_messages_ignores_invalid_json():
    channel, state = make_channel({"mode": {"current": "static"}})
    channel._client = FakeClient(queue_items=[(b"controller/led/1/state/update", b"not json", False)])

    asyncio.run(channel._handle_messages())

    assert state.mode.current == "static"


def test_handle_messages_ignores_disallowed_keys():
    channel, state = make_channel({"mode": {"current": "static"}})
    channel._client = FakeClient(
        queue_items=[
            (b"controller/led/1/state/update", json.dumps({"wifi": {"password": "hacked"}}).encode(), False),
        ]
    )

    asyncio.run(channel._handle_messages())

    assert "wifi" not in state.data()


def test_handle_messages_ignores_own_device_payload():
    channel, state = make_channel({"mode": {"current": "static", "on": True}})
    channel._client = FakeClient(
        queue_items=[
            (
                b"controller/led/1/state",
                json.dumps({"device": state.device_id, "mode": {"on": False}}).encode(),
                True,
            ),
        ]
    )

    asyncio.run(channel._handle_messages())

    assert state.mode.on is True


def test_handle_up_subscribes_to_state_update_and_announces_online():
    channel, _ = make_channel({})
    channel._base = "mytopic"
    channel._running = True
    client = FakeClient()
    channel._client = client

    async def run_briefly():
        client.up.set()
        task = asyncio.create_task(channel._handle_up())
        await asyncio.sleep(0.01)
        channel._running = False
        client.up.set()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_briefly())

    assert ("mytopic/state/update", 0) in client.subscribed
    assert ("mytopic/state/online", "online", True, 0) in client.published


def test_publish_state_sends_full_mode_and_leds_on_change():
    channel, state = make_channel(
        {
            "mode": {"current": "static", "on": True},
            "leds": {"count": 10, "pin": 0, "segmenting": {"enabled": False, "length": 5}},
        }
    )
    channel._base = "controller/led/1"
    channel._running = True
    client = FakeClient()
    channel._client = client

    async def run_briefly():
        channel._changed.set()
        task = asyncio.create_task(channel._publish_state())
        await asyncio.sleep(0.01)
        channel._running = False
        channel._changed.set()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_briefly())

    assert len(client.published) == 1
    topic, payload, retain, qos = client.published[0]
    assert topic == "controller/led/1/state/full"
    assert retain is True
    assert qos == 0
    data = json.loads(payload)
    assert data["mode"] == {"current": "static", "on": True}
    assert data["leds"] == {"count": 10, "segmenting": {"enabled": False, "length": 5}}
    assert data["device"] == state.device_id


def test_single_topic_joins_update_and_full():
    channel, _ = make_channel({})
    channel._base = "mytopic"
    channel._single = True

    assert channel._update_topic() == "mytopic/state"
    assert channel._full_topic() == "mytopic/state"


def test_single_topic_subscribe_and_publish_use_joined_topic():
    channel, _ = make_channel({"mode": {"current": "static", "on": True}})
    channel._base = "mytopic"
    channel._single = True
    channel._running = True
    client = FakeClient()
    channel._client = client

    async def run_briefly():
        client.up.set()
        channel._changed.set()
        tasks = [
            asyncio.create_task(channel._handle_up()),
            asyncio.create_task(channel._publish_state()),
        ]
        await asyncio.sleep(0.01)
        channel._running = False
        client.up.set()
        channel._changed.set()
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass

    asyncio.run(run_briefly())

    assert ("mytopic/state", 0) in client.subscribed
    assert any(topic == "mytopic/state" for topic, _, _, _ in client.published)
