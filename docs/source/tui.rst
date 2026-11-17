.. _tui-guide:

TUI Framework
=============

.. automodule:: ascii_colors.tui
   :no-members:

``ascii_colors`` ships a curses-style, widget-based TUI framework for building
richly-styled interactive console applications with focus handling, diff-based
rendering, and alternate-screen support. It has **no external dependencies** and
works on Windows, macOS, and Linux.

Use the TUI layer when you need persistent full-screen interfaces,
keyboard-driven navigation across multiple widgets, or real-time dashboards.
For lighter interactions prefer :doc:`interactive_prompts` (questionary-style
prompts) or :class:`ascii_colors.ProgressBar`.

Quick example
-------------

.. code-block:: python

   from ascii_colors.tui import App, VBox, Label, ListBox

   body = VBox(gap=1, pad=1)
   body.add(Label("[bold cyan]My App[/bold cyan]", align="center"))
   body.add(ListBox(["one", "two", "three"]))

   app = App()
   app.set_root(body)
   app.run()

Press ``Tab`` / ``Shift+Tab`` to cycle focus, ``Up`` / ``Down`` to navigate,
``Enter`` to activate the focused widget, and ``Esc`` to quit.

Application runtime
-------------------

.. autoclass:: ascii_colors.tui.app.App
   :members:
   :undoc-members:
   :show-inheritance:

Screen buffer & rendering
-------------------------

.. automodule:: ascii_colors.tui.screen
   :members: ScreenBuffer, ScreenRenderer, Cell
   :undoc-members:
   :show-inheritance:

Borders
-------

.. automodule:: ascii_colors.tui.borders
   :members: BORDERS, get_border
   :undoc-members:

Widgets
-------

The widget set covers layout containers, text and status displays, input
controls, data views, and lightweight charts.

.. automodule:: ascii_colors.tui.widgets
   :members:
   :undoc-members:
   :show-inheritance:

Advanced agent console
----------------------

``ChatbotApp`` wraps any streaming or non-streaming generator in the responsive
**lollms console**, with a responsive block-letter welcome banner, compact
mascot, wordmark, and session sidebar. The composer receives initial focus so
users can type immediately. It includes clickable sessions, mouse-wheel scrolling,
Markdown/code/tool transcript cards, token and latency metadata, a multi-line
composer, slash commands, and background generation marshalled through
``App.post()`` so worker threads never mutate widgets during rendering.

.. code-block:: python

   from ascii_colors.tui import ChatbotApp

   def generate(prompt, history, on_chunk):
       for token in ("Hello", " from", " the agent"):
           on_chunk(token)
       return "Hello from the agent"

   app = ChatbotApp(generate, title="My Agent")
   app.run()

Use ``Ctrl+N`` for a new conversation, ``Ctrl+L`` to clear one, ``F1`` for
help, and ``Ctrl+Q`` to exit. Composer commands include ``/new``, ``/clear``,
``/title NAME``, ``/model``, ``/logs``, ``/logs clear``, ``/settings`` and
``/help``. Typing ``/`` opens command autocomplete with descriptions. Use
Up/Down to choose, Tab or Right to accept, Enter to run, Escape to dismiss,
or click a suggestion. ``add_tool_event()`` inserts tool
activity cards into the active transcript. ``RichChatView`` is also exported
for applications that want the advanced transcript inside a custom layout.

The complete example in ``examples/tui/tui_chatbot_demo.py`` also provides an
**F2 settings panel** (or ``/settings``) for the discussion workspace, image
generation/editing, and end-tag enforcement. Online operation requires the
optional ``lollms_client`` package and uses ``LollmsDiscussion.chat()`` with
``MSG_TYPE_CHUNK`` streaming callbacks:

.. code-block:: bash

   pip install lollms_client
   python examples/tui/tui_chatbot_demo.py --online

Connection creation is delegated to ``get_client_from_env(create_tti=True)``;
configure lollms through its normal environment/saved configuration. Applying
the settings panel while offline connects on demand. The console itself still
works without ``lollms_client`` by supplying any other generator. Applying
settings calls ``ChatbotApp.refresh()`` so connection status and transcript
state are repainted immediately. ``App.refresh(clear=True)`` is available to
applications that also need to clear stale terminal cells after an overlay.

Captured terminal logs
----------------------

Every ``ChatbotApp`` installs a bounded, thread-safe ``TerminalLogBuffer``
handler before generator construction. It captures all ASCIIColors levels,
including lollms configuration logs, without writing raw output over the TUI.
Use ``/logs`` or ``F3`` to open the viewer, type to filter, choose Errors to
filter by level, use Clear to empty it, and Escape to return to Compose.
``/logs clear`` clears it directly. Repeated console creation is idempotent.

The standalone API is also exported:

.. code-block:: python

   from ascii_colors.tui import TerminalLogBuffer, attach_log_capture

   logs = attach_log_capture(TerminalLogBuffer(max_entries=4000))
   print(logs.text(level="ERROR"))

Captured terminal logs
----------------------

Every ``ChatbotApp`` installs a bounded, thread-safe ``TerminalLogBuffer``
handler before generator construction. It captures ASCIIColors records,
including lollms configuration logs, without writing raw output over the TUI.
Use ``/logs`` or ``F3`` to open the viewer, type to filter, choose Errors to
filter by level, use Clear to empty it, and Escape to return to Compose.
``/logs clear`` clears it directly. Repeated console creation is idempotent.

The standalone API is also exported:

.. code-block:: python

   from ascii_colors.tui import TerminalLogBuffer, attach_log_capture

   logs = attach_log_capture(TerminalLogBuffer(max_entries=4000))
   print(logs.text(level="ERROR"))

Custom widgets
--------------

Subclass :class:`ascii_colors.tui.widgets.Widget` and implement ``layout()``
(optional), ``draw(buffer)``, and — if interactive — ``handle_key(key)``. The
:class:`ascii_colors.tui.screen.ScreenBuffer` passed to ``draw`` exposes
``set_cell``, ``put``, ``draw_text``, ``draw_wrapped``, and related helpers that
respect wide characters and ANSI styling.

.. code-block:: python

   from ascii_colors.tui import Widget
   from ascii_colors.tui.screen import ScreenBuffer


   class Hello(Widget):
       def draw(self, buffer: ScreenBuffer) -> None:
           buffer.draw_text(
               self.x, self.y,
               "[bold green]Hello![/bold green]",
               max_width=self.w,
           )