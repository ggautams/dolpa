import os
import json

import requests
from requests.auth import HTTPDigestAuth
from dolpa_utils import interpolate, get_dict_value_from_json_path
from dolpa_logger import get_logger
from comparator import Comparator
from exceptions import InValidCallAttributeError


LOGGER = get_logger()


class EndpointCall:
    allowed_keys = {'identifier', 'description', 'resource', 'method', 'body', 'headers', 'saves', 'assertions'}

    def __init__(self, call):
        self._validate(call)
        self.identifier = call.get('identifier')
        self.description = call.get('description')
        self.resource = call['resource']
        self.method = call['method']
        self.body = call.get('body')
        self.headers = call.get('headers')
        self.saves = call.get('saves')
        self.assertions = call.get('assertions')
        self._response = None

    def _validate(self, call):
        if not set(call.keys()).issubset(self.allowed_keys):
            invalid_attrs = set(call.keys()) - (set(call.keys()).intersection(self.allowed_keys))
            raise InValidCallAttributeError(f'{invalid_attrs} not allowed. Fix your JSON file.')

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, http_response):
        self._response = http_response


class IntegrationTests:

    call_method_to_req_method_mapping = {
        'GET': requests.get,
        'POST': requests.post,
        'PUT': requests.put,
        'DELETE': requests.delete,
        'HEAD': requests.head,
        'OPTIONS': requests.options,
        'PATCH': requests.patch,
    }

    def __init__(self, runner_dict):
        self.response_store = []
        self.run_config = runner_dict['config']
        self.calls = runner_dict['calls']
        self._env_var_names = ['dolpa_username', 'dolpa_password', 'dolpa_auth_token', 'dolpa_environment']

    def _load_into_config_from_env(self):
        for var_name in self._env_var_names:
            env_value = os.getenv(var_name)
            if env_value:
                self.run_config[var_name] = env_value

    def _combine_global_with_local(self, key, local_map):
        if self.run_config.get(key):
            if local_map and isinstance(local_map, dict):
                return {**self.run_config[key], **local_map}
            else:
                return {**self.run_config[key]}

    def _get_auth(self):
        auth_type = self.run_config.get('auth')
        if not auth_type:
            return None
        if self.run_config['auth'].lower() == 'basic':
            return self.run_config['dolpa_username'], self.run_config['dolpa_password']
        if self.run_config['auth'].lower() == 'digest':
            return HTTPDigestAuth(self.run_config['dolpa_username'], self.run_config['dolpa_password'])
        return None

    def _call_execute(self, call):
        endpoint = self.run_config['base_url'] + call.resource if call.resource.startswith('/') else call.resource
        headers = self._combine_global_with_local('headers', call.headers)
        requests_func = self.call_method_to_req_method_mapping[call.method.upper()]
        response = requests_func(
            endpoint,
            json=interpolate(call.body, self.run_config),
            headers=headers,
            auth=self._get_auth(),
        )
        json_res = response.json()
        for key, val in call.saves.items():
            self.run_config[key] = get_dict_value_from_json_path(json_res, val[2:]) if val.startswith("$.") else val
        for assertion_name, assertion in call.assertions.items():
            Comparator(assertion_name, assertion, self.run_config, json_res).execute()
        return response

    def run_all(self):
        self._load_into_config_from_env()
        for call_dict in self.calls:
            endpoint_call = EndpointCall(call_dict)
            endpoint_call.response = self._call_execute(endpoint_call)

    def run(self, call_identifier):
        self._load_into_config_from_env()
        call = [item for item in self.calls if item["identifier"] == call_identifier][0]
        endpoint_call = EndpointCall(call)
        endpoint_call.response = self._call_execute(endpoint_call)
        return endpoint_call


def run_integration_tests(folder_path):
    with open(folder_path, 'r') as read_file:
        int_test = IntegrationTests(json.load(read_file))
        int_test.run_all()


def run_bulk_integration_tests(root_path):
    contents = sorted(os.listdir(root_path))
    for curr_path in contents:
        inner_path = (root_path + curr_path) if root_path.endswith('/') else (root_path + '/' + curr_path)
        if os.path.isdir(inner_path):
            run_bulk_integration_tests(inner_path)
        else:
            if inner_path.endswith('.json'):
                with open(inner_path, 'r') as read_file:
                    int_test = IntegrationTests(json.load(read_file))
                    int_test.run_all()


def get_integration_test_handler(file_path):
    with open(file_path, 'r') as read_file:
        int_test = IntegrationTests(json.load(read_file))
        return int_test

if __name__ == "__main__":
    run_bulk_integration_tests(r'/Users/ggautam/PycharmProjects/dolpa/tests')