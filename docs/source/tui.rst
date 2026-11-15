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