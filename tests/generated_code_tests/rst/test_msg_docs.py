################################################################################
# \file test_msg_docs
#
# Generate docs and verify they are valid syntax
#
# Copyright (c) 2024 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import sys, time
from pathlib import Path
import subprocess

script_dir = Path(__file__).parent.resolve()
repo_root_dir = script_dir.parent.parent.parent.absolute()
sys.path.insert(0, repo_root_dir)

from mavlibgen import MavlibgenRunner
from mavlib_gen.lang_generators.generator_rst import RstLangGenerator
from mavlib_gen.lang_generators.generator_base import OneShotGeneratorWrapper

DIALECT_NAME = "message_type_tests"

TEST_MSG_DEF = script_dir.parent / "test_cases" / f"{DIALECT_NAME}.xml"


def test_rst_msg_doc():
    """Verify that generating base RST docs doesnt crash"""
    TESTGEN_OUTPUT_BASE_DIR = (
        script_dir.parent.parent
        / "test_artifacts"
        / f"rst_msg_doc_tests{str(int(time.time_ns() / 1000))}"
    )
    assert MavlibgenRunner.generate_once(TEST_MSG_DEF, "rst", TESTGEN_OUTPUT_BASE_DIR)


def test_rst_with_sphinx_doc():
    """
    Verify generation works when generating additional sphinx-specific pages is enabled.
    Then. verify generating html docs with these via sphinx-build actually works! (sphinx-build
    returns a 0)
    """
    TESTGEN_OUTPUT_BASE_DIR = (
        script_dir.parent.parent
        / "test_artifacts"
        / f"rst_msg_doc_tests{str(int(time.time_ns() / 1000))}"
    )
    rstgen = RstLangGenerator(generate_sphinx_root=True, include_msg_diagrams=True)
    gen = OneShotGeneratorWrapper(rstgen, output_dir=TESTGEN_OUTPUT_BASE_DIR)
    runner = MavlibgenRunner(mavlink_xmls=TEST_MSG_DEF, generator=gen)
    assert runner.run()

    sphinx_cmd = [
        "sphinx-build",
        "-bhtml",
        TESTGEN_OUTPUT_BASE_DIR,
        TESTGEN_OUTPUT_BASE_DIR / "_sphinx_build",
    ]
    assert subprocess.check_call(sphinx_cmd) == 0


def test_rst_with_sphinx_doc_multi_xml():
    """
    Verify sphinx-based generation works when multiple XML's are involved
    """
    TESTGEN_OUTPUT_BASE_DIR = (
        script_dir.parent.parent
        / "test_artifacts"
        / f"rst_msg_doc_tests{str(int(time.time_ns() / 1000))}"
    )
    files = ["top_level.xml", "top_level2.xml"]
    complex_tree_folder = repo_root_dir / "tests" / "xml_validator_tests" / "test_cases"
    abs_files = [complex_tree_folder / "pass" / "complex_include_graph" / fname for fname in files]
    rstgen = RstLangGenerator(generate_sphinx_root=True, include_msg_diagrams=True)
    gen = OneShotGeneratorWrapper(rstgen, output_dir=TESTGEN_OUTPUT_BASE_DIR)
    runner = MavlibgenRunner(mavlink_xmls=abs_files, generator=gen)
    assert runner.run()

    sphinx_cmd = [
        "sphinx-build",
        "-bhtml",
        TESTGEN_OUTPUT_BASE_DIR,
        TESTGEN_OUTPUT_BASE_DIR / "_sphinx_build",
    ]
    assert subprocess.check_call(sphinx_cmd) == 0
