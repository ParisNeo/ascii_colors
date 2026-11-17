
# -*- coding: utf-8 -*-
"""Smoke test for ascii_colors.tui.chatbot — no TUI loop, pure logic."""

import sys
import threading
import time

sys.path.insert(0, ".")

from ascii_colors.tui import (
    CallableGenerator,
    ChatbotApp,
    GeneratorProtocol,
    LollmsAdapter,
    try_build_lollms_generator,
)


def streamed_generator(prompt, history, on_chunk):
    for token in ("hello", " ", "from", " ", "the", " ", "bot"):
        on_chunk(token)
    return "hello from the bot"


def plain_generator(prompt, history):
    return f"echo: {prompt}"


def test_callable_streaming():
    gen = CallableGenerator(streamed_generator)
    chunks = []
    result = gen.generate("hi", [], chunks.append)
    assert chunks == ["hello", " ", "from", " ", "the", " ", "bot"], chunks
    assert result == "hello from the bot", result
    print("[OK] CallableGenerator streaming path")


def test_callable_plain():
    gen = CallableGenerator(plain_generator)
    chunks = []
    result = gen.generate("ping", [], chunks.append)
    assert result == "echo: ping", result
    assert chunks == ["echo: ping"], chunks
    print("[OK] CallableGenerator plain path")


class FakeLollmsClient:
    def generate(self, prompt, system_prompt=None, streaming_callback=None):
        for piece in ("A", "B", "C"):
            if streaming_callback:
                streaming_callback(piece)
        return "ABC"


def test_lollms_adapter():
    adapter = LollmsAdapter(FakeLollmsClient(), system_prompt="be brief")
    chunks = []
    result = adapter.generate("question", [{"role": "user", "content": "earlier"}], chunks.append)
    assert result == "ABC", result
    assert chunks == ["A", "B", "C"], chunks
    print("[OK] LollmsAdapter forwards chunks")


def test_try_build_falls_back_to_none():
    gen = try_build_lollms_generator(binding_name="nonexistent-binding")
    if gen is not None:
        print("[SKIP] lollms_client is installed; fallback not exercised")
    else:
        print("[OK] try_build_lollms_generator returned None without lollms_client")


def test_chatbot_app_constructs():
    app = ChatbotApp(
        CallableGenerator(streamed_generator),
        title="Smoke",
        system_prompt="You are a test.",
        user_label="Me",
        assistant_label="Bot",
    )
    assert app.generator is not None
    assert app.input.on_submit is not None
    assert isinstance(app._history, list)
    assert app._history[0]["role"] == "system"
    print("[OK] ChatbotApp constructed with system prompt")


def test_chatbot_app_roundtrip():
    """Simulate a submit + background generation without an App loop."""
    app = ChatbotApp(CallableGenerator(streamed_generator), title="Roundtrip")
    app.send("Hello there")

    # Wait for the worker to finish (it streams tokens with no delay).
    deadline = time.time() + 5.0
    while app._busy and time.time() < deadline:
        time.sleep(0.02)

    assert not app._busy, "worker did not finish"
    roles = [m["role"] for m in app.chat_view.messages]
    assert roles == ["user", "assistant"], roles
    assert app.chat_view.messages[-1]["content"] == "hello from the bot", app.chat_view.messages[-1]
    assert app._history[-1]["role"] == "assistant"
    assert app._history[-1]["content"] == "hello from the bot"
    print("[OK] ChatbotApp roundtrip (submit -> stream -> history)")


def test_chatbot_app_busy_guard():
    slow_start = threading.Event()
    slow_release = threading.Event()

    def slow_generator(prompt, history, on_chunk):
        slow_start.set()
        slow_release.wait(timeout=5.0)
        on_chunk("done")
        return "done"

    app = ChatbotApp(CallableGenerator(slow_generator), title="Busy")
    app.send("first")
    assert slow_start.wait(timeout=2.0), "slow generator did not start"
    # Second send while busy must be ignored.
    app.send("second")
    # Only one user message should exist.
    user_count = sum(1 for m in app.chat_view.messages if m["role"] == "user")
    assert user_count == 1, user_count
    slow_release.set()
    deadline = time.time() + 3.0
    while app._busy and time.time() < deadline:
        time.sleep(0.02)
    print("[OK] ChatbotApp busy guard ignores concurrent submits")


def test_error_reporting():
    def broken(prompt, history, on_chunk):
        raise RuntimeError("boom")

    app = ChatbotApp(CallableGenerator(broken), title="Err")
    app.send("anything")
    deadline = time.time() + 3.0
    while app._busy and time.time() < deadline:
        time.sleep(0.02)
    error_msgs = [m for m in app.chat_view.messages if m["role"] == "error"]
    assert error_msgs, app.chat_view.messages
    assert "boom" in error_msgs[0]["content"]
    print("[OK] ChatbotApp surfaces generator errors as error messages")


def main():
    test_callable_streaming()
    test_callable_plain()
    test_lollms_adapter()
    test_try_build_falls_back_to_none()
    test_chatbot_app_constructs()
    test_chatbot_app_roundtrip()
    test_chatbot_app_busy_guard()
    test_error_reporting()
    print("\nALL CHATBOT SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()