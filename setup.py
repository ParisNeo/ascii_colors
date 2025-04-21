# -*- coding: utf-8 -*-
"""
Setup script for the ascii_colors library.

Author: Saifeddine ALOUI (ParisNeo)
License: Apache License 2.0
"""

from setuptools import find_packages, setup

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ascii_colors",
    version="0.7.5",  # Updated version
    description="A Python library for rich terminal output with advanced logging features.",
    long_description=long_description,
    long_description_content_type="text/markdown",  # Specify markdown format
    author="ParisNeo",
    author_email="parisneo_ai@gmail.com",
    url="https://github.com/ParisNeo/ascii_colors",  # Updated URL to main repo
    packages=find_packages(
        include=["ascii_colors", "ascii_colors.*"]
    ),  # Ensure submodules are found
    classifiers=[
        "Development Status :: 4 - Beta",  # Upgraded status
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",  # Added OS Independent classifier
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Logging",  # Added relevant topic
        "Topic :: Terminals",  # Added relevant topic
        "Topic :: Utilities",  # Added relevant topic
    ],
    python_requires=">=3.8",
    keywords=[
        "logging",
        "color",
        "terminal",
        "console",
        "ansi",
        "style",
        "format",
        "json",
        "log rotation",
        "context",
    ],
    # No external dependencies required for core functionality
)
