import unittest
from mavlib_gen.lang_generators.generator_c import CLangGenerator
from mavlib_gen.validator import *
import os

class TestCLangGenerator(unittest.TestCase):

    def setUp(self):
        self.validator = MavlinkXmlValidator()
        self.cgen = CLangGenerator()

    def test(self):
        simple_xml = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'simple_msg.xml'))
        result = self.validator.validate([simple_xml])
        self.assertIsNotNone(result)

        gen_result = self.cgen.generate(result, os.path.dirname(__file__))
        self.assertTrue(gen_result)


if __name__ == "__main__":
    unittest.main()