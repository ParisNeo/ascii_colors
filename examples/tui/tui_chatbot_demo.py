# -*- coding: utf-8 -*-
"""lollms console — streaming chat with an interactive settings panel.

Offline showcase (no optional dependency required)::

    python examples/tui/tui_chatbot_demo.py

Real lollms discussion using your existing lollms environment/config::

    pip install lollms_client
    python examples/tui/tui_chatbot_demo.py --online

``--binding`` and ``--model`` are accepted for CLI compatibility; connection
creation itself is delegated to ``get_client_from_env(create_tti=True)``.
Press **F2** or enter **/settings** to configure the workspace and discussion
features. Applying settings in offline mode connects to lollms on demand.
"""

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ascii_colors.tui import (
    App,
    Box,
    Button,
    ChatbotApp,
    Checkbox,
    Divider,
    HBox,
    Label,
    LollmsDiscussionAdapter,
    TextInput,
    VBox,
    attach_log_capture,
)


@dataclass
class DemoSettings:
    workspace: str = str(Path.cwd() / "workspaces")
    image_generation: bool = True
    image_editing: bool = True
    enforce_end_tag: bool = True


class SettingsDialog(Box):
    """A small, fully keyboard- and mouse-accessible settings form."""

    def __init__(self, demo: "ConsoleDemo"):
        super().__init__(
            title=" lollms settings ",
            border="rounded",
            border_style="bright_yellow",
            padding=1,
        )
        self.demo = demo
        self.focusable = True
        self.w = 72
        self.h = 17

        self.workspace = TextInput(value=demo.settings.workspace)
        self.images = Checkbox(
            "Enable image generation", checked=demo.settings.image_generation
        )
        self.editing = Checkbox(
            "Enable image editing", checked=demo.settings.image_editing
        )
        self.end_tag = Checkbox(
            "Enforce discussion end tag", checked=demo.settings.enforce_end_tag
        )
        self.feedback = Label("", wrap=True)

        self.add(
            Label(
                "[bright_black]Connection: lollms_client environment / saved configuration[/bright_black]"
            )
        )
        self.add(Divider(char="·", style="bright_black"))
        self.add(Label("[bold bright_white]Workspace folder[/bold bright_white]"))
        self.add(self.workspace)
        self.add(self.images)
        self.add(self.editing)
        self.add(self.end_tag)
        self.add(self.feedback)

        actions = HBox(gap=2)
        actions.add(Button(" Apply ", on_press=self.apply))
        actions.add(Button(" Cancel ", on_press=self.close))
        actions.min_height = 1
        actions.flex = 0
        self.add(actions)
        self.add(Label("[dim]Tab moves · Space toggles · Enter activates · Esc cancels[/dim]"))

    def open(self) -> None:
        app = self.demo.console._app
        if app is None:
            return
        app.push_modal(self)
        app.focus(self.workspace)

    def close(self) -> None:
        app = self.demo.console._app
        if app is not None:
            app.pop_modal()
            app.focus(self.demo.console.input)

    def apply(self) -> None:
        workspace = self.workspace.value.strip()
        if not workspace:
            self.feedback.text = "[red]Workspace path cannot be empty.[/red]"
            return
        settings = DemoSettings(
            workspace=workspace,
            image_generation=self.images.checked,
            image_editing=self.editing.checked,
            enforce_end_tag=self.end_tag.checked,
        )
        try:
            self.demo.apply_settings(settings)
        except Exception as exc:
            self.feedback.text = (
                f"[red]Could not connect:[/red] {type(exc).__name__}: {exc}"
            )
            return
        self.close()
        self.demo.console.status.right = "[green]settings applied[/green]"
        self.demo.console.refresh(clear=True)

    def handle_key(self, key: str) -> bool:
        if key == "ESCAPE":
            self.close()
            return True
        return False


