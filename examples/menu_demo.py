"""
Comprehensive demo for the interactive Menu system.
Demonstrates the fixed in-place rendering (no screen scrolling/flickering)
across all menu modes: Execute, Select, and Checkbox.
Includes nested submenus with single and multi-select settings, and a final summary.
"""

import sys
from ascii_colors import Menu, ASCIIColors

# Top-level state dictionary to aggregate settings from submenus
app_settings = {
    "language": None,
    "theme": "Dark",
    "toppings": []
}

def show_settings_summary():
    """Displays the aggregated settings at the end of the session."""
    ASCIIColors.rule("Session Settings Summary", style="bold magenta")
    
    lang_str = app_settings["language"] or "Not Set"
    ASCIIColors.info(f"Selected Language : {lang_str}")
    ASCIIColors.info(f"UI Theme         : {app_settings['theme']}")
    
    toppings = app_settings["toppings"]
    if toppings:
        ASCIIColors.info(f"Pizza Toppings   : {', '.join(toppings)}")
    else:
        ASCIIColors.info("Pizza Toppings   : None (Cheese only)")
        
    ASCIIColors.rule(style="bold magenta")


def build_single_select_submenu(parent: Menu) -> Menu:
    """Build a submenu that returns a single value."""
    submenu = Menu("Application Settings", parent=parent, mode=Menu.MODE_RETURN)
    submenu.set_intro("Choose your preferred programming language for code generation.")
    submenu.add_choice("Python", value="python")
    submenu.add_choice("Rust", value="rust")
    submenu.add_choice("TypeScript", value="typescript")
    submenu.add_choice("C++", value="cpp", disabled=True)
    return submenu


def build_checkbox_submenu(parent: Menu) -> Menu:
    """Build a submenu that returns multiple values."""
    submenu = Menu("Feature Configuration", parent=parent, mode=Menu.MODE_CHECKBOX)
    submenu.set_intro("Select the optional features to enable for this session.")
    submenu.add_checkbox("Enable Telemetry", value="telemetry")
    submenu.add_checkbox("Verbose Logging", value="verbose", checked=True)
    submenu.add_checkbox("Auto-Save", value="autosave")
    return submenu


def demo_execute_mode():
    """Demonstrates a main dashboard with actions and nested settings submenus."""
    ASCIIColors.rule("MODE: EXECUTE (Dashboard & Submenus)", style="bold cyan")
    
    main_menu = Menu("Main Dashboard", mode=Menu.MODE_EXECUTE)
    main_menu.set_intro("Welcome! Use arrow keys to navigate. Select settings submenus to configure the app.")
    
    single_select = build_single_select_submenu(main_menu)
    multi_select = build_checkbox_submenu(main_menu)
    
    def run_language_selector():
        try:
            result = single_select.run()
            if result is not None:
                app_settings["language"] = result
                ASCIIColors.success(f"Language set to: {result}")
        except KeyboardInterrupt:
            ASCIIColors.warning("Language selection cancelled.")
            
    def run_feature_selector():
        try:
            result = multi_select.run()
            if result is not None:
                app_settings["toppings"] = result
                ASCIIColors.success(f"Features updated: {', '.join(result)}")
        except KeyboardInterrupt:
            ASCIIColors.warning("Feature selection cancelled.")
            
    main_menu.add_action("Configure Language (Single Select)", action=run_language_selector)
    main_menu.add_action("Configure Features (Multi Select)", action=run_feature_selector)
    main_menu.add_action("View Current Settings", action=show_settings_summary)
    
    result = main_menu.run()
    if result is None:
        ASCIIColors.warning("User quit the main menu. Halting demo.")
        sys.exit(0)
        
        
        
def demo_select_mode():
    """Demonstrates standalone single selection (questionary-style)."""
    ASCIIColors.rule("MODE: SELECT (Standalone Single Return)", style="bold magenta")
    
    select_menu = Menu("Choose UI Theme", mode=Menu.MODE_RETURN)
    select_menu.set_intro("Select the interface theme. This will be saved to app settings.")
    select_menu.add_choice("Dark Mode", value="Dark")
    select_menu.add_choice("Light Mode", value="Light")
    select_menu.add_choice("System Default", value="System")
    
    result = select_menu.run()
    if result is not None:
        app_settings["theme"] = result
        ASCIIColors.info(f"You selected: {result}")


def demo_checkbox_mode():
    """Demonstrates standalone multi-selection (questionary-style)."""
    ASCIIColors.rule("MODE: CHECKBOX (Standalone Multi-Return)", style="bold green")
    
    checkbox_menu = Menu("Select Pizza Toppings", mode=Menu.MODE_CHECKBOX)
    checkbox_menu.set_intro("Choose your preferred toppings. Press Space to toggle, Enter to confirm.")
    checkbox_menu.add_checkbox("Pepperoni", value="pepperoni")
    checkbox_menu.add_checkbox("Mushrooms", value="mushrooms", checked=True)
    checkbox_menu.add_checkbox("Extra Cheese", value="cheese")
    checkbox_menu.add_checkbox("Olives", value="olives")
    
    result = checkbox_menu.run()
    if result is not None:
        app_settings["toppings"] = result
        ASCIIColors.info(f"You selected toppings: {result}")


if __name__ == "__main__":
    try:
        # Run the interactive dashboard
        demo_execute_mode()
        
        # Run standalone selections
        demo_select_mode()
        demo_checkbox_mode()
        
        # Show final aggregated state
        show_settings_summary()
        
    except KeyboardInterrupt:
        ASCIIColors.warning("\nDemo exited by user.")
        sys.exit(0)