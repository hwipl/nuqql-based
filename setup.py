#!/usr/bin/env python3

"""
nuqql-based setup file
"""

from setuptools import setup

VERSION = "0.1"
DESCRIPTION = "Dummy network daemon for nuqql"
with open("README.md", 'r') as f:
    LONG_DESCRIPTION = f.read()
CLASSIFIERS = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
]

setup(
    name="nuqql-based",
    version=VERSION,
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
        "console_scripts": ["nuqql-based = nuqql_based.based:main"]
    },
    classifiers=CLASSIFIERS,
    python_requires='>=3.6',
    zip_safe=False,
)
