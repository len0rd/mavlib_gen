import unittest, os
import xmlschema

class TestXmlSchemaValidator(unittest.TestCase):

    def setUp(self):
        self.script_dir = os.path.dirname(__file__)
        base_url = os.path.abspath(os.path.join(self.script_dir, '..', '..', 'mavlib_gen', 'schema'))
        self.schema = xmlschema.XMLSchema11(os.path.join(base_url, 'mavlink_schema.xsd'), base_url=base_url)

    def test_failure_cases(self):
        """Test cases where the schema validator should produce an error"""
        test_case_dir = os.path.join(self.script_dir, 'test_cases', 'fail')
        test_case_files = [f for f in os.listdir(test_case_dir) if os.path.isfile(os.path.join(test_case_dir, f))]

        for test_file in test_case_files:
            test_file = os.path.join(test_case_dir, test_file)
            if self.schema.is_valid(test_file):
                # schema validation should fail
                self.fail('Test case file "{}" passed schema validation when it should have failed!'.format(test_file))

    def test_successful_cases(self):
        """Test cases where the schema validator should succeed"""
        test_case_dir = os.path.join(self.script_dir, 'test_cases', 'pass')
        test_case_files = [f for f in os.listdir(test_case_dir) if os.path.isfile(os.path.join(test_case_dir, f))]

        for test_file in test_case_files:
            test_file = os.path.join(test_case_dir, test_file)
            if not self.schema.is_valid(test_file):
                try:
                    self.schema.validate(test_file)
                except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
                    print("Validation of message definition file '{}' failed!".format(os.path.relpath(test_file)))
                    reason = ""
                    if e.reason is not None:
                        reason += "Reason: {}".format(e.reason)
                    if e.path is not None:
                        reason += " At path '{}':".format(e.path)
                    print(reason)
                    if xmlschema.etree.is_etree_element(e.elem):
                        print("\n{}".format(xmlschema.etree.etree_tostring(e.elem, e.namespaces, '', 5)))
                # schema validation should pass
                self.fail('Test case file "{}" failed schema validation when it should have passed!'.format(test_file))
