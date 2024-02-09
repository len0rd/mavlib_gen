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
import sys, shutil, time
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, script_dir.parent.parent.parent.absolute())

from typing import Union, List
from mavlibgen import MavlibgenRunner

# when True, generated files will not be deleted on module teardown
DEBUG_MODE = True
TESTGEN_OUTPUT_BASE_DIR = (
    script_dir.parent.parent
    / "test_artifacts"
    / f"pygen_msg_tests{str(int(time.time_ns() / 1000))}"
)

DIALECT_NAME = "message_type_tests"

TEST_MSG_DEF = script_dir.parent / "test_cases" / f"{DIALECT_NAME}.xml"


def generate_mavlib(file_in: Union[List[str], str], dir_out: str) -> bool:
    return MavlibgenRunner.generate_once(file_in, "python", dir_out)


def setup_module(module):
    """pytest module setup. Generate the code that will be under test"""
    assert MavlibgenRunner.generate_once(TEST_MSG_DEF, "python", TESTGEN_OUTPUT_BASE_DIR)
    sys.path.insert(0, TESTGEN_OUTPUT_BASE_DIR.as_posix())


def teardown_module(module):
    """pytest module teardown. remove all auto-generated files"""
    if TESTGEN_OUTPUT_BASE_DIR.is_dir() and not DEBUG_MODE:
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
