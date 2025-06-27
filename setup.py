"""Setup script for MagnetRun package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="magnetrun",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package for analyzing magnetic measurement data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/magnetrun",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
        "pint>=0.18",
        "natsort>=8.0.0",
        "click>=8.0.0",
        "npTDMS>=1.2.0",
        "tabulate>=0.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "magnetrun=magnetrun.cli.commands:cli",
        ],
    },
)
