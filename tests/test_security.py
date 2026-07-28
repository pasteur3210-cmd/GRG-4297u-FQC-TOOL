import unittest

from router_oqc.security import (
    calculate_post_security_flag,
    create_login_values,
    build_login_checksum_input,
)


class SecurityTests(unittest.TestCase):
    def test_known_browser_payload_flag(self):
        encoded = "VGZ0aklpeGUyRjk1STl2eFREMzU="
        input_value = build_login_checksum_input("admin", encoded)
        self.assertEqual(calculate_post_security_flag(input_value), 22879)

    def test_password_changes_flag(self):
        a = create_login_values("admin", "password-A")
        b = create_login_values("admin", "password-B")
        self.assertNotEqual(a[1], b[1])


if __name__ == "__main__":
    unittest.main()
