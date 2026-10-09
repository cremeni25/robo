import unittest
from pathlib import Path

class DiscoveryTests(unittest.TestCase):
    def test_discovery_script_exists(self):
        self.assertTrue((Path(__file__).resolve().parents[1] / 'scripts' / 'awin_discover.py').is_file())

if __name__ == '__main__':
    unittest.main()
