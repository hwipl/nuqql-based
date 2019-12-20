#!/usr/bin/env python3

"""
nuqql-based setup file
"""

import os
import re
import codecs

from setuptools import setup

# setup parameters
DESCRIPTION = "Basic network daemon library for nuqql"
with open("README.md", 'r') as f:
    LONG_DESCRIPTION = f.read()
CLASSIFIERS = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
]


# setup helpers
def read(*parts):
    """
    Read encoded file
    """

    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, *parts), 'r') as enc_file:
        return enc_file.read()


def find_version(*file_paths):
    """
    Find version in encoded file
    """

    version_file = read(*file_paths)
    version_pattern = r"^VERSION = ['\"]([^'\"]*)['\"]"
    version_match = re.search(version_pattern, version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# run setup
setup(
    name="nuqql-based",
    version=find_version("nuqql_based", "main.py"),
    description=DESCRIPTION,
    license="MIT",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="hwipl",
    author_email="nuqql-based@hwipl.net",
    url="https://github.com/hwipl/nuqql-based",
    package_data={"nuqql_based": ["py.typed"]},
    packages=["nuqql_based"],
    entry_points={
        "console_scripts": ["nuqql-based = nuqql_based.main:main"]
    },
    classifiers=CLASSIFIERS,
    python_requires='>=3.6',
    zip_safe=False,
)
