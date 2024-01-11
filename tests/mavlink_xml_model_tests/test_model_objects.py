################################################################################
# \file test_model_objects
#
# Unit tests for the mavlink xml model objects
#
# Copyright (c) 2021 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import sys
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, script_dir.parent.parent)

from mavlib_gen.validator import *
import xmlschema

TEST_CASE_DIR = script_dir / "test_cases"
mav_schema_dir = script_dir.parent.parent / "mavlib_gen" / "schema"
schema = xmlschema.XMLSchema11(mav_schema_dir / "mavlink_schema.xsd", base_url=mav_schema_dir)


def test_enum_import():
    """Verify enum values are properly imported into model objects"""
    xml_to_test = "simple_enum.xml"
    validator = MavlinkXmlValidator()
    simple_enum_xml = TEST_CASE_DIR / xml_to_test
    enumXmlTruth = schema.to_dict(simple_enum_xml)
    modelObjs = validator.validate([simple_enum_xml])
    assert modelObjs is not None

    mavXml = modelObjs.get(xml_to_test)
    assert mavXml is not None
    mavXml = mavXml.xml
    assert len(enumXmlTruth["enums"]["enum"]) == len(mavXml.enums)

    # verify each enum in the xml
    for enum in mavXml.enums:
        truthEnum = None
        for eTruth in enumXmlTruth["enums"]["enum"]:
            if enum.name == eTruth["@name"]:
                truthEnum = eTruth
                break
        assert truthEnum is not None
        assert truthEnum["description"] == enum.description
        assert len(truthEnum["entry"]) == len(enum.entries)
        # for each enum verify all its values
        for entry in enum.entries:
            truthEntry = None
            for eTruth in truthEnum["entry"]:
                if entry.name == eTruth["@name"]:
                    truthEntry = eTruth
                    break
            assert truthEntry is not None
            assert truthEntry["description"] == entry.description
            assert truthEntry["@value"] == entry.value

            # check all param values if present
            if "param" in truthEntry:
                assert len(truthEntry["param"]) == len(entry.params)
                for param in entry.params:
                    truthParam = None
                    for pTruth in truthEntry["param"]:
                        if param.index == pTruth["@index"]:
                            truthParam = pTruth
                            break
                    assert truthParam is not None
                    assert truthParam["$"] == param.description
