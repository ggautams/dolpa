import re
from itertools import product
from .dolpa_logger import get_logger
from .exceptions import AttributeNotFoundError


LOGGER = get_logger()


def get_dict_value_from_json_path(search_dict, json_path):
    try:
        if '.' not in json_path:
            stripped_key = json_path.strip()
            if len(stripped_key) < len(json_path):
                LOGGER.warning(f"Removing extra spaces when using the key {stripped_key}. Correct your Json file...")
            return search_dict[stripped_key]
        path_tokens = json_path.split('.')
        current_value = search_dict
        for token in path_tokens:
            if '[' in token:
                assert ']' in token
                path_token, index = token.split('[')
                index = index[:-1]
                current_value = current_value[path_token][int(index)]
            else:
                current_value = current_value[token]
        return current_value
    except (IndexError, ValueError):
        raise AttributeNotFoundError(f'The value {json_path} not found in {search_dict}')


def get_all_lookouts(json_path, lower_limit=0, upper_limit=100):
    expansion_stack = []
    for index, char in enumerate(json_path):
        if char == '[':
            end_index = json_path.index(']', index)
            current_range = json_path[index+1:end_index]
            if ':' in current_range:
                start, end = [int(item) for item in current_range.split(":")]
                expansion_stack.append(list(range(start, end)))
            else:
                if current_range == '*':
                    expansion_stack.append(list(range(lower_limit, upper_limit)))
                else:
                    expansion_stack.append([int(current_range)])
    possible_lookouts_index_tuples = list(product(*expansion_stack))
    all_possible_lookouts = []
    for lookout in possible_lookouts_index_tuples:
        wild_path = json_path
        for pos in lookout:
            wild_path = wild_path.replace(re.compile('[.*]'), '[pos]')
        all_possible_lookouts.append(wild_path)
    return all_possible_lookouts


def do_dict_interpolation(call: dict, run_config):

    def convert_string_to_value(raw_value):
        if not raw_value.strip().startswith("{{"):
            return raw_value
        variable_name = raw_value.strip()[2:-2].strip()
        return run_config[variable_name]

    if len(call) == 0:
        return {}

    interpolated_dict = {}
    for key, value in call.items():
        if isinstance(value, str):
            interpolated_dict[key] = convert_string_to_value(value)
        elif isinstance(value, list):
            interpolated_list = []
            for list_item in value:
                if isinstance(list_item, str):
                    interpolated_list.append(convert_string_to_value(list_item))
                elif isinstance(list_item, dict):
                    dict_interpolated = do_dict_interpolation(list_item, run_config)
                    interpolated_list.append(dict_interpolated)
                elif isinstance(list_item, list):
                    dict_interpolated = do_dict_interpolation({'placeholder': list_item}, run_config)
                    interpolated_list.append(dict_interpolated['placeholder'])
        elif isinstance(value, dict):
            dict_interpolated = do_dict_interpolation(value, run_config)
            interpolated_dict[key] = dict_interpolated
    return interpolated_dict


def do_string_interpolation(raw_string, run_config):
    if '{{' not in raw_string:
        return raw_string
    interpolated_string = raw_string
    pattern = r'\{\{.*?\}\}'
    matches = re.finditer(pattern, raw_string)
    for match in matches:
        matched_text = match.group()
        actual_value = get_dict_value_from_json_path(run_config, match.group().strip()[2:-2].strip())
        interpolated_string = interpolated_string.replace(matched_text, actual_value, 1)
    return interpolated_string


def interpolate(target, run_config):
    if isinstance(target, str):
        stripped_key = target.strip()
        if len(stripped_key) < len(target):
            LOGGER.warning(f"Removing extra spaces when using the key {stripped_key}. Correct your Json file...")
        return do_string_interpolation(target, run_config)
    if isinstance(target, dict):
        return do_dict_interpolation(target, run_config)
