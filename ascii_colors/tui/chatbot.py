# -*- coding: utf-8 -*-
"""Pluggable, session-aware lollms console with captured logs and completion."""

import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Optional, Protocol, Union, runtime_checkable

from ascii_colors.tui.app import App
from ascii_colors.tui.chat_widgets import RichChatView
from ascii_colors.tui.log_capture import TerminalLogBuffer, attach_log_capture
from ascii_colors.tui.widgets import (
    AsciiArt,
    Box,
    Button,
    Divider,
    HBox,
    Label,
    ListBox,
    MultiLineInput,
    Spinner,
    StatusBar,
    TextInput,
    VBox,
)


@runtime_checkable
class GeneratorProtocol(Protocol):
    def generate(
        self,
        prompt: str,
        history: List[dict],
        on_chunk: Callable[[str], None],
    ) -> str:
        pass


class CallableGenerator:
    """Adapt ``fn(prompt, history[, on_chunk])`` to ``GeneratorProtocol``."""

    def __init__(self, func: Callable[..., str]):
        if not callable(func):
            raise TypeError(
                f"CallableGenerator expects a callable, got {type(func).__name__}"
            )
        self.func = func
        self._streaming = self._takes_on_chunk(func)

    @staticmethod
    def _takes_on_chunk(func: Callable[..., str]) -> bool:
        try:
            import inspect

            return "on_chunk" in inspect.signature(func).parameters
        except (ValueError, TypeError):
            return False

    def generate(
        self,
        prompt: str,
        history: List[dict],
        on_chunk: Callable[[str], None],
    ) -> str:
        if self._streaming:
            result = self.func(prompt, history, on_chunk)
        else:
            result = self.func(prompt, history)
            if result:
                on_chunk(result)
        return result if isinstance(result, str) else ""


class LollmsAdapter:
    """Best-effort adapter for common ``lollms_client`` generate signatures."""

    def __init__(self, client: Any, *, system_prompt: Optional[str] = None):
        self.client = client
        self.system_prompt = system_prompt

    def generate(
        self,
        prompt: str,
        history: List[dict],
        on_chunk: Callable[[str], None],
    ) -> str:
        full_prompt = self._compose_prompt(prompt, history)
        try:
            chunks = self.client.generate(
                prompt=full_prompt,
                system_prompt=self.system_prompt,
                streaming_callback=on_chunk,
            )
        except TypeError:
            chunks = self.client.generate(full_prompt, streaming_callback=on_chunk)

        if isinstance(chunks, str):
            on_chunk(chunks)
            return chunks
        if hasattr(chunks, "__iter__"):
            pieces: List[str] = []
            for piece in chunks:
                if piece is not None:
                    text = str(piece)
                    if text:
                        pieces.append(text)
                        on_chunk(text)
            return "".join(pieces)
        return ""

    def _compose_prompt(self, prompt: str, history: List[dict]) -> str:
        lines = [
            f"{message.get('role', 'user')}: {message.get('content', '') or ''}"
            for message in history
        ]
        lines.append(f"user: {prompt}")
        return "\n".join(lines)


class LollmsDiscussionAdapter:
    """Stream a real ``LollmsDiscussion`` into the console."""

    def __init__(
        self,
        client: Any,
        *,
        workspace_path: Union[str, Path],
        enable_image_generation: bool = True,
        enable_image_editing: bool = True,
        enforce_end_tag: bool = True,
    ):
        from lollms_client.lollms_discussion import LollmsDiscussion

        self.workspace_path = Path(workspace_path).expanduser().resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.enable_image_generation = enable_image_generation
        self.enable_image_editing = enable_image_editing
        self.enforce_end_tag = enforce_end_tag
        self.discussion = LollmsDiscussion(client, workspace_path=self.workspace_path)

    def generate(
        self,
        prompt: str,
        history: List[dict],
        on_chunk: Callable[[str], None],
    ) -> str:
        from lollms_client import MSG_TYPE

        pieces: List[str] = []

        def streaming_callback(chunk, msg_type, metadata) -> bool:
            if msg_type == MSG_TYPE.MSG_TYPE_CHUNK and chunk is not None:
                text = str(chunk)
                if text:
                    pieces.append(text)
                    on_chunk(text)
            return True

        self.discussion.chat(
            prompt,
            streaming_callback=streaming_callback,
            enable_image_generation=self.enable_image_generation,
            enable_image_editing=self.enable_image_editing,
            enforce_end_tag=self.enforce_end_tag,
        )
        return "".join(pieces)


