import os
import sys
from DRY import ConfigMerger
import logging
logger = logging.getLogger("DRY")  # DRY: Dont Repeat Yourself (Merge, Extend and Override your config file)

from utils.box import load_from_yaml, load_from_json, to_json, to_yaml
from utils.util import get_recursively
from pprint import pprint

from ruamel.yaml import YAML


def convert_to_normal_dicts(_dict):
    deserialised = dict()

    for key, value in _dict.items():
        deserialised[key] = convert_to_normal_dicts(value) if isinstance(value, dict) else value

    return deserialised

def main():
    # For usage of DRY go to config.yaml.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Loading config in YAML format
    # config_dict = load_from_yaml(filename=os.path.join(BASE_DIR, 'config/config.yaml'))
    config_dict = load_from_yaml(filename='vendor_products.yaml')

    # YAML to JSON
    # to_json(config_dict, filename=os.path.join(BASE_DIR, 'config/config.json'))

    key_counter = 0
    for key, value in get_recursively(config_dict):
        # pprint([key, value])
        key_counter += 1

    print("\nNumber of Keys 'config_dict' is: {0}\n {1}".format(key_counter, '-'*100))

    # .............................................................................
    # Usage of DRY
    merger_obj = ConfigMerger(config_dict, merge_at_init=True)
    if merger_obj.return_value == -1:
        logger.error('Error in Config Merger')
        return -1

    # Get merged dict as result
    merged_config_dict = merger_obj.config_dict  # Merged object have MeldDict type
    # Convert MeldDict objects to dict()
    normal_merged_config_dict = convert_to_normal_dicts(merged_config_dict)

    PY3 = sys.version_info[0] == 3
    if PY3:
        to_yaml(normal_merged_config_dict, filename='normal_py3.x.x.yaml')  # Without YAML tags
        to_yaml(merged_config_dict, filename='py3.x.x.yaml')  # With YAML tags
        to_json(merged_config_dict, filename='py3.x.x.json')
    else:
        to_yaml(normal_merged_config_dict, filename='normal_py2.7.x.yaml')  # Without YAML tags
        to_yaml(merged_config_dict, filename='py2.7.x.yaml')  # With YAML tags
        to_json(merged_config_dict, filename='py2.7.x.json')


    key_counter = 0
    for key, value in get_recursively(merged_config_dict):
        # pprint([key, value])
        key_counter += 1

    print("\nNumber of Keys 'merged_config_dict' in YAML format is: {0}\n {1}".format(key_counter, '-'*100))

    # ----------------------------------------------------------------------------------

    # Loading config in JSON format
    config_dict = load_from_json(filename=os.path.join(BASE_DIR, 'config/config.json'))

    # .............................................................................
    # Usage of DRY
    merger_obj = ConfigMerger(config_dict, merge_at_init=True)
    if merger_obj.return_value == -1:
        logger.error('Error in Config Merger')
        return -1

    # Get merged dict as result
    merged_config_dict = merger_obj.config_dict

    key_counter = 0
    for key, value in get_recursively(merged_config_dict):
        # pprint([key, value])
        key_counter += 1

    print("\nNumber of Keys 'merged_config_dict' in JSON format is: {0}\n {1}".format(key_counter, '-'*100))


if __name__ == "__main__":
    main()
