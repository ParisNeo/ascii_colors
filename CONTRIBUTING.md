# Contributing to ASCIIColors

First off, thank you for considering contributing to ASCIIColors! We welcome contributions from everyone, whether it's reporting a bug, proposing a feature, or submitting code changes.

This document provides guidelines to help make the contribution process smooth and effective for everyone involved.

## Table of Contents

- [Getting Started](#getting-started)
  - [Forking the Repository](#forking-the-repository)
  - [Setting Up the Development Environment](#setting-up-the-development-environment)
- [Making Changes](#making-changes)
  - [Creating a Branch](#creating-a-branch)
  - [Coding Style](#coding-style)
  - [Linting and Formatting](#linting-and-formatting)
  - [Type Checking](#type-checking)
  - [Running Tests](#running-tests)
  - [Writing Tests](#writing-tests)
  - [Documentation](#documentation)
  - [Commiting Changes](#commiting-changes)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Code of Conduct](#code-of-conduct)
- [Getting Help](#getting-help)

## Getting Started

### Forking the Repository

1.  **Fork:** Click the "Fork" button on the top right of the [ASCIIColors GitHub repository](https://github.com/ParisNeo/ascii_colors) page. This creates your own copy of the project.
2.  **Clone:** Clone your forked repository to your local machine:
    ```bash
    git clone https://github.com/YOUR_USERNAME/ascii_colors.git
    cd ascii_colors
    ```
    Replace `YOUR_USERNAME` with your actual GitHub username.

### Setting Up the Development Environment

We strongly recommend using a virtual environment to manage dependencies and avoid conflicts with other projects.

1.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    ```
2.  **Activate Virtual Environment:**
    *   **macOS/Linux:** `source venv/bin/activate`
    *   **Windows (Git Bash):** `source venv/Scripts/activate`
    *   **Windows (CMD/PowerShell):** `venv\Scripts\activate`
3.  **Install Development Dependencies:**
    Install the tools needed for linting, formatting, testing, and type checking:
    ```bash
    pip install flake8 black isort mypy pytest pre-commit
    ```
    *(Note: `pytest` is recommended for running tests, although `unittest` can also be used directly.)*

## Making Changes

### Creating a Branch

Create a new branch for your feature or bug fix. Use a descriptive name, like:

*   `feature/add-network-handler`
*   `fix/resolve-rotation-bug`
*   `docs/update-readme-context`

```bash
git checkout -b feature/your-branch-name
```

### Coding Style

*   **PEP 8:** Follow the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/) for Python code.
*   **Black:** Code formatting is enforced using `black`. Don't worry about manual formatting; `black` will handle it automatically via `pre-commit` or manual runs.
*   **isort:** Import sorting is enforced using `isort`. It groups and sorts imports automatically.
*   **Docstrings:** Write clear and concise docstrings for new functions, classes, and methods. Google style docstrings are preferred but clarity is the main goal.

### Linting and Formatting

We use `pre-commit` to automatically run linters and formatters (`black`, `isort`, `flake8`) before each commit.

1.  **Install Hooks:** Set up the pre-commit hooks in your local repository (only needs to be done once per clone):
    ```bash
    pre-commit install
    ```
2.  **Automatic Checks:** Now, whenever you run `git commit`, `pre-commit` will run the configured checks on the files you've staged (`git add ...`).
    *   If `black` or `isort` modify files, the commit will be aborted. Simply review the changes, `git add` the modified files again, and re-run `git commit`.
    *   If `flake8` reports errors, the commit will be aborted. You need to fix the reported issues manually, `git add` the fixes, and re-run `git commit`.
3.  **Manual Run:** You can run the checks on all files at any time using:
    ```bash
    pre-commit run --all-files
    ```
    Or run formatters/linters individually:
    ```bash
    black .
    isort .
    flake8 .  # Uses setup.cfg for configuration
    ```

### Type Checking

We use `mypy` for static type checking. Ensure your code includes type hints and passes `mypy` checks.

*   **Run `mypy`:**
    ```bash
    mypy ascii_colors/
    ```
    Fix any reported type errors. Configuration is in `setup.cfg`.

### Running Tests

Tests are crucial to ensure functionality and prevent regressions. We use Python's built-in `unittest` framework, located in the `tests/` directory.

*   **Run Tests:**
    *   Using `unittest`:
        ```bash
        python -m unittest tests/test_ascii_colors.py
        ```
    *   Using `pytest` (recommended for potentially better output):
        ```bash
        pytest tests/
        ```
*   **Ensure Tests Pass:** All tests must pass before submitting a pull request.

### Writing Tests

*   **New Features:** Add new test cases to `tests/test_ascii_colors.py` (or a new test file if appropriate) that cover the functionality of your new feature.
*   **Bug Fixes:** Add a test case that specifically reproduces the bug you are fixing. This ensures the bug is actually fixed and prevents it from recurring later.

### Documentation

*   **README.md:** If your changes affect the user-facing API, usage patterns, or add significant new features, update the relevant sections in `README.md`.
*   **Docstrings:** Ensure new functions, methods, and classes have clear docstrings explaining their purpose, arguments, and return values.

### Commiting Changes

*   **Stage Files:** `git add <your_modified_files>`
*   **Commit:** Write clear and concise commit messages. A good format is:
    ```
    feat: Add support for XYZ feature

    Detailed description of the changes, why they were made,
    and any relevant context. Fixes #123.
    ```
    (Using prefixes like `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` is encouraged but not strictly required.)

## Submitting a Pull Request

1.  **Push Branch:** Push your local branch to your forked repository on GitHub:
    ```bash
    git push origin feature/your-branch-name
    ```
2.  **Open Pull Request:** Go to the original [ASCIIColors repository](https://github.com/ParisNeo/ascii_colors) on GitHub. You should see a prompt to create a Pull Request (PR) from your recently pushed branch. Click it.
3.  **Describe PR:** Fill out the PR template:
    *   Provide a clear title.
    *   Describe the changes you made (the "what" and "why").
    *   Link to any relevant issues (e.g., `Fixes #123`).
    *   Explain how the changes can be tested or verified.
4.  **Submit & Review:** Submit the PR. Project maintainers will review your code. Be prepared to respond to feedback and make adjustments if necessary. Continuous Integration (CI) checks (if configured) must pass.
5.  **Merge:** Once approved and all checks pass, a maintainer will merge your contribution. Congratulations!

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. *(Maintainer: If you add a CODE_OF_CONDUCT.md file, link it here. Otherwise, keep a general statement about respectful interaction.)* We expect all contributors to interact respectfully and constructively.

## Getting Help

If you get stuck, have questions, or want to discuss a potential contribution before starting, feel free to open an [Issue](https://github.com/ParisNeo/ascii_colors/issues) on GitHub.

---

Thank you again for your interest in contributing to ASCIIColors!