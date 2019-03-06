# -*- coding: utf-8 -*-
# Copyright (c) 2019 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import os
from setuptools import setup, find_packages

from cygnus import __version__

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Cygnus",
    version = __version__,
    author = "Jesse Mather",
    author_email = "jmather@arista.com",
    description = "EOSSDK based SWAN replica",
    long_description = "", #read("README.md"),
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Network Engineers",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Environment :: Functional Testing Automation"
    ],
    packages = find_packages(),
    url = "http://aristanetworks.com",
    license = "Proprietary",
    scripts = ['scripts/Cygnus'],
    options = {
        "bdist_rpm": {
            "post_install" : "scripts/post_install.sh",
            "post_uninstall" : "scripts/post_uninstall.sh"
        }
    }
)
