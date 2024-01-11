################################################################################
# \file test_schema
#
# Test the XML schema without any other mavlib_gen code in the loop
#
# Copyright (c) 2022 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
from pathlib import Path
import xmlschema
import pytest

script_dir = Path(__file__).parent.resolve()
mav_schema_dir = script_dir.parent.parent / "mavlib_gen" / "schema"
schema = xmlschema.XMLSchema11(mav_schema_dir / "mavlink_schema.xsd", base_url=mav_schema_dir)

failure_test_case_dir = script_dir / "test_cases" / "fail"
schema_failure_files = [
    f for f in failure_test_case_dir.iterdir() if (Path(failure_test_case_dir) / f).is_file()
]

success_test_case_dir = script_dir / "test_cases" / "pass"
schema_success_files = [
    f for f in success_test_case_dir.iterdir() if (Path(success_test_case_dir) / f).is_file()
]


@pytest.mark.parametrize("filename", schema_failure_files)
def test_failure_cases(filename):
    test_file = failure_test_case_dir / filename
    assert not schema.is_valid(
        test_file
    ), f"Test case file '{filename}' passed schema validation when it should have failed"


@pytest.mark.parametrize("filename", schema_success_files)
def test_success_cases(filename):
    test_file = success_test_case_dir / filename
    try:
        assert schema.is_valid(
            test_file
        ), f"Test case file '{filename}' failed schema validation when it should have passed"
    except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
        err_msg = f"Validation of message definition file '{filename}'. "
        if e.reason is not None:
            err_msg += f"Reason: {e.reason}"
        if e.path is not None:
            err_msg += f" at path '{e.path}'"
        if xmlschema.etree.is_etree_element(e.elem):
            err_msg += f"\n{xmlschema.etree.etree_tostring(e.elem, e.namespaces, '', 5)}"

        assert False, err_msg