def try_build_lollms_generator(
    model_name: str = "",
    *,
    binding_name: str = "",
    system_prompt: Optional[str] = None,
    client: Any = None,
) -> Optional[GeneratorProtocol]:
    """Return a ``LollmsAdapter`` when a client is supplied or importable."""
    lollms = client
    if lollms is None:
        try:
            from lollms_client import LollmsClient

            lollms = LollmsClient(
                model_name=model_name or None,
                binding_name=binding_name or None,
            )
        except Exception:
            return None
    return LollmsAdapter(lollms, system_prompt=system_prompt)


@dataclass
class ChatSession:
    title: str = "New conversation"
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    messages: List[dict] = field(default_factory=list)
    history: List[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    busy: bool = False


class _ResponsiveChatBody(HBox):
    def __init__(self, sidebar, main):
        super().__init__(gap=1)
        self.sidebar = sidebar
        self.main = main
        self.add(sidebar)
        self.add(main)

    def layout(self, x, y, w, h):
        self.sidebar.visible = w >= 76
        super().layout(x, y, w, h)


class _TerminalLogDialog(Box):
    """Scrollable log viewer with text and severity filtering."""

    def __init__(self, console: "ChatbotApp", query: str = ""):
        super().__init__(
            title=" Terminal logs ",
            border="rounded",
            border_style="bright_magenta",
            padding=1,
            gap=1,
        )
        self.console = console
        self.level = ""
        self.focusable = True
        self.w = 100
        self.h = 24
        self.filter_input = TextInput(value=query)
        self.view = ListBox([])
        self._entries_signature = None
        self.add(Label("[dim]Filter captured ASCIIColors records[/dim]"))
        self.add(self.filter_input)
        self.add(self.view)

        actions = HBox(gap=1)
        actions.add(Button(" All ", on_press=lambda: self.set_level("")))
        actions.add(Button(" Errors ", on_press=lambda: self.set_level("ERROR")))
        actions.add(Button(" Clear ", on_press=self.clear_logs))
        actions.add(Button(" Close ", on_press=self.close))
        actions.min_height = 1
        actions.flex = 0
        self.add(actions)
        self.add(Label("[dim]Type to filter · wheel scrolls · F3 refreshes · Esc closes[/dim]"))
        self.refresh_entries()

    def refresh_entries(self) -> None:
        lines = self.console.log_buffer.lines(
            self.filter_input.value, level=self.level
        ) or ["No matching log entries."]
        signature = (self.filter_input.value, self.level, tuple(lines))
        self.title = f" Terminal logs · {len(self.console.log_buffer)} captured "
        if signature == self._entries_signature:
            return
        self._entries_signature = signature
        self.view.items = lines
        self.view.selected = max(0, len(lines) - 1)
        self.view._sync_scroll()

    def set_level(self, level: str) -> None:
        self.level = level
        self.refresh_entries()

    def clear_logs(self) -> None:
        self.console.log_buffer.clear()
        self.refresh_entries()

    def close(self) -> None:
        if self._app is not None:
            self._app.pop_modal()
            self._app.focus(self.console.input)
            self._app.refresh(clear=True)

    def handle_key(self, key: str) -> bool:
        if key == "ESCAPE":
            self.close()
            return True
        if key == "F3":
            self.refresh_entries()
            return True
        if len(key) == 1 and key.isprintable():
            self.filter_input.value += key
            self.filter_input.cursor = len(self.filter_input.value)
            self.refresh_entries()
            return True
        if key == "BACKSPACE" and self.filter_input.value:
            self.filter_input.value = self.filter_input.value[:-1]
            self.filter_input.cursor = len(self.filter_input.value)
            self.refresh_entries()
            return True
        return self.view.handle_key(key)

    def draw(self, buffer) -> None:
        self.refresh_entries()
        super().draw(buffer)


class ChatbotApp:
    """Full-screen, multi-session chat with streaming and slash completion."""

    def __init__(
        self,
        generator: Union[GeneratorProtocol, Callable[..., str]],
        *,
        title: str = "lollms console",
        system_prompt: Optional[str] = None,
        user_label: str = "You",
        assistant_label: str = "Agent",
        fps: float = 20.0,
        alt_screen: bool = True,
        show_sidebar: bool = True,
        show_welcome: bool = True,
        mouse: bool = True,
        on_settings: Optional[Callable[[], None]] = None,
        log_buffer: Optional[TerminalLogBuffer] = None,
    ):
        self.log_buffer = attach_log_capture(log_buffer)
        if not hasattr(generator, "generate"):
            generator = CallableGenerator(generator)
        self.generator = generator
        self.title = title
        self.system_prompt = system_prompt
        self.fps = fps
        self.alt_screen = alt_screen
        self.mouse = mouse
        self.show_welcome = show_welcome
        self.on_settings = on_settings
        self.sessions: List[ChatSession] = []
        self.active_session: Optional[ChatSession] = None

        self.chat_view = RichChatView(
            user_label=user_label,
            assistant_label=assistant_label,
        )
        self.command_specs = (
            ("/new", "Create a conversation"),
            ("/clear", "Clear the active conversation"),
            ("/title", "Rename: /title NAME"),
            ("/model", "Show the active generator"),
            ("/settings", "Open console settings"),
            ("/logs", "Show captured terminal logs"),
            ("/logs clear", "Clear captured terminal logs"),
            ("/help", "Show keyboard and command help"),
        )
        self.input = MultiLineInput(
            placeholder="Ask anything…  (type / for commands)",
            on_submit=self._on_submit,
            max_height=6,
            completions=self._command_completions,
        )
        self.session_list = ListBox([], on_select=self._select_session_by_title)
        self.header = StatusBar(
            left=f"[bold bright_yellow]◈ {title}[/bold bright_yellow] "
            "[bright_black]· local intelligence, beautifully connected[/bright_black]",
            right=self._generator_name(),
        )
        self.status = StatusBar(
            left="[dim]Enter send · Ctrl+J newline · Ctrl+N new · F1 help · F3 logs[/dim]",
            right="[dim]ready[/dim]",
        )
        self.activity = Spinner(label="[dim]idle[/dim]", interval=0.1)
        self.session_info = Label("", wrap=True)

        conversation_box = Box(
            title=" Transcript ", border="rounded", border_style="bright_cyan", padding=1
        )
        conversation_box.add(self.chat_view)
        prompt_box = Box(
            title=" Compose ", border="rounded", border_style="bright_green", padding=0
        )
        prompt_box.add(self.input)
        prompt_box.min_height = 4
        prompt_box.flex = 0

        activity_row = HBox(gap=1)
        activity_row.add(self.activity)
        activity_row.min_height = 1
        activity_row.flex = 0

        main = VBox(gap=0)
        main.add(conversation_box)
        main.add(prompt_box)
        main.add(activity_row)
        main.add(self.status)

        sidebar = self._build_sidebar()
        body = _ResponsiveChatBody(sidebar, main)
        if not show_sidebar:
            sidebar.visible = False
            body.layout = self._layout_without_sidebar

        self.root = VBox(gap=0)
        self.root.add(self.header)
        self.root.add(body)
        self._app: Optional[App] = None
        self._state_lock = threading.RLock()
        self._worker: Optional[threading.Thread] = None
        self.new_session(activate=True)
        if show_welcome:
            self.active_session.messages.append(
                {
                    "role": "welcome",
                    "content": "Local intelligence. Beautifully connected.",
                }
            )
            self.chat_view._dirty = True

    def _layout_without_sidebar(self, x, y, w, h):
        body = self.root.children[-1]
        body.sidebar.visible = False
        HBox.layout(body, x, y, w, h)

    def _generator_name(self) -> str:
        name = type(self.generator).__name__
        if name == "LollmsAdapter":
            name = type(self.generator.client).__name__
        return f"[bright_black]{name}[/bright_black]"

    def _build_sidebar(self) -> Box:
        logo = AsciiArt(
            ["  ╭─────╮  ", "  │ ● ● │  ", "  ╰─┬┬┬─╯  "],
            style="bold bright_yellow",
            align="center",
            valign="center",
        )
        logo.min_height = 3
        logo.flex = 0
        wordmark = Label(
            "[bold bright_yellow]l o l l m s[/bold bright_yellow]",
            align="center",
        )

        actions = HBox(gap=1)
        actions.add(Button("+ New chat", on_press=self.new_session))
        actions.add(Button("Clear", on_press=self.clear_session))
        actions.add(Button("Help", on_press=self.show_help))
        actions.min_height = 1
        actions.flex = 0

        sidebar = Box(
            title=" Sessions ", border="rounded", border_style="bright_black", padding=1
        )
        sidebar.add(logo)
        sidebar.add(wordmark)
        sidebar.add(Divider(char="·", style="bright_black"))
        sidebar.add(self.session_list)
        sidebar.add(actions)
        sidebar.add(Divider(char="·", style="bright_black"))
        sidebar.add(self.session_info)
        sidebar.min_width = 25
        sidebar.flex = 0
        return sidebar

    def _system_messages(self) -> List[dict]:
        if not self.system_prompt:
            return []
        return [{"role": "system", "content": self.system_prompt}]

    def new_session(self, activate: bool = True) -> ChatSession:
        with self._state_lock:
            session = ChatSession(history=self._system_messages())
            session.messages.extend(self._system_messages())
            self.sessions.append(session)
            if activate:
                self._activate_session(session)
            self._refresh_sessions()
            return session

    def _activate_session(self, session: ChatSession) -> None:
        self.active_session = session
        self.chat_view.messages = session.messages
        self.chat_view._dirty = True
        self.chat_view.scroll_to_end()
        self._update_chrome()

    def _select_session_by_title(self, _title: str, index: int) -> None:
        if 0 <= index < len(self.sessions):
            with self._state_lock:
                self._activate_session(self.sessions[index])

    def _refresh_sessions(self) -> None:
        selected = self.sessions.index(self.active_session) if self.active_session else 0
        self.session_list.items = [
            f"{'●' if session.busy else '○'} {session.title}" for session in self.sessions
        ]
        self.session_list.selected = selected
        self.session_list._sync_scroll()
        self._update_chrome()

    def _update_chrome(self) -> None:
        session = self.active_session
        if session is None:
            return
        messages = sum(
            1 for message in session.messages if message.get("role") != "system"
        )
        self.session_info.text = (
            f"[bright_black]ID[/bright_black] {session.session_id}\n"
            f"[bright_black]Messages[/bright_black] {messages}\n"
            f"[bright_black]State[/bright_black] "
            f"{'streaming' if session.busy else 'ready'}"
        )
        self.activity.label = (
            "[yellow]streaming…[/yellow]" if session.busy else "[dim]ready[/dim]"
        )
        self.status.right = (
            "[yellow]receiving tokens…[/yellow]" if session.busy else "[dim]ready[/dim]"
        )

    def clear_session(self) -> None:
        session = self.active_session
        if session is None or session.busy:
            return
        session.messages[:] = self._system_messages()
        session.history[:] = self._system_messages()
        self.chat_view._dirty = True
        self.chat_view.scroll_to_end()
        self._update_chrome()

    def run(self) -> None:
        app = App(
            fps=self.fps,
            alt_screen=self.alt_screen,
            mouse=self.mouse,
            quit_keys=["ESCAPE"],
        )
        app.set_root(self.root)
        app.bind("CTRL_N", self.new_session)
        app.bind("CTRL_L", self.clear_session)
        app.bind("F1", self.show_help)
        app.bind("F2", self.show_settings)
        app.bind("F3", self.show_logs)
        app.bind("CTRL_Q", app.exit)
        self._app = app
        app.refresh_focus()
        app.focus(self.input)
        try:
            app.run()
        finally:
            self._app = None

    def send(self, text: str) -> None:
        self._on_submit(text)

    def refresh(self, *, clear: bool = False) -> None:
        self._refresh_sessions()
        self.chat_view._dirty = True
        if self._app is not None:
            self._app.refresh(clear=clear)

    def add_tool_event(self, name: str, content: str, status: str = "completed") -> None:
        if self.active_session is None:
            return
        self.active_session.messages.append(
            {
                "role": "tool",
                "content": content,
                "name": name,
                "status": status,
                "timestamp": time.time(),
            }
        )
        self.chat_view._dirty = True
        self.chat_view.scroll_to_end()

    def _handle_command(self, text: str) -> bool:
        if not text.startswith("/"):
            return False
        command, _separator, argument = text.partition(" ")
        command = command.lower()
        if command == "/new":
            self.new_session()
        elif command == "/clear":
            self.clear_session()
        elif command == "/help":
            self.show_help()
        elif command == "/settings":
            self.show_settings()
        elif command == "/logs":
            if argument.strip().lower() == "clear":
                self.log_buffer.clear()
                self._notify("Captured terminal logs cleared.")
            else:
                self.show_logs(argument.strip())
        elif command == "/title":
            title = argument.strip()
            if title and self.active_session is not None:
                self.active_session.title = title[:32]
                self._refresh_sessions()
        elif command == "/model":
            self._notify(f"Generator: `{type(self.generator).__name__}`")
        else:
            self.active_session.messages.append(
                {
                    "role": "error",
                    "content": f"Unknown command `{command}`. Try `/help`.",
                    "timestamp": time.time(),
                }
            )
            self.chat_view._dirty = True
        return True

    def _command_completions(self, value: str, cursor: int):
        line_start = value.rfind("\n", 0, cursor) + 1
        prefix = value[line_start:cursor]
        if not prefix.startswith("/") or any(char.isspace() for char in prefix[1:]):
            return []
        return [
            (prefix, command, description)
            for command, description in self.command_specs
            if command.startswith(prefix.lower())
        ]

    def _notify(self, content: str) -> None:
        if self.active_session is not None:
            self.active_session.messages.append(
                {"role": "system", "content": content, "timestamp": time.time()}
            )
            self.chat_view._dirty = True
            self.chat_view.scroll_to_end()

    def _on_submit(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        self.input.value = ""
        self.input.cursor = 0
        self.input.completion_items = []
        if self._handle_command(text):
            return
        session = self.active_session
        if session is None or session.busy:
            return
        now = time.time()
        session.title = text[:32] if session.title == "New conversation" else session.title
        session.messages.append({"role": "user", "content": text, "timestamp": now})
        session.history.append({"role": "user", "content": text})
        assistant_message = {"role": "assistant", "content": "", "timestamp": now}
        session.messages.append(assistant_message)
        session.busy = True
        session.updated_at = now
        self.chat_view._dirty = True
        self.chat_view.scroll_to_end()
        self._refresh_sessions()
        self._worker = threading.Thread(
            target=self._generate_in_background,
            args=(session, text, assistant_message),
            name=f"chat-{session.session_id}",
            daemon=True,
        )
        self._worker.start()

    def _post_ui(self, callback: Callable, *args) -> None:
        if self._app is not None:
            self._app.post(callback, *args)
        else:
            callback(*args)

    def _generate_in_background(
        self,
        session: ChatSession,
        prompt: str,
        assistant_message: dict,
    ) -> None:
        started = time.monotonic()
        pieces: List[str] = []

        def on_chunk(chunk: str) -> None:
            if chunk:
                pieces.append(chunk)
                self._post_ui(self._append_chunk, session, assistant_message, chunk)

        error: Optional[BaseException] = None
        result = ""
        try:
            result = self.generator.generate(prompt, list(session.history), on_chunk)
        except BaseException as exc:
            error = exc
        self._post_ui(
            self._finish_generation,
            session,
            assistant_message,
            result,
            "".join(pieces),
            error,
            time.monotonic() - started,
        )

    def _append_chunk(self, session: ChatSession, message: dict, chunk: str) -> None:
        message["content"] = (message.get("content") or "") + chunk
        message["tokens"] = max(1, len(message["content"]) // 4)
        session.updated_at = time.time()
        self.chat_view._dirty = True
        if session is self.active_session:
            self.chat_view.scroll_to_end()

    def _finish_generation(
        self,
        session: ChatSession,
        message: dict,
        result: str,
        streamed: str,
        error: Optional[BaseException],
        elapsed: float,
    ) -> None:
        if error is not None:
            message["role"] = "error"
            message["content"] = f"Generation failed: {type(error).__name__}: {error}"
        else:
            final = result or streamed
            if final:
                message["content"] = final
            message["elapsed"] = elapsed
            message["tokens"] = max(1, len(message.get("content", "")) // 4)
            session.history.append({"role": "assistant", "content": final})
        session.busy = False
        session.updated_at = time.time()
        self.chat_view._dirty = True
        self.chat_view.scroll_to_end()
        self._refresh_sessions()
        if self._app is not None:
            self._app.refresh_focus()

    def show_logs(self, query: str = "") -> None:
        if self._app is None:
            self._notify(self.log_buffer.text(query) or "No captured logs.")
            return
        for modal in self._app._modals:
            if isinstance(modal, _TerminalLogDialog):
                modal.refresh_entries()
                return
        self._app.push_modal(_TerminalLogDialog(self, query))
        self._app.refresh(clear=True)

    def show_settings(self) -> None:
        if self.on_settings is not None:
            self.on_settings()
            return
        self._notify(
            "This console has no settings panel. See the lollms demo for an example."
        )

    def show_help(self) -> None:
        content = (
            "Commands: /new · /clear · /title NAME · /model · /settings · /logs · /help\n"
            "Type / for autocomplete · Tab/Right accepts · Up/Down selects\n"
            "Enter sends · Ctrl+J inserts a newline · F3 opens captured logs"
        )
        if self._app is None:
            self._notify(content)
            return
        dialog = Box(
            title=" Console help ", border="rounded", border_style="bright_cyan", padding=1
        )
        for line in (
            "[bold bright_white]Navigation[/bold bright_white]",
            "Click sessions · wheel transcript · Tab / Shift+Tab focus",
            "Ctrl+N new · Ctrl+L clear · F1 help · F2 settings · F3 logs · Ctrl+Q quit",
            "",
            "[bold bright_white]Composer[/bold bright_white]",
            "Enter send · Ctrl+J newline · type / for autocomplete",
            "/new · /clear · /title NAME · /model · /settings · /logs · /help",
        ):
            dialog.add(Label(line))
        dialog.add(Button(" Close ", on_press=self._app.pop_modal))
        dialog.w = 78
        dialog.h = 13
        self._app.push_modal(dialog)