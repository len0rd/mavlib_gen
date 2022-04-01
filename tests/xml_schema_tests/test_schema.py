import os
import xmlschema
import pytest

script_dir = os.path.dirname(__file__)
mav_schema_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "mavlib_gen", "schema"))
schema = xmlschema.XMLSchema11(
    os.path.join(mav_schema_dir, "mavlink_schema.xsd"), base_url=mav_schema_dir
)

failure_test_case_dir = os.path.join(script_dir, "test_cases", "fail")
schema_failure_files = [
    f
    for f in os.listdir(failure_test_case_dir)
    if os.path.isfile(os.path.join(failure_test_case_dir, f))
]

success_test_case_dir = os.path.join(script_dir, "test_cases", "pass")
schema_success_files = [
    f
    for f in os.listdir(success_test_case_dir)
    if os.path.isfile(os.path.join(success_test_case_dir, f))
]


@pytest.mark.parametrize("filename", schema_failure_files)
def test_failure_cases(filename):
    test_file = os.path.join(failure_test_case_dir, filename)
    assert not schema.is_valid(
        test_file
    ), f"Test case file '{filename}' passed schema validation when it should have failed"


@pytest.mark.parametrize("filename", schema_success_files)
def test_success_cases(filename):
    test_file = os.path.join(success_test_case_dir, filename)
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
