from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="magnetrun",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive Python package for analyzing magnetic measurement data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/magnetrun",
    project_urls={
        "Bug Tracker": "https://github.com/yourorg/magnetrun/issues",
        "Documentation": "https://magnetrun.readthedocs.io",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910",
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=0.15",
            "sphinx-autodoc-typehints>=1.12",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "pytest-mock>=3.0",
            "pytest-benchmark=3.0",
            "hypothesis>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "magnetrun=magnetrun.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "magnetrun": ["config/*.yaml", "examples/data/*"],
    },
)
