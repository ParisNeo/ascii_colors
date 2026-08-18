import io
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure local source is imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from ascii_colors.menu import Menu, MenuItem


def test_menu_does_not_use_full_screen_clear():
    """Ensure the menu never uses \033[2J or os.system('cls') which destroys the terminal history."""
    buffer = io.StringIO()
    menu = Menu("Test Menu", mode=Menu.MODE_RETURN, clear_screen_on_run=True, file=buffer)
    menu.add_choice("Option 1")
    menu.add_choice("Option 2")
    
    menu._key_source = iter(["DOWN", "ENTER"])
    
    try:
        menu.run()
    except Exception:
        pass
    
    output = buffer.getvalue()
    
    assert "\033[2J" not in output, "Menu used \033[2J (full screen clear)!"
    assert "\x1b[2J" not in output, "Menu used \x1b[2J (full screen clear)!"
    
    with patch("os.system") as mock_system:
        menu._key_source = iter(["DOWN", "ENTER"])
        try:
            menu.run()
        except Exception:
            pass
        mock_system.assert_not_called()


def test_menu_uses_in_place_cursor_repositioning():
    """Ensure the menu redraws using cursor up (\033[A) and line clear (\033[K)."""
    buffer = io.StringIO()
    menu = Menu("Test Menu", mode=Menu.MODE_RETURN, clear_screen_on_run=True, file=buffer)
    menu.add_choice("Option 1")
    menu.add_choice("Option 2")
    
    menu._key_source = iter(["DOWN", "DOWN", "ENTER"])
    
    try:
        menu.run()
    except Exception:
        pass
    
    output = buffer.getvalue()
    
    assert "\x1b[" in output and "A" in output, "Expected cursor up ANSI sequence for in-place rendering!"
    assert "\x1b[K" in output or "\033[K" in output, "Expected clear line ANSI sequence for in-place rendering!"


def test_menu_navigation_state_integrity():
    """Ensure the selection index updates correctly without rendering."""
    buffer = io.StringIO()
    menu = Menu("Test Menu", mode=Menu.MODE_RETURN, file=buffer)
    menu.add_choice("Option 1")
    menu.add_choice("Option 2")
    menu.add_choice("Option 3")
    
    menu._key_source = iter(["DOWN", "DOWN", "ENTER"])
    
    result = menu.run()
    
    assert result == "Option 3", f"Expected 'Option 3', got {result}"


def test_submenu_cursor_synchronization():
    """Ensure submenu execution does not corrupt the parent's line tracking state."""
    parent_buffer = io.StringIO()
    
    parent = Menu("Parent Menu", mode=Menu.MODE_RETURN, file=parent_buffer)
    parent.add_choice("Option 1")
    parent.add_choice("Option 2")
    
    submenu = Menu("Submenu", mode=Menu.MODE_RETURN, file=parent_buffer)
    submenu.add_choice("Sub A")
    submenu.add_choice("Sub B")
    
    parent.add_submenu("Go to Submenu", submenu)
    
    keys = iter(["DOWN", "DOWN", "ENTER", "ENTER"])
    parent._key_source = keys
    submenu._key_source = keys
    
    initial_parent_lines = parent._last_frame_lines
    
    try:
        result = parent.run()
    except Exception:
        pass
    
    assert parent._last_frame_lines == 0, "Parent menu did not reset its frame tracker on exit!"
    assert submenu._last_frame_lines == 0, "Submenu did not reset its frame tracker, which corrupts parent redraws!"
    
    assert result == "Sub A", f"Expected 'Sub A', got {result}"


def test_quit_key_execution_mode():
    """Ensure pressing 'q' in MODE_EXECUTE cleanly exits the loop and returns None."""
    buffer = io.StringIO()
    menu = Menu("Test Menu", mode=Menu.MODE_EXECUTE, file=buffer)
    menu.add_action("Action 1")
    menu.add_action("Action 2")

    menu._key_source = iter(["q"])
    result = menu.run()

    assert result is None, f"Expected None when quitting, got {result}"
    assert menu._quit is True, "Menu did not set _quit flag to True"


def test_menu_shortcuts_and_separators():
    """Test menu shortcuts and separators."""
    buffer = io.StringIO()
    menu = Menu("Shortcuts Menu", mode=Menu.MODE_RETURN, enable_shortcuts=True, file=buffer)
    menu.add_choice("First Choice", value=1, shortcut="1")
    menu.add_separator("--- Section 2 ---")
    menu.add_choice("Second Choice", value=2, shortcut="2")

    # Press '2' directly for hotkey instant selection
    menu._key_source = iter(["2"])
    result = menu.run()
    assert result == 2


def test_menu_checkbox_toggle_all_and_invert():
    """Test checkbox 'a' (toggle all) and 'i' (invert selection)."""
    buffer = io.StringIO()
    menu = Menu("Checkbox Menu", mode=Menu.MODE_CHECKBOX, file=buffer)
    menu.add_checkbox("Item 1", value="A", checked=False)
    menu.add_checkbox("Item 2", value="B", checked=False)

    # Press 'a' (select all), then ENTER to confirm
    menu._key_source = iter(["a", "ENTER"])
    result = menu.run()
    assert result == ["A", "B"]

    # Press 'i' (invert selection from initially checked item)
    menu2 = Menu("Invert Menu", mode=Menu.MODE_CHECKBOX, file=buffer)
    menu2.add_checkbox("Item 1", value="A", checked=True)
    menu2.add_checkbox("Item 2", value="B", checked=False)
    menu2._key_source = iter(["i", "ENTER"])
    result2 = menu2.run()
    assert result2 == ["B"]


def test_menu_default_initial_selection():
    """Test menu opening with default selection index/value."""
    buffer = io.StringIO()
    menu = Menu("Default Selection Menu", mode=Menu.MODE_RETURN, default="Target", file=buffer)
    menu.add_choice("Choice 1", value="First")
    menu.add_choice("Choice 2", value="Target")
    menu.add_choice("Choice 3", value="Third")

    # Press ENTER immediately to select default
    menu._key_source = iter(["ENTER"])
    result = menu.run()
    assert result == "Target"