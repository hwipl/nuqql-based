#!/usr/bin/env python3

"""
Helper script for starting based
"""

import asyncio
import sys

import nuqql_based.main
import nuqql_based

# start nuqql-based
sys.exit(asyncio.run(nuqql_based.main.main()))
