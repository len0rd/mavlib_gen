################################################################################
# \file test_runner
#
# Generates code and then calls the correct script to run tests against
# the generated code
#
# Copyright (c) 2022 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import os, sys, shutil, time

script_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, "..", "..", "..")))

from typing import Union, List
from mavlib_gen.generator import generate

# when True, generated files will not be deleted on module teardown
DEBUG_MODE = True
TESTGEN_OUTPUT_BASE_DIR = os.path.abspath(
    os.path.join(
        script_dir,
        "..",
        "..",
        "test_artifacts",
        f"pygen_msg_tests{str(int(time.time_ns() / 1000))}",
    )
)

DIALECT_NAME = "message_type_tests"

TEST_MSG_DEF = os.path.abspath(os.path.join(script_dir, "..", "test_cases", f"{DIALECT_NAME}.xml"))


def generate_mavlib(file_in: Union[List[str], str], dir_out: str) -> bool:
    return generate(file_in, "python", dir_out)


def setup_module(module):
    """pytest module setup. Generate the code that will be under test"""
    assert generate(TEST_MSG_DEF, "python", TESTGEN_OUTPUT_BASE_DIR)
    sys.path.insert(0, TESTGEN_OUTPUT_BASE_DIR)


def teardown_module(module):
    """pytest module teardown. remove all auto-generated files"""
    if os.path.isdir(TESTGEN_OUTPUT_BASE_DIR) and not DEBUG_MODE:
        shutil.rmtree(TESTGEN_OUTPUT_BASE_DIR)


def test_message_serialization():
    from mavlink_types import MavlinkChannel
    from message_type_tests_msgs import MessageEmptyMsg

    mav_chn = MavlinkChannel(1, 2, 3)
    assert mav_chn is not None
    empty_msg = MessageEmptyMsg()
    serialized_msg = empty_msg.pack(mav_chn)
    EXPECTED_HEADER_BYTES = bytearray(
        [
            # STX
            0xFD,
            # payload length
            0x0,
            # incompat flags
            0x0,
            # compat flags
            0x0,
            # sequence_id
            0x0,
            # src system
            0x1,
            # src component
            0x2,
            # msgid low
            0x1,
            # msgid mid
            0x0,
            # msgid high
            0x0,
        ]
    )
    assert serialized_msg[:10] == EXPECTED_HEADER_BYTES
