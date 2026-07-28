import unittest
from pathlib import Path

from router_oqc.parser import normalize_mac, parse_status_html


class ParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = Path("tests/fixtures/status_sample.html").read_text(encoding="utf-8")

    def test_main_fields(self):
        result = parse_status_html(self.html)
        self.assertEqual(result.system["Device Name"], "GRG-4297u")
        self.assertEqual(result.system["Serial Number"], "2654297UF-AA000028")
        self.assertEqual(result.system["CPU Usage"], "3%")
        self.assertEqual(result.system["Memory Usage"], "41%")
        self.assertEqual(result.lan["MAC Address"], "1C:64:99:AF:B4:9D")

    def test_malformed_wan_rows_recovered(self):
        result = parse_status_html(self.html)
        self.assertEqual(len(result.wan), 2)
        self.assertEqual(result.wan[1]["Interface"], "nas0_1")
        self.assertEqual(result.wan[1]["VLAN ID"], "3998")

    def test_mac_normalization(self):
        self.assertEqual(normalize_mac("1c-64-99-af-b4-9d"), "1C:64:99:AF:B4:9D")


if __name__ == "__main__":
    unittest.main()
