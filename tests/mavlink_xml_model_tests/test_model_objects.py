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
import unittest, os
from mavlib_gen.validator import *
import xmlschema

TEST_CASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_cases'))

class TestModelObject(unittest.TestCase):
    """Verify XMLs are imported into the model objects properly"""


    def setUp(self):
        self.validator = MavlinkXmlValidator()
        self.script_dir = os.path.dirname(__file__)
        base_url = os.path.abspath(os.path.join(self.script_dir, '..', '..', 'mavlib_gen', 'schema'))
        self.schema = xmlschema.XMLSchema11(os.path.join(base_url, 'mavlink_schema.xsd'), base_url=base_url)

    def test_simple_enum(self):
        xml_to_test = 'simple_enum.xml'
        simple_enum_xml = os.path.join(TEST_CASE_DIR, xml_to_test)
        enumXmlTruth = self.schema.to_dict(simple_enum_xml)
        modelObjs = self.validator.validate([simple_enum_xml])
        self.assertIsNotNone(modelObjs)

        mavXml = modelObjs.get(xml_to_test)
        self.assertIsNotNone(mavXml)
        mavXml = mavXml.xml
        self.assertEqual(len(enumXmlTruth['enums']['enum']), len(mavXml.enums))

        # verify each enum in the xml
        for enum in mavXml.enums:
            truthEnum = None
            for eTruth in enumXmlTruth['enums']['enum']:
                if enum.name == eTruth['@name']:
                    truthEnum = eTruth
                    break
            self.assertIsNotNone(truthEnum)
            self.assertEqual(truthEnum['description'], enum.description)
            self.assertEqual(len(truthEnum['entry']), len(enum.entries))
            # for each enum verify all its values
            for entry in enum.entries:
                truthEntry = None
                for eTruth in truthEnum['entry']:
                    if entry.name == eTruth['@name']:
                        truthEntry = eTruth
                        break
                self.assertIsNotNone(truthEntry)
                self.assertEqual(truthEntry['description'], entry.description)
                self.assertEqual(truthEntry['@value'], entry.value)

                # check all param values if present
                if 'param' in truthEntry:
                    self.assertEqual(len(truthEntry['param']), len(entry.params))
                    for param in entry.params:
                        truthParam = None
                        for pTruth in truthEntry['param']:
                            if param.index == pTruth['@index']:
                                truthParam = pTruth
                                break
                        self.assertIsNotNone(truthParam)
                        self.assertEqual(truthParam['$'], param.description)
