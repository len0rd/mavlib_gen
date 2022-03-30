import unittest, os, sys
import logging


def run_all_tests() -> int:
    """
    Returns result of running all unit tests
    """
    scriptDir = os.path.dirname(__file__)
    suite = unittest.TestLoader().discover(scriptDir, pattern="test_*.py")
    results = unittest.TextTestRunner(verbosity=1).run(suite)
    return not results.wasSuccessful()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.CRITICAL)
    sys.exit(run_all_tests())
