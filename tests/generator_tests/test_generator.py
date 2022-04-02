################################################################################
# \file test_generator
#
# Tests for the top-level generator script. Language-specific generator tests
# should have their own subfolder
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
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, "..", "..")))

from mavlib_gen.generator import generate, GENERATOR_MAP

TEST_OUT_DIR = os.path.abspath(
    os.path.join(script_dir, "..", "test_artifacts", str(int(time.time_ns() / 1000)))
)

# since these are high-level smoke tests, it doesnt matter what lang is used
VALID_OUTPUT_LANG = list(GENERATOR_MAP.keys())[0]


def teardown_module(module):
    """pytest module teardown. remove any generated mavlink files"""
    if os.path.isdir(TEST_OUT_DIR):
        shutil.rmtree(TEST_OUT_DIR)


def test_generator_bad_inputs():
    """verify top-level generate method rejects bad inputs"""
    # Bad xml input param
    assert not generate(None, VALID_OUTPUT_LANG, TEST_OUT_DIR)
    # bad output language
    assert not generate(["test.xml"], "asdf", TEST_OUT_DIR)


def test_no_gen_on_validation_fail():
    """Verify if XML validation fails, no files are generated"""
    invalid_file = os.path.join(script_dir, "test_cases", "invalid_mavlink.xml")
    assert not generate(invalid_file, VALID_OUTPUT_LANG, TEST_OUT_DIR)


def test_gen_with_valid_file():
    """verify if the file is valid, generate returns true"""
    valid_file = os.path.join(script_dir, "test_cases", "valid_mavlink.xml")
    assert generate(valid_file, VALID_OUTPUT_LANG, TEST_OUT_DIR)
