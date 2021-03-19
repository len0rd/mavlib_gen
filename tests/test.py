import unittest, os, sys
import logging

logging.getLogger().setLevel(logging.CRITICAL)
scriptDir = os.path.dirname(__file__)
suite = unittest.TestLoader().discover(scriptDir, pattern="test_*.py")
results = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(not results.wasSuccessful())
