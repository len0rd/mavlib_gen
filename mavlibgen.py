#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
################################################################################
# \file cli
#
# Top level Command Line Interface to the mavlib_gen library
#
# Copyright (c) 2024 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import argparse
import sys, os
import logging

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
print("In module products sys.path[0], __package__ ==", sys.path[0], __package__)
from mavlib_gen.validator import MavlinkXmlValidator

DEFAULT_GRAPH_FILE = "include_graph.dot"


def add_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--no-validation",
        action="store_true",
        default=False,
        help="Skip validation step",
    )
    parser.add_argument(
        "--no-generation", action="store_true", default=False, help="Skip generation step"
    )

    parser.add_argument(
        "xmls",
        nargs="+",
        help="One or more XMLs to work with. Validation will expand any includes so you do not need to add all of those XMLs as arguments",
    )


def run(args: argparse.Namespace):
    if not args.no_validation:
        xml_validator = MavlinkXmlValidator()
        result = xml_validator.validate(args.xmls)
        if result is None:
            return -1

    return 0


def main() -> int:
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    add_args(parser)
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
