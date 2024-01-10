################################################################################
# \file test_msg_diagram
#
# Generate diagrams and verify they are valid graphviz files
#
# Copyright (c) 2024 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import os, sys, shutil, time

script_dir = os.path.dirname(__file__)
repo_root_dir = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
sys.path.insert(0, repo_root_dir)

from mavlib_gen.generator import generate

# when True, generated files will not be deleted on module teardown
DEBUG_MODE = True
TESTGEN_OUTPUT_BASE_DIR = os.path.abspath(
    os.path.join(
        script_dir,
        "..",
        "..",
        "test_artifacts",
        f"graphviz_msg_diagram_tests{str(int(time.time_ns() / 1000))}",
    )
)

DIALECT_NAME = "message_type_tests"

TEST_MSG_DEF = os.path.abspath(os.path.join(script_dir, "..", "test_cases", f"{DIALECT_NAME}.xml"))


def test_graphviz_diagram():
    """For now just testing that generating the diagrams doesnt cause a crash"""
    assert generate(TEST_MSG_DEF, "graphviz", TESTGEN_OUTPUT_BASE_DIR)


def test_inc_tree_diagram():
    files = ["top_level.xml", "top_level2.xml"]
    complex_tree_folder = os.path.join(repo_root_dir, "tests", "xml_validator_tests", "test_cases")
    abs_files = [
        os.path.join(complex_tree_folder, "pass", "complex_include_graph", fname) for fname in files
    ]
    assert generate(abs_files, "graphviz", TESTGEN_OUTPUT_BASE_DIR)