class ConsoleDemo:
    """Own runtime settings and construct real lollms discussions on demand."""

    def __init__(self, settings: DemoSettings):
        self.settings = settings
        self.online = False
        self.console: Optional[ChatbotApp] = None

    @staticmethod
    def build_discussion(settings: DemoSettings) -> LollmsDiscussionAdapter:
        try:
            from lollms_client.lollms_config_cli_env import get_client_from_env
        except ImportError as exc:
            raise RuntimeError(
                "lollms_client is not installed. Run: pip install lollms_client"
            ) from exc

        client = get_client_from_env(create_tti=True)
        return LollmsDiscussionAdapter(
            client,
            workspace_path=settings.workspace,
            enable_image_generation=settings.image_generation,
            enable_image_editing=settings.image_editing,
            enforce_end_tag=settings.enforce_end_tag,
        )

    def apply_settings(self, settings: DemoSettings) -> None:
        generator = self.build_discussion(settings)
        self.settings = settings
        self.online = True
        self.console.generator = generator
        self.console.header.right = "[bright_green]lollms · connected[/bright_green]"
        self.console.active_session.messages.append(
            {
                "role": "system",
                "content": (
                    f"Connected to lollms.\nWorkspace: `{settings.workspace}`\n"
                    f"Images: generation={settings.image_generation}, "
                    f"editing={settings.image_editing}"
                ),
                "timestamp": time.time(),
            }
        )
        self.console.chat_view._dirty = True
        self.console.chat_view.scroll_to_end()
        self.console.refresh()

    def open_settings(self) -> None:
        SettingsDialog(self).open()


class _EchoGenerator:
    """Offline generator showcasing streamed Markdown and code rendering."""

    def generate(self, prompt: str, history: List[dict], on_chunk) -> str:
        reply = (
            "I received your request:\n\n"
            f"> {prompt}\n\n"
            "This is the offline showcase. Press **F2** to configure and connect "
            "a real lollms discussion.\n\n"
            "```python\n"
            "def greet(name: str) -> str:\n"
            "    return f'Hello, {name}!'\n\n"
            "print(greet('lollms'))\n"
            "```\n\n"
            "- `/settings` opens the same panel\n"
            "- `F1` lists keyboard and mouse controls"
        )
        for index in range(0, len(reply), 9):
            on_chunk(reply[index:index + 9])
            time.sleep(0.008)
        return reply


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Connect using lollms_client")
    parser.add_argument("--binding", default="", help="Implies --online; configured by lollms env")
    parser.add_argument("--model", default="", help="Implies --online; configured by lollms env")
    parser.add_argument("--system", default="", help="Optional console history system prompt")
    parser.add_argument("--title", default="lollms console")
    parser.add_argument(
        "--workspace",
        default=str(Path.cwd() / "workspaces"),
        help="Discussion workspace for generated artifacts",
    )
    parser.add_argument("--no-images", action="store_true", help="Disable image generation/editing")
    parser.add_argument("--no-sidebar", action="store_true", help="Hide the session rail")
    return parser.parse_args()


def main() -> int:
    # Capture startup and configuration logs before importing/constructing a
    # real client. ChatbotApp reuses this handler and buffer idempotently.
    attach_log_capture()
    args = _parse_args()
    settings = DemoSettings(
        workspace=args.workspace,
        image_generation=not args.no_images,
        image_editing=not args.no_images,
    )
    demo = ConsoleDemo(settings)
    generator = _EchoGenerator()
    startup_error = ""
    if args.online or args.binding or args.model:
        try:
            generator = demo.build_discussion(settings)
            demo.online = True
        except Exception as exc:
            startup_error = f"{type(exc).__name__}: {exc}"

    console = ChatbotApp(
        generator,
        title=args.title,
        system_prompt=args.system or None,
        user_label="You",
        assistant_label="Lollms",
        show_sidebar=not args.no_sidebar,
        on_settings=demo.open_settings,
    )
    demo.console = console
    console.header.right = (
        "[bright_green]lollms · connected[/bright_green]"
        if demo.online
        else "[bright_black]offline showcase · F2 to connect[/bright_black]"
    )
    console.status.left = (
        "[dim]Enter send · Tab complete · F1 help · F2 settings · F3 logs[/dim]"
    )
    if startup_error:
        console.active_session.messages.append(
            {
                "role": "error",
                "content": f"Could not connect to lollms: {startup_error}",
                "timestamp": time.time(),
            }
        )
    elif not demo.online:
        console.active_session.messages.append(
            {
                "role": "system",
                "content": "Offline mode. F2 connects · F3 shows captured logs.",
                "timestamp": time.time(),
            }
        )
    console.chat_view._dirty = True
    try:
        console.run()
    except RuntimeError as exc:
        print(f"tui_chatbot_demo: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())