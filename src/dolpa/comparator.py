from .dolpa_utils import interpolate, get_dict_value_from_json_path
from .exceptions import FailedAssertion, NotAllowedComparison
from .dolpa_logger import get_logger

LOGGER = get_logger()


class Comparator:
    def __init__(self, assertion_name, assertion, run_config, response):
        self.assertion_name = assertion_name
        self.assertion = assertion
        self.run_config = run_config
        self.response = response
        self.allowed_comparators = ["==", "<=", ">=", "!=", "<", ">"]

    def execute(self):
        left_side, right_side = None, None
        comparator = None
        for operator in self.allowed_comparators:
            if operator in self.assertion:
                left_side, right_side = (item.strip() for item in self.assertion.split(operator))
                comparator = operator
                break
        if comparator is None:
            raise NotAllowedComparison(f"Found invalid comparator! Valid comparators are f{self.allowed_comparators}")
        if left_side.startswith("$."):
            left_side_interpolated = interpolate(left_side[2:], self.run_config)
        else:
            left_side_interpolated = left_side
        right_side_interpolated = interpolate(right_side, self.run_config)
        if comparator == "==":
            is_pass = get_dict_value_from_json_path(self.response, left_side_interpolated) == right_side_interpolated
        elif comparator == "<=":
            is_pass = get_dict_value_from_json_path(self.response, left_side_interpolated) <= right_side_interpolated
        elif comparator == ">=":
            is_pass = get_dict_value_from_json_path(self.response, left_side_interpolated) >= right_side_interpolated
        elif comparator == "!=":
            is_pass = get_dict_value_from_json_path(self.response, left_side_interpolated) != right_side_interpolated
        elif comparator == "<":
            is_pass = get_dict_value_from_json_path(self.response, left_side_interpolated) < right_side_interpolated
        else:
            is_pass = get_dict_value_from_json_path(self.response, left_side_interpolated) > right_side_interpolated
        if is_pass:
            LOGGER.info(f"{self.assertion_name} which asserts {self.assertion} passed")
        else:
            raise FailedAssertion(f"{self.assertion_name} which asserts {self.assertion} failed")


