#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from setuptools import setup


def get_content(filename):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename), encoding="utf-8") as f:
        return f.read()


setup(
    name='datalog_http_monitoring',
    version='1.0.0',
    packages=['datalog_http_monitoring'],
    author='Cyril DEMINGEON',
    install_requires=[l for l in get_content('requirements.txt').split() if '==' in l],
    entry_points={
        'console_scripts': ['datalog=datalog_http_monitoring.__main__:main'],
    }
)
