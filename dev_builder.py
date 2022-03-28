#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
################################################################################
# \file dev_builder
#
# Utility script for building and testing portions of the library
# and its generated code
#
# Copyright (c) 2022 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import sys, os, shutil
import argparse, argcomplete
import subprocess
import logging
from typing import List

log = logging.getLogger("dev")

script_root = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


def run_check_call(command: List[str]) -> int:
    """
    Runs the provided command and returns the result code
    """
    try:
        return subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        log.fatal(f"Running command: `{' '.join(command)}` failed.")
        return e.returncode


class DocumentationBuilder:
    """
    Encapsulates various commands useful when building documentation
    """

    AVAILABLE_SUBCOMMANDS = ["build", "autobuild", "check", "clean"]

    doc_source_path = os.path.join(script_root, "docs")
    doc_build_path = os.path.join(doc_source_path, "_build")

    @staticmethod
    def add_arguments(subparser: argparse._SubParsersAction):
        """
        Add arguments to a new subparser
        """
        docs_subparser = subparser.add_parser(
            "docs",
            help="Build the sphinx documentation",
        )
        docs_subparser.set_defaults(func=DocumentationBuilder.run)

        docs_subparser.add_argument(
            "build_type",
            help="Specify the type of build to run",
            choices=DocumentationBuilder.AVAILABLE_SUBCOMMANDS,
        )

    @classmethod
    def run(cls, args: argparse.Namespace) -> int:
        """
        Run documentation builder with the provided arguments
        """
        if args.build_type == "build":
            command = ["sphinx-build", "-bhtml", cls.doc_source_path, cls.doc_build_path]
            return run_check_call(command)
        elif args.build_type == "autobuild":
            command = ["sphinx-autobuild", cls.doc_source_path, cls.doc_build_path]
            return run_check_call(command)
        elif args.build_type == "clean":
            if os.path.isdir(cls.doc_build_path):
                shutil.rmtree(cls.doc_build_path)
            return 0
        elif args.build_type == "check":
            # run sphinx's link-check to verify validity of all external links
            command = ["sphinx-build", "-blinkcheck", cls.doc_source_path, cls.doc_build_path]
            return run_check_call(command)

        log.fatal(f"Unknown build_type '{args.build_type}' for docs command")
        return 1


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="./dev_builder.py`")
    subparsers = parser.add_subparsers(dest="cmd")
    DocumentationBuilder.add_arguments(subparsers)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    sys.exit(args.func(args))
