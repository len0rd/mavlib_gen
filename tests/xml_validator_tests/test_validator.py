import unittest
from mavlib_gen.validator import *

class TestValidateSingleXml(unittest.TestCase):

    def setUp(self):
        self.validator = MavlinkXmlValidator()

    def test_bad_filename(self):
        """Non-existent xml file should fail"""
        self.assertIsNone(self.validator.validate_single_xml("bogus/file.xml"))

    def test_msg_def_duplicate_err(self):
        mdefa = MessageDefXml('/test/path1/common.xml', {})
        mdefb = MessageDefXml('/test/path2/asdf.xml', {})
        mdefc = MessageDefXml('/test/path2/common.xml', {})
        self.assertEqual(MSG_DEF_DUPLICATE_ERR, self.validator.is_msg_def_unique(mdefa, [mdefb, mdefc]))

    def test_msg_def_duplicate(self):
        mdefa = MessageDefXml('/test/path/common.xml', {})
        mdefb = MessageDefXml('/test/path2/asdf.xml', {})
        mdefc = MessageDefXml('/test/path/common.xml', {})
        self.assertEqual(MSG_DEF_DUPLICATE, self.validator.is_msg_def_unique(mdefa, [mdefb, mdefc]))

    def test_msg_def_unique(self):
        mdefa = MessageDefXml('/test/path/common.xml', {})
        mdefb = MessageDefXml('/test/path/asdf.xml', {})
        mdefc = MessageDefXml('/test/path/ghjk.xml', {})
        self.assertEqual(MSG_DEF_UNIQUE, self.validator.is_msg_def_unique(mdefa, [mdefb, mdefc]))
