
import unittest
from router_oqc.client import RouterClient


class LegacyTransportTests(unittest.TestCase):
    def test_bad_status_line_detection(self):
        exc = RuntimeError("ProtocolError: BadStatusLine('<HTML>')")
        self.assertTrue(RouterClient._is_bad_status_line(exc))

    def test_normal_connection_error_not_misclassified(self):
        exc = RuntimeError("Connection refused")
        self.assertFalse(RouterClient._is_bad_status_line(exc))


if __name__ == "__main__":
    unittest.main()
