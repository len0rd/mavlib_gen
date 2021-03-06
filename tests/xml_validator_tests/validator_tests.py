import unittest, os
import xmlschema

class TestXmlSchemaValidator(unittest.TestCase):

    def test_failure_cases(self):
        """Test cases where we expect the schema validator to produce and error"""
        script_dir = os.path.dirname(__file__)
        base_url = os.path.abspath(os.path.join(script_dir, '..', '..', 'leo_mavgen', 'schema'))
        schema = xmlschema.XMLSchema11(os.path.join(base_url, 'mavlink_schema.xsd'), base_url=base_url)

        # schema.validate(os.path.join(script_dir, 'test_cases', 'fail', 'bad_name_2.xml'))
        self.assertFalse(schema.is_valid(os.path.join(script_dir, 'test_cases', 'fail', 'bad_name_2.xml')))
