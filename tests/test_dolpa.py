import os
import json
import unittest
from unittest import mock

from src.dolpa.dolpa import run_bulk_api_tests, APITests


class DolpaTest(unittest.TestCase):
    class MockedResponse:
        status_code = 200

        def __init__(self, mocked_json):
            self.mocked_json = mocked_json

        def json(self):
            return self.mocked_json

    def setUp(self) -> None:
        os.environ['dolpa_username'] = 'admin_user'
        os.environ['dolpa_password'] = 'strong_password'
        os.environ['dolpa_extra_username'] = 'extra_user'
        os.environ['dolpa_extra_password'] = 'strongest_password'
        mocked_responses_list = [
            {
                "auth_token": "xxxxxxxxxxxx",
                "responseSent": 'yes'
            },
            {
                'location': "Office",
                'isEmployed': True,
                'originState': 'GA',
                'currentDepartment': {
                    'currentBlock': 'secret',
                    'departmentInfo': {
                        'floor': 3,
                        'employees': ['Ram', 'Sam', 'Tammy']
                    }
                }
            },
            {
                "workingBlock": "secret",
                "friend": "Tammy"
            },
            {},
        ]
        self.mocked_response_objects = [self.MockedResponse(in_dict) for in_dict in mocked_responses_list]

    @mock.patch('src.dolpa.dolpa.APITests.call_method_to_req_method_mapping')
    def test_run_bulk_api_tests(self, mocked_requests_mapping):
        mocked_post = mock.Mock()
        mocked_post.side_effect = self.mocked_response_objects
        mocked_requests_mapping.__getitem__.side_effect = {'POST': mocked_post}.__getitem__
        run_bulk_api_tests(r'.')

    @mock.patch('src.dolpa.dolpa.APITests.do_call_assertions')
    @mock.patch('src.dolpa.dolpa.APITests._call_execute')
    @mock.patch('src.dolpa.dolpa.APITests.call_method_to_req_method_mapping')
    def test_api_tests_run_all_no_assert(self, mocked_requests_mapping, mocked_call_execute, mocked_asserter):
        mocked_post = mock.Mock()
        mocked_post.side_effect = self.mocked_response_objects
        mocked_requests_mapping.__getitem__.side_effect = {'POST': mocked_post}.__getitem__
        with open(r'test.json', 'r') as read_file:
            int_test = APITests(json.load(read_file))
            int_test.run_all(run_with_assertions=False)
            self.assertEqual(mocked_call_execute.call_count, 4)
            self.assertEqual(mocked_asserter.call_count, 0)

    @mock.patch('src.dolpa.dolpa.APITests.do_call_assertions')
    @mock.patch('src.dolpa.dolpa.APITests._call_execute')
    @mock.patch('src.dolpa.dolpa.APITests.call_method_to_req_method_mapping')
    def test_api_tests_run_all_assert(self, mocked_requests_mapping, mocked_call_execute, mocked_asserter):
        mocked_post = mock.Mock()
        mocked_post.side_effect = self.mocked_response_objects
        mocked_requests_mapping.__getitem__.side_effect = {'POST': mocked_post}.__getitem__
        with open(r'test.json', 'r') as read_file:
            int_test = APITests(json.load(read_file))
            int_test.run_all(run_with_assertions=True)
            self.assertEqual(mocked_call_execute.call_count, 4)
            self.assertEqual(mocked_asserter.call_count, 4)

    @mock.patch('src.dolpa.dolpa.Comparator')
    @mock.patch('src.dolpa.dolpa.APITests.call_method_to_req_method_mapping')
    def test_api_tests_do_call_assertions(self, mocked_requests_mapping, mocked_comparator):
        mocked_post = mock.Mock()
        mocked_post.side_effect = self.mocked_response_objects
        mocked_requests_mapping.__getitem__.side_effect = {'POST': mocked_post}.__getitem__
        with open(r'test.json', 'r') as read_file:
            int_test = APITests(json.load(read_file))
            endpoint_call = int_test.run(1)
            int_test.do_call_assertions(endpoint_call)
            self.assertEqual(mocked_comparator.call_count, 1)

    @mock.patch('src.dolpa.dolpa.APITests.do_call_assertions')
    @mock.patch('src.dolpa.dolpa.APITests._call_execute')
    @mock.patch('src.dolpa.dolpa.APITests.call_method_to_req_method_mapping')
    def test_api_tests_run_no_assert(self, mocked_requests_mapping, mocked_call_execute, mocked_asserter):
        mocked_post = mock.Mock()
        mocked_post.side_effect = self.mocked_response_objects
        mocked_requests_mapping.__getitem__.side_effect = {'POST': mocked_post}.__getitem__
        with open(r'test.json', 'r') as read_file:
            int_test = APITests(json.load(read_file))
            int_test.run(1, run_with_assertions=False)
            self.assertEqual(1, mocked_call_execute.call_count)
            self.assertEqual(0, mocked_asserter.call_count)

    @mock.patch('src.dolpa.dolpa.APITests.do_call_assertions')
    @mock.patch('src.dolpa.dolpa.APITests._call_execute')
    @mock.patch('src.dolpa.dolpa.APITests.call_method_to_req_method_mapping')
    def test_api_tests_run_assert(self, mocked_requests_mapping, mocked_call_execute, mocked_asserter):
        mocked_post = mock.Mock()
        mocked_post.side_effect = self.mocked_response_objects
        mocked_requests_mapping.__getitem__.side_effect = {'POST': mocked_post}.__getitem__
        with open(r'test.json', 'r') as read_file:
            int_test = APITests(json.load(read_file))
            int_test.run(1, run_with_assertions=True)
            self.assertEqual(1, mocked_call_execute.call_count)
            self.assertEqual(1, mocked_asserter.call_count)
