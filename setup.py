#!/usr/bin/env python
from setuptools import setup, find_packages

from config import VERSION, APP_NAME

setup(
      name=APP_NAME,
      version=VERSION,
      packages=find_packages()
)
