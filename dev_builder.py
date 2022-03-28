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

SCRIPT_ROOT = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


def run_check_call(command: List[str]) -> int:
    """
    Runs the provided command and returns the result code
    """
    log.debug(f"Running: {' '.join(command)}")
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

    doc_source_path = os.path.join(SCRIPT_ROOT, "docs")
    doc_build_path = os.path.join(doc_source_path, "_build")

    @staticmethod
    def add_arguments(subparser: argparse._SubParsersAction) -> None:
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


class StyleChecker:
    """
    Encapsulates running the command to check python library style
    """

    flake_config_path = os.path.join(SCRIPT_ROOT, ".flake8")
    library_path = os.path.join(SCRIPT_ROOT, "mavlib_gen")

    @staticmethod
    def add_arguments(subparser: argparse._SubParsersAction) -> None:
        """
        Add arguments to a new subparser.
        TODO: in future support passing path so style can be checked on generated
        python lib
        TODO: clang-format enforcement for C++ generated code?
        """
        style_subparser = subparser.add_parser(
            "style",
            help="Check library code style is compliant",
        )
        style_subparser.set_defaults(func=StyleChecker.run)

    @classmethod
    def run(cls, args: argparse.Namespace) -> int:
        command = ["flake8", "--config", cls.flake_config_path, cls.library_path]
        ret_code = run_check_call(command)
        if ret_code == 0:
            log.info("Style checks passed!")
        return ret_code


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="./dev_builder.py`")
    subparsers = parser.add_subparsers(dest="cmd")

    # add subparsers as needed here
    DocumentationBuilder.add_arguments(subparsers)
    StyleChecker.add_arguments(subparsers)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    sys.exit(args.func(args))
