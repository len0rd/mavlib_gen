import unittest
from mavlib_gen.validator import *
import networkx as netx

TEST_CASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_cases'))

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
        other_defs = {
            mdefb.filename: mdefb,
            mdefc.filename: mdefc
        }
        self.assertEqual(MSG_DEF_DUPLICATE_ERR, self.validator.is_msg_def_unique(mdefa, other_defs))

    def test_msg_def_duplicate(self):
        mdefa = MessageDefXml('/test/path/common.xml', {})
        mdefb = MessageDefXml('/test/path2/asdf.xml', {})
        mdefc = MessageDefXml('/test/path/common.xml', {})
        other_defs = {
            mdefb.filename: mdefb,
            mdefc.filename: mdefc
        }
        self.assertEqual(MSG_DEF_DUPLICATE, self.validator.is_msg_def_unique(mdefa, other_defs))

    def test_msg_def_unique(self):
        mdefa = MessageDefXml('/test/path/common.xml', {})
        mdefb = MessageDefXml('/test/path/asdf.xml', {})
        mdefc = MessageDefXml('/test/path/ghjk.xml', {})
        other_defs = {
            mdefb.filename: mdefb,
            mdefc.filename: mdefc
        }
        self.assertEqual(MSG_DEF_UNIQUE, self.validator.is_msg_def_unique(mdefa, other_defs))

class TestValidatorExpandIncludes(unittest.TestCase):

    def setUp(self):
        self.validator = MavlinkXmlValidator()

    def setup_complex_tree_top_xmls(self):
        """setup the top-level xmls for the complex include tree tests"""
        files = ['top_level.xml', 'top_level2.xml']
        abs_files = [os.path.join(TEST_CASE_DIR, 'pass', 'complex_include_graph', fname) for fname in files]
        validated = [self.validator.validate_single_xml(fname) for fname in abs_files]
        self.validated_complex_xmls = dict(zip(files, validated))
        for fname, xml in self.validated_complex_xmls.items():
            self.assertIsNotNone(xml)
            self.assertEqual(fname, xml.filename)

    def test_invalid_include_path(self):
        """include path pointing to non-existent file should fail"""
        good_xml_path = os.path.join(TEST_CASE_DIR, 'fail', 'invalid_include.xml')
        good_xml = self.validator.validate_single_xml(good_xml_path)
        self.assertIsNotNone(good_xml)
        result = self.validator.expand_includes({good_xml.filename:good_xml})
        self.assertIsNone(result)

    def test_xml_with_no_include(self):
        """expand_includes should do nothing if xmls dont have include tags"""
        filename = 'no_includes.xml'
        includeless_xml_path = os.path.join(TEST_CASE_DIR, 'pass', filename)
        includeless_xml = self.validator.validate_single_xml(includeless_xml_path)
        self.assertIsNotNone(includeless_xml)
        xmls_in = {includeless_xml.filename: includeless_xml}
        result = self.validator.expand_includes(xmls_in)
        self.assertEqual(xmls_in, result[0])
        self.assertEqual(['no_includes.xml'], list(netx.topological_sort(result[1])))

    def test_complex_include_tree(self):
        """verify expand_includes successfully/properly parses the complex include graph"""
        # used to verify the generated include graph (in this case successors are xmls DIRECTLY included by the key)
        expected_successors = {
            'top_level.xml': ['m1.xml', 'm2.xml', 'm3.xml', 'm5.xml'],
            'top_level2.xml': ['m5.xml'],
            'm1.xml': ['m4.xml'],
            'm2.xml': ['m4.xml'],
            'm3.xml': ['r1.xml', 'r2.xml'],
            'm4.xml': ['r2.xml'],
            'm5.xml': ['r1.xml', 'm2.xml'],
            'r1.xml': [],
            'r2.xml': [],
        }
        self.setup_complex_tree_top_xmls()

        result = self.validator.expand_includes(self.validated_complex_xmls)
        self.assertIsNotNone(result)
        expanded_xmls = result[0]
        include_graph = result[1]
        self.assertTrue(netx.is_directed_acyclic_graph(include_graph))
        all_nodes = list(netx.topological_sort(include_graph))
        self.assertEqual(len(all_nodes), len(list(expected_successors.keys())))

        for node in all_nodes:
            self.assertIn(node, expected_successors)
            self.assertEqual(sorted(expected_successors[node]), sorted(list(include_graph.successors(node))))

    def test_generate_dependency_list_complex_tree(self):
        """verify generate_dependency_list produces accurate results for a complex tree"""
        expected_dep_lists = {
            'top_level.xml': ['m1.xml', 'm2.xml', 'm3.xml', 'm4.xml', 'm5.xml', 'r1.xml', 'r2.xml'],
            'top_level2.xml': ['m2.xml', 'm4.xml', 'm5.xml', 'r1.xml', 'r2.xml'],
            'm1.xml': ['m4.xml', 'r2.xml'],
            'm2.xml': ['m4.xml', 'r2.xml'],
            'm3.xml': ['r1.xml', 'r2.xml'],
            'm4.xml': ['r2.xml'],
            'm5.xml': ['m2.xml', 'm4.xml', 'r1.xml', 'r2.xml'],
            'r1.xml': [],
            'r2.xml': [],
        }
        self.setup_complex_tree_top_xmls()
        result = self.validator.expand_includes(self.validated_complex_xmls)
        self.assertIsNotNone(result)
        expanded_xmls = result[0]
        include_graph = result[1]

        self.validator.generate_dependency_list(expanded_xmls, include_graph)

        for fname, xml in expanded_xmls.items():
            self.assertIn(fname, expected_dep_lists)
            self.assertEqual(sorted(expected_dep_lists[fname]), sorted(xml.dependencies))

