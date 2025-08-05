#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Pytest configuration file
"""

import pytest
import sys
import os

# Add the parent directory to Python path so we can import from python_magnetrun
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


