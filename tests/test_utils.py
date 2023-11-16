import unittest

from src.dolpa.dolpa_utils import interpolate, get_dict_value_from_json_path


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
                "value-1": "{{value-1}}",
                "sampleArray": [
                    {"arr1": [1, 2, 3], "arr2": [4, 5, 6]},
                    {"arr3": [7, 8, 9], "arr4": [10, 11, 12]}
                ]
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

    def test_get_dict_value_from_json_path(self):
        actual_value = get_dict_value_from_json_path(self.test_call, 'body.sampleArray[1].arr3[2]')
        self.assertEqual(actual_value, 9)