class TestValidatorGenerateDependencyList(unittest.TestCase):

    def setUp(self):
        self.validator = MavlinkXmlValidator()

class TestUniqueMsgIdNameAcrossDependencies(unittest.TestCase):

    def setUp(self):
        self.xml_validator = MavlinkXmlValidator()
        self.msg_id_name_validator = UniqueMsgIdNameAcrossDependencies()

    def setup_complex_tree_top_xmls(self):
        """setup the top-level xmls for a complex include tree test"""
        files = ['top_level.xml', 'top_level2.xml']
        abs_files = [os.path.join(TEST_CASE_DIR, 'pass', 'complex_include_graph', fname) for fname in files]
        validated = [self.xml_validator.validate_single_xml(fname) for fname in abs_files]
        validated_complex_xmls = dict(zip(files, validated))
        result = self.xml_validator.expand_includes(validated_complex_xmls)
        self.assertIsNotNone(result)
        self.complex_expanded_xmls = result[0]
        self.complex_include_graph = result[1]
        self.xml_validator.generate_dependency_list(self.complex_expanded_xmls, self.complex_include_graph)

    def test_empty_dict(self):
        self.assertTrue(self.msg_id_name_validator.validate({}, netx.DiGraph()))

    def test_single_xml(self):
        mdef = self.xml_validator.validate_single_xml(os.path.join(TEST_CASE_DIR, 'pass', 'no_includes.xml'))
        self.assertIsNotNone(mdef)
        self.assertTrue(self.msg_id_name_validator.validate({mdef.filename: mdef}, netx.DiGraph()))

    def test_few_messages(self):
        """Verify returns True with the complex_include_graph example that only has a couple messages"""
        self.setup_complex_tree_top_xmls()
        self.assertTrue(self.msg_id_name_validator.validate(self.complex_expanded_xmls, self.complex_include_graph))

    def test_conflicting_ids(self):
        """verify returns False when a msg id conflicts"""
        top_xml = self.xml_validator.validate_single_xml(
            os.path.join(TEST_CASE_DIR, 'fail', 'include_with_conflicting_msgid', 'top.xml'))
        self.assertIsNotNone(top_xml)

        result = self.xml_validator.expand_includes({top_xml.filename: top_xml})
        self.assertIsNotNone(result)
        self.xml_validator.generate_dependency_list(result[0], result[1])
        self.assertFalse(self.msg_id_name_validator.validate(result[0], result[1]))

    def test_conflicting_names(self):
        """verify returns False when a msg name conflicts"""
        top_xml = self.xml_validator.validate_single_xml(
            os.path.join(TEST_CASE_DIR, 'fail', 'include_with_conflicting_msgname', 'top.xml'))
        self.assertIsNotNone(top_xml)
        result = self.xml_validator.expand_includes({top_xml.filename: top_xml})
        self.assertIsNotNone(result)
        self.xml_validator.generate_dependency_list(result[0], result[1])
        self.assertFalse(self.msg_id_name_validator.validate(result[0], result[1]))


if __name__ == "__main__":
    unittest.main()
