import os
import json

import requests
from requests.auth import HTTPDigestAuth
from .dolpa_utils import interpolate, get_dict_value_from_json_path
from .dolpa_logger import get_logger
from .comparator import Comparator
from .exceptions import (InValidCallAttributeError, InValidCallAttributeModifierError,
                         AuthTypeNotSupportedError, NoResponseDataError, FailedAssertion)

LOGGER = get_logger()


class EndpointCall:
    allowed_keys = {'identifier', 'description', 'resource', 'method', 'body', 'headers', 'saves', 'assertions', 'auth'}
    allowed_modifiers = {'replace', 'merge'}

    def __init__(self, call):
        self._validate(call)
        self.identifier = call.get('identifier')
        self.description = call.get('description')
        self.resource = call['resource']
        self.method = call['method']
        self.body = call.get('body')
        self.headers = None
        self.header_strategy = None
        self.saves = call.get('saves')
        self.assertions = call.get('assertions')
        self.auth = call.get('auth')
        self.abort_if_assertion_fails = call.get('abortIfAssertionFails')
        self._response = None
        self._populate_headers_and_headers_strategy(call)

    def _validate(self, call):
        keys_set = {key if ':' not in key else key.split(':')[0] for key in call.keys()}
        modifier_set = {key.split(':')[1] for key in call.keys() if ':' in key}
        if not set(modifier_set).issubset(self.allowed_modifiers):
            invalid_modifiers = set(modifier_set) - (modifier_set.intersection(self.allowed_modifiers))
            raise InValidCallAttributeModifierError(f'{invalid_modifiers} not allowed. Fix your JSON file')
        if not set(keys_set).issubset(self.allowed_keys):
            invalid_attrs = set(keys_set) - (set(keys_set).intersection(self.allowed_keys))
            raise InValidCallAttributeError(f'{invalid_attrs} not allowed. Fix your JSON file.')

    def _populate_headers_and_headers_strategy(self, call):
        possible_headers_key = ['headers'] + ['headers' + ':' + mod for mod in self.allowed_modifiers]
        header_with_strategy = list(filter(lambda key: key in possible_headers_key, call.keys()))[0]
        if ':' in header_with_strategy:
            self.headers, self.header_strategy = call[header_with_strategy], header_with_strategy.split(':')[-1]
        else:
            self.headers, self.header_strategy = call[header_with_strategy], None

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, http_response):
        self._response = http_response


class APITests:
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
        self._app_env_indicator = 'dolpa_'

    def _load_into_config_from_env(self):
        env_variables = os.environ
        for var_name, var_value in env_variables.items():
            if var_name.startswith(self._app_env_indicator):
                self.run_config[var_name] = var_value

    def _combine_global_with_local(self, key, local_map, strategy=None):
        strategy = strategy or 'merge'
        if self.run_config.get(key):
            if local_map and isinstance(local_map, dict):
                if strategy == 'merge':
                    return {**self.run_config[key], **local_map}
                if strategy == 'replace':
                    return local_map
            else:
                return {**self.run_config[key]}
        return local_map

    def _get_auth(self, call_auth_settings_dict=None):
        if call_auth_settings_dict:
            local_auth = interpolate(call_auth_settings_dict, self.run_config)
            auth_type = local_auth['auth']
        else:
            local_auth = {}
            auth_type = self.run_config.get('auth')
        if not auth_type:
            return None
        if auth_type.lower() not in ['basic', 'digest']:
            AuthTypeNotSupportedError(f'{auth_type} - auth mechanism is not supported.')
        username = local_auth.get('username') or self.run_config['dolpa_username']
        password = local_auth.get('password') or self.run_config['dolpa_password']
        if auth_type.lower() == 'basic':
            return username, password
        if self.run_config['auth'].lower() == 'digest':
            return HTTPDigestAuth(username, password)
        return None

    def _call_execute(self, call: EndpointCall):
        endpoint = self.run_config['base_url'] + call.resource if call.resource.startswith('/') else call.resource
        endpoint = interpolate(endpoint, self.run_config)
        headers = self._combine_global_with_local('headers', call.headers, call.header_strategy)
        requests_func = self.call_method_to_req_method_mapping[call.method.upper()]
        LOGGER.info(f'Making {call.method.upper()} request to the endpoint: {endpoint}')
        response = requests_func(
            endpoint,
            json=interpolate(call.body, self.run_config),
            headers=headers,
            auth=self._get_auth(call.auth),
        )
        LOGGER.info(f'{endpoint} responded with status code: {response.status_code}')
        json_res = response.json()
        for key, val in call.saves.items():
            self.run_config[key] = get_dict_value_from_json_path(json_res, val[2:]) if val.startswith("$.") else val
        call.response = response
        return call

    def do_call_assertions(self, call: EndpointCall):
        if not call.response:
            raise NoResponseDataError(f'The call do not have response set. Probably it\'s not yet called.')
        response_json = call.response.json()
        should_fail_if_assertion_fails = True
        if call.abort_if_assertion_fails is None:
            global_abort_state = self.run_config.get('abortIfAssertionFails')
            if global_abort_state is not None:
                should_fail_if_assertion_fails = global_abort_state
        for assertion_name, assertion in call.assertions.items():
            try:
                Comparator(assertion_name, assertion, self.run_config, response_json).execute()
            except FailedAssertion as e:
                if should_fail_if_assertion_fails:
                    raise e
                else:
                    LOGGER.warning(f"{assertion_name} which asserts {assertion} failed. Continuing...")

    def run_all(self, run_with_assertions=True):
        self._load_into_config_from_env()
        for call_dict in self.calls:
            endpoint_call = EndpointCall(call_dict)
            self._call_execute(endpoint_call)
            if run_with_assertions:
                self.do_call_assertions(endpoint_call)

    def run(self, call_identifier: int, run_with_assertions=False):
        self._load_into_config_from_env()
        call = [item for item in self.calls if item["identifier"] == call_identifier][0]
        endpoint_call = EndpointCall(call)
        self._call_execute(endpoint_call)
        if run_with_assertions:
            self.do_call_assertions(endpoint_call)
        return endpoint_call


def run_api_tests(folder_path):
    with open(folder_path, 'r') as read_file:
        int_test = APITests(json.load(read_file))
        int_test.run_all()


def run_bulk_api_tests(root_path):
    contents = sorted(os.listdir(root_path))
    for curr_path in contents:
        inner_path = (root_path + curr_path) if root_path.endswith('/') else (root_path + '/' + curr_path)
        if os.path.isdir(inner_path):
            run_bulk_api_tests(inner_path)
        else:
            if inner_path.endswith('.json'):
                with open(inner_path, 'r') as read_file:
                    int_test = APITests(json.load(read_file))
                    int_test.run_all()


def get_api_test_handler(file_path):
    with open(file_path, 'r') as read_file:
        int_test = APITests(json.load(read_file))
        return int_test
