################################################################################
# \file test_msg_emb_cpp
#
# Generate code using the "emb_cpp" language and verify it builds
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

script_dir = Path(__file__).parent.resolve()
repo_root_dir = script_dir.parent.parent.parent.absolute()
sys.path.insert(0, repo_root_dir)

from mavlib_gen.generator import generate

# when True, generated files will not be deleted on module teardown
DEBUG_MODE = True
TESTGEN_OUTPUT_BASE_DIR = (
    script_dir.parent.parent
    / "test_artifacts"
    / f"emb_cpp_msg_tests{str(int(time.time_ns() / 1000))}"
)

DIALECT_NAME = "message_type_tests"

TEST_MSG_DEF = script_dir.parent / "test_cases" / f"{DIALECT_NAME}.xml"


def test_emb_cpp_generation():
    """For now just testing that generating the diagrams doesnt cause a crash"""
    assert generate(TEST_MSG_DEF, "emb_cpp", TESTGEN_OUTPUT_BASE_DIR)


# def test_inc_tree_diagram():
#     files = ["top_level.xml", "top_level2.xml"]
#     complex_tree_folder = repo_root_dir / "tests" / "xml_validator_tests" / "test_cases"
#     abs_files = [complex_tree_folder / "pass" / "complex_include_graph" / fname for fname in files]
#     assert generate(abs_files, "emb_cpp", TESTGEN_OUTPUT_BASE_DIR)
