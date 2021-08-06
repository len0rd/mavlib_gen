import unittest
from mavlib_gen.lang_generators.generator_c import CLangGenerator
from mavlib_gen.validator import *
import os

class TestCLangGenerator(unittest.TestCase):

    def setUp(self):
        self.validator = MavlinkXmlValidator()
        self.cgen = CLangGenerator()
        self.base_output_dir = os.path.join(os.path.dirname(__file__), '..', 'test_outputs')

    def test(self):
        simple_xml = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_cases', 'simple_msg.xml'))
        result = self.validator.validate([simple_xml])
        self.assertIsNotNone(result)


        testName = self.id()
        testName = testName.split('.')
        out_dir = os.path.join(self.base_output_dir, *testName)
        os.makedirs(out_dir)

        gen_result = self.cgen.generate(result, out_dir)
        self.assertTrue(gen_result)


if __name__ == "__main__":
    unittest.main()
