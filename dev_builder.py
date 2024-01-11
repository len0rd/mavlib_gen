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
import pytest
from pathlib import Path

log = logging.getLogger("dev")

SCRIPT_ROOT = Path(__file__).parent.resolve()

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARN,
    "error": logging.ERROR,
    "fatal": logging.FATAL,
}


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

    doc_source_path = SCRIPT_ROOT / "docs"
    doc_build_path = doc_source_path / "_build"

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
            command = [
                "sphinx-build",
                "-bhtml",
                cls.doc_source_path.as_posix(),
                cls.doc_build_path.as_posix(),
            ]
            return run_check_call(command)
        elif args.build_type == "autobuild":
            command = [
                "sphinx-autobuild",
                cls.doc_source_path.as_posix(),
                cls.doc_build_path.as_posix(),
            ]
            return run_check_call(command)
        elif args.build_type == "clean":
            if Path(cls.doc_build_path).is_dir():
                shutil.rmtree(cls.doc_build_path)
            return 0
        elif args.build_type == "check":
            # run sphinx's link-check to verify validity of all external links
            command = [
                "sphinx-build",
                "-blinkcheck",
                cls.doc_source_path.as_posix(),
                cls.doc_build_path.as_posix(),
            ]
            return run_check_call(command)

        log.fatal(f"Unknown build_type '{args.build_type}' for docs command")
        return 1


class StyleChecker:
    """
    Encapsulates running the command to check python library style
    """

    flake_config_path = SCRIPT_ROOT / ".flake8"
    library_path = SCRIPT_ROOT / "mavlib_gen"

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
        command = [
            "flake8",
            "--config",
            cls.flake_config_path.as_posix(),
            cls.library_path.as_posix(),
        ]
        ret_code = run_check_call(command)
        if ret_code == 0:
            log.info("Style checks passed!")
        return ret_code


class UnitTestRunner:
    """
    Encapsulates running various levels of unit tests
    """

    @staticmethod
    def add_arguments(subparser: argparse._SubParsersAction) -> None:
        """
        Add arguments to a new subparser.
        TODO: in future support passing path so style can be checked on generated
        python lib
        TODO: clang-format enforcement for C++ generated code?
        """
        test_subparser = subparser.add_parser(
            "test",
            help="Run package unit tests",
        )
        test_subparser.add_argument(
            "-c", "--cov", action="store_true", help="Produce coverate report"
        )
        test_subparser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            default=False,
            help="Run tests verbosely using the log level provided to this script via -l/--level",
        )

        test_subparser.set_defaults(func=UnitTestRunner.run)

    @classmethod
    def run(cls, args: argparse.Namespace) -> int:
        """Run unit tests"""
        pytest_args = ["tests/"]
        if args.verbose:
            pytest_args.extend(["-v", "-o", "log_cli=true"])
        if args.cov:
            pytest_args.extend(["--cov=mavlib_gen/", "--cov-report=xml"])
        return pytest.main(pytest_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="./dev_builder.py`")
    subparsers = parser.add_subparsers(dest="cmd")
    parser.add_argument(
        "-l",
        "--level",
        help="Specify the log level to run the command at",
        default="error",
        choices=LOG_LEVELS.keys(),
    )

    # add subparsers as needed here
    DocumentationBuilder.add_arguments(subparsers)
    StyleChecker.add_arguments(subparsers)
    UnitTestRunner.add_arguments(subparsers)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    logging.basicConfig(level=LOG_LEVELS[args.level.lower()])

    sys.exit(args.func(args))
