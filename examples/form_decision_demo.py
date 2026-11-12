# -*- coding: utf-8 -*-
"""
Demo: Form Decision Calling

Exercises the `form()` helper from ascii_colors.questionary to demonstrate
a decision chain: a `Confirm` gate that, when answered "no", short-circuits
the rest of the form (the `Form.ask` early-exit behavior).

Run:
    python examples/form_decision_demo.py

Author: Saifeddine ALOUI (ParisNeo)
License: Apache License 2.0
"""

from ascii_colors import ASCIIColors
from ascii_colors.questionary import form, confirm, select, text


def build_decision_form():
    """Build a form that asks the user whether to continue, then collect details."""
    return form(
        confirm(
            "Do you want to launch the deployment?",
            default=False,
            name="proceed",
        ),
        select(
            "Choose target environment:",
            choices=[
                {"name": "Development", "value": "dev"},
                {"name": "Staging", "value": "staging"},
                {"name": "Production", "value": "prod"},
            ],
            name="environment",
        ),
        text(
            "Enter release version (e.g. 1.2.3):",
            name="version",
            default="0.1.0",
        ),
    )


def main():
    ASCIIColors.cyan("=== Form Decision Calling Demo ===\n", flush=True)

    answers = build_decision_form().ask()

    ASCIIColors.info("\n--- Collected Answers ---")
    for key, value in answers.items():
        ASCIIColors.green(f"  {key}: {value}")

    if answers.get("proceed") is not True:
        ASCIIColors.warning("\nDeployment cancelled by user decision (early-exit path).")
        return 0

    ASCIIColors.success(
        f"\nDeploying version {answers.get('version')} to "
        f"{answers.get('environment')} ... done."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())