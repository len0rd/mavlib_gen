import unittest, os, sys

scriptDir = os.path.dirname(__file__)
suite = unittest.TestLoader().discover(scriptDir, pattern="test_*.py")
results = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not results.wasSuccessful())
