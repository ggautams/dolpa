import unittest

from src.dolpa.dolpa_utils import interpolate


class TestUtils(unittest.TestCase):

    def setUp(self) -> None:
        self.test_config = {
            "value-1": "test-value-1",
            "value-2": "test-value-2"
        }

        self.test_call = {
            "identifier": 1,
            "description": "login_endpoint",
            "resource": "/login",
            "method": "POST",
            "body": {
                "currentUser": "alex.martin",
                "currentState": "healthy",
                "value-1": "{{value-1}}"
            },
            "headers": {
                "app-status": "current"
            },
            "saves": {
                "authToken": "$.auth_token"
            },
            "assertions": {
                "responseCheckAssertion": "responseSent==yes"
            }
        }

    def test_interpolate(self):
        interpolated = interpolate(self.test_call, self.test_config)
        self.assertEqual(interpolated['body']['value-1'], 'test-value-1')

